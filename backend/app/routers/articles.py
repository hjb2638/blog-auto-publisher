import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.schemas.article import (
    ApproveContentRequest,
    ApproveFinalRequest,
    ApproveOutlineRequest,
    CreateArticleRequest,
    PublishRequest,
    RegenerateRequest,
    WPCategory,
    WPTag,
)
from app.services import article_service as svc
from app.services.content_service import generate_content, regenerate_sections, revise_sections
from app.services.image_service import search_and_insert_images
from app.services.outline_service import generate_outline, revise_outline
from app.services.taxonomy_service import match_or_create_taxonomy
from app.services.wordpress_service import wordpress_service
from app.utils.logger import logger

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("", status_code=201)
async def create_article(body: CreateArticleRequest, db: AsyncSession = Depends(get_session)):
    article = await svc.create_article(db, body.topic, body.requirements, body.mode.value)
    article = await generate_outline(db, article)
    await db.commit()
    await db.refresh(article)
    return {"success": True, "data": svc.article_to_detail(article)}


@router.get("")
async def list_articles(
    page: int = 1,
    limit: int = 20,
    status: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    articles, total = await svc.list_articles(db, page=page, limit=limit, status=status)
    return {
        "success": True,
        "data": [svc.article_to_list_item(a) for a in articles],
        "meta": {"total": total, "page": page, "limit": limit, "pages": math.ceil(total / limit) if total else 0},
    }


@router.get("/{article_id}")
async def get_article_detail(article_id: UUID, db: AsyncSession = Depends(get_session)):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    return {"success": True, "data": svc.article_to_detail(article)}


@router.get("/{article_id}/status")
async def get_article_status(article_id: UUID, db: AsyncSession = Depends(get_session)):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    return {
        "success": True,
        "data": {
            "id": str(article.id),
            "status": article.status,
            "progress": article.progress,
            "error_message": article.error_message,
            "updated_at": article.updated_at.isoformat(),
        },
    }


@router.post("/{article_id}/approve-outline")
async def approve_outline(
    article_id: UUID, body: ApproveOutlineRequest, db: AsyncSession = Depends(get_session)
):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    if article.status != "outline_ready":
        raise HTTPException(409, detail=f"Article is not in outline_ready state (current: {article.status})")

    if body.regenerate:
        article = await generate_outline(db, article)
    elif body.revision_prompt:
        if body.title and article.outline:
            article.outline["title"] = body.title
        if body.sections and article.outline:
            article.outline["sections"] = [s.model_dump() for s in body.sections]
        article = await revise_outline(db, article, body.revision_prompt)
    else:
        if body.title and article.outline:
            article.outline["title"] = body.title
        if body.sections and article.outline:
            article.outline["sections"] = [s.model_dump() for s in body.sections]
        article = await svc.update_status(db, article, "outline_approved")
        await generate_content(db, article)

    await db.commit()
    await db.refresh(article)
    return {"success": True, "data": svc.article_to_detail(article)}


@router.post("/{article_id}/approve-content")
async def approve_content(
    article_id: UUID, body: ApproveContentRequest, db: AsyncSession = Depends(get_session)
):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    if article.status != "content_ready":
        raise HTTPException(409, detail=f"Article is not in content_ready state (current: {article.status})")

    if body.section_edits and article.content:
        sections = article.content.get("sections", [])
        for s in sections:
            slug = s.get("slug", "")
            if slug in body.section_edits:
                s["html"] = body.section_edits[slug]
        article.content["sections"] = sections

    if body.revision_prompt:
        slugs = body.regenerate_sections or []
        article = await revise_sections(db, article, slugs, body.revision_prompt)
    elif body.regenerate_sections:
        article = await regenerate_sections(db, article, body.regenerate_sections)
    else:
        article = await svc.update_status(db, article, "content_approved")
        await search_and_insert_images(db, article)

    await db.commit()
    await db.refresh(article)
    return {"success": True, "data": svc.article_to_detail(article)}


@router.post("/{article_id}/approve-final")
async def approve_final(
    article_id: UUID, body: ApproveFinalRequest, db: AsyncSession = Depends(get_session)
):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    if article.status != "images_ready":
        raise HTTPException(409, detail=f"Article is not in images_ready state (current: {article.status})")

    if body.remove_images and article.images:
        article.images = [img for img in article.images if img.get("id") not in body.remove_images]

    article = await svc.update_status(db, article, "final_approved")
    await db.commit()
    await db.refresh(article)
    return {"success": True, "data": svc.article_to_detail(article)}


@router.post("/{article_id}/publish")
async def publish_article(
    article_id: UUID, body: PublishRequest, db: AsyncSession = Depends(get_session)
):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    if article.status not in ("final_approved", "failed"):
        raise HTTPException(409, detail=f"Article cannot be published in {article.status} state")

    article = await svc.update_status(db, article, "publishing")

    try:
        title = body.title or (article.outline or {}).get("title", article.topic)
        content = article.content.get("full_html", "") if article.content else ""
        slug = body.slug or None

        category_id = body.category_id
        tag_ids = body.tag_ids

        outline = article.outline or {}

        if category_id is None and outline.get("category"):
            matched_cat, _ = await match_or_create_taxonomy(
                wordpress_service,
                outline["category"],
                None,
                auto_create=body.auto_create_taxonomy,
            )
            if matched_cat is not None:
                category_id = matched_cat

        if tag_ids is None and outline.get("tags"):
            _, matched_tags = await match_or_create_taxonomy(
                wordpress_service,
                None,
                outline["tags"],
                auto_create=body.auto_create_taxonomy,
            )
            if matched_tags:
                tag_ids = matched_tags

        wp_post = await wordpress_service.create_post(
            title=title,
            content=content,
            slug=slug,
            status=body.status,
            category_id=category_id,
            tag_ids=tag_ids,
        )

        article.wp_post_id = wp_post["id"]
        article.wp_post_url = wp_post["link"]
        article.wp_slug = wp_post["slug"]
        article = await svc.update_status(db, article, "published")
        await db.commit()
        await db.refresh(article)

        logger.info("Article published: id=%s wp_post_id=%s url=%s", article.id, wp_post["id"], wp_post["link"])
        return {"success": True, "data": svc.article_to_detail(article)}

    except Exception as e:
        await db.rollback()
        article = await svc.mark_failed(db, article, "publishing", str(e))
        raise HTTPException(502, detail=f"WordPress publish failed: {str(e)}")


@router.post("/{article_id}/regenerate")
async def regenerate_article(
    article_id: UUID, body: RegenerateRequest, db: AsyncSession = Depends(get_session)
):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    if article.status == "published":
        raise HTTPException(409, detail="Cannot regenerate a published article")

    stage = body.stage
    if stage == "outline":
        if body.updated_requirements:
            article.requirements = body.updated_requirements
        article = await generate_outline(db, article)
    elif stage == "content":
        article = await generate_content(db, article, sections_to_generate=body.section_slugs)
    elif stage == "images":
        article = await search_and_insert_images(db, article)

    await db.commit()
    await db.refresh(article)
    return {"success": True, "data": svc.article_to_detail(article)}


@router.get("/wordpress/categories")
async def get_wp_categories():
    try:
        categories = await wordpress_service.get_categories()
        return {
            "success": True,
            "data": [{"id": c["id"], "name": c["name"], "slug": c["slug"], "count": c.get("count", 0)} for c in categories],
        }
    except Exception as e:
        raise HTTPException(502, detail=f"Failed to fetch WP categories: {str(e)}")


@router.get("/wordpress/tags")
async def get_wp_tags():
    try:
        tags = await wordpress_service.get_tags()
        return {
            "success": True,
            "data": [{"id": t["id"], "name": t["name"], "slug": t["slug"], "count": t.get("count", 0)} for t in tags],
        }
    except Exception as e:
        raise HTTPException(502, detail=f"Failed to fetch WP tags: {str(e)}")


@router.delete("/{article_id}")
async def delete_article(article_id: UUID, db: AsyncSession = Depends(get_session)):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    if article.status == "publishing":
        raise HTTPException(409, detail="Cannot delete article while publishing")

    await db.delete(article)
    await db.commit()
    return {"success": True, "data": {"deleted": True, "id": str(article_id)}}
