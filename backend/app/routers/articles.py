import math
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.schemas.article import (
    ApproveContentRequest,
    ApproveFinalRequest,
    ApproveImageKeywordsRequest,
    ApproveOutlineRequest,
    BatchActionRequest,
    CreateArticleRequest,
    PublishRequest,
    RegenerateRequest,
)
from app.models.article import Article
from app.services import article_service as svc
from app.services.content_service import generate_content, regenerate_sections, revise_sections
from app.services.image_service import generate_image_plan, search_and_insert_images, insert_images_into_content
from app.services.outline_service import generate_outline, revise_outline
from app.services.taxonomy_service import match_or_create_taxonomy
from app.services.wordpress_service import wordpress_service
from app.utils.logger import logger
from app.utils.sanitizer import sanitize_html

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
    source: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    articles, total = await svc.list_articles(db, page=page, limit=limit, status=status, source=source)
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


async def _generate_content_bg(article_id: UUID):
    from app.core.database import async_session_factory
    async with async_session_factory() as db:
        article = await svc.get_article(db, article_id)
        if article:
            await generate_content(db, article)
            await db.commit()


async def _generate_images_bg(article_id: UUID):
    from app.core.database import async_session_factory
    async with async_session_factory() as db:
        article = await svc.get_article(db, article_id)
        if article:
            await generate_image_plan(db, article)
            await db.commit()


@router.post("/{article_id}/approve-outline")
async def approve_outline(
    article_id: UUID, body: ApproveOutlineRequest, background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    if article.status != "outline_ready":
        raise HTTPException(409, detail=f"Article is not in outline_ready state (current: {article.status})")

    if body.regenerate:
        article = await generate_outline(db, article)
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    if body.revision_prompt:
        if body.title and article.outline:
            article.outline["title"] = body.title
        if body.sections and article.outline:
            article.outline["sections"] = [s.model_dump() for s in body.sections]
        article = await revise_outline(db, article, body.revision_prompt)
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    if article.content and not svc._outline_changed(article.outline, body.title, body.sections):
        article = await svc.update_status(db, article, "outline_approved")
        article = await svc.update_status(db, article, "content_ready")
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    if body.title and article.outline:
        article.outline["title"] = body.title
    if body.sections and article.outline:
        article.outline["sections"] = [s.model_dump() for s in body.sections]
    article = await svc.update_status(db, article, "outline_approved")
    await db.commit()
    await db.refresh(article)
    background_tasks.add_task(_generate_content_bg, article.id)
    return {"success": True, "data": svc.article_to_detail(article)}


@router.post("/{article_id}/approve-content")
async def approve_content(
    article_id: UUID, body: ApproveContentRequest, background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
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
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    if body.regenerate_sections:
        article = await regenerate_sections(db, article, body.regenerate_sections)
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    article = await svc.update_status(db, article, "content_approved")
    await db.commit()
    await db.refresh(article)
    background_tasks.add_task(_generate_images_bg, article.id)
    return {"success": True, "data": svc.article_to_detail(article)}


async def _search_images_bg(article_id: UUID):
    from app.core.database import async_session_factory
    async with async_session_factory() as db:
        article = await svc.get_article(db, article_id)
        if article:
            await search_and_insert_images(db, article)
            await db.commit()


@router.post("/{article_id}/approve-image-keywords")
async def approve_image_keywords(
    article_id: UUID, body: ApproveImageKeywordsRequest, background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    if article.status != "image_keywords_ready":
        raise HTTPException(409, detail=f"Article is not in image_keywords_ready state (current: {article.status})")

    if body.plan:
        article.image_plan = body.plan.model_dump()

    if body.revision_prompt:
        article = await generate_image_plan(db, article)
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    if not svc._plan_changed(article.image_plan, body.plan.model_dump() if body.plan else None) and article.images:
        article = await svc.update_status(db, article, "image_keywords_ready")
        article = await svc.update_status(db, article, "images_ready")
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    article = await svc.update_status(db, article, "image_keywords_ready")
    await db.commit()
    await db.refresh(article)
    background_tasks.add_task(_search_images_bg, article.id)
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

    if body.selected_images and article.images:
        article.images = [img for img in article.images if img.get("id") in body.selected_images]
    elif body.remove_images and article.images:
        article.images = [img for img in article.images if img.get("id") not in body.remove_images]

    if body.cover_image_id and article.images:
        for img in article.images:
            img["type"] = "cover" if img.get("id") == body.cover_image_id else img.get("type", "inline")

    article = insert_images_into_content(article)
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
        content = article.full_html or (article.content or {}).get("full_html", "")
        slug = body.slug or None
        outline = article.outline or {}

        category_id = body.category_id
        tag_ids = list(body.tag_ids) if body.tag_ids else None

        if category_id is None and body.category_name:
            new_cat = await wordpress_service.create_category(body.category_name)
            category_id = new_cat["id"]
            logger.info("Created custom category: %s -> id=%d", body.category_name, category_id)
        elif category_id is None and outline.get("category"):
            matched_cat, _ = await match_or_create_taxonomy(
                wordpress_service,
                outline["category"],
                None,
                auto_create=body.auto_create_taxonomy,
            )
            if matched_cat is not None:
                category_id = matched_cat

        if tag_ids is None:
            tag_ids = []
        if body.tag_names:
            for tag_name in body.tag_names:
                new_tag = await wordpress_service.create_tag(tag_name)
                tag_ids.append(new_tag["id"])
                logger.info("Created custom tag: %s -> id=%d", tag_name, new_tag["id"])
        elif not tag_ids and outline.get("tags"):
            _, matched_tags = await match_or_create_taxonomy(
                wordpress_service,
                None,
                outline["tags"],
                auto_create=body.auto_create_taxonomy,
            )
            if matched_tags:
                tag_ids = matched_tags

        featured_media_id = None
        cover_image = None
        if article.images:
            cover_image = next((img for img in article.images if img.get("type") == "cover"), None)
        if cover_image:
            try:
                alt = cover_image.get("alt_text", title)
                media = await wordpress_service.upload_media(cover_image.get("full_url") or cover_image["url"], alt)
                featured_media_id = media["id"]
                logger.info("Cover image uploaded: wp_media_id=%d", featured_media_id)
            except Exception as e:
                logger.warning("Failed to upload cover image: %s", e)

        wp_post = await wordpress_service.create_post(
            title=title,
            content=content,
            slug=slug,
            status=body.status,
            category_id=category_id,
            tag_ids=tag_ids if tag_ids else None,
            featured_media_id=featured_media_id,
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



STEP_BACK_MAP = {
    "outline_ready": "draft",
    "content_ready": "outline_ready",
    "image_keywords_generating": "content_ready",
    "image_keywords_ready": "content_ready",
    "images_ready": "image_keywords_ready",
    "final_approved": "images_ready",
}


@router.post("/{article_id}/step-back")
async def step_back(article_id: UUID, db: AsyncSession = Depends(get_session)):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    prev = STEP_BACK_MAP.get(article.status)
    if not prev:
        raise HTTPException(409, detail=f"Cannot step back from {article.status}")
    article = await svc.update_status(db, article, prev)
    await db.commit()
    await db.refresh(article)
    return {"success": True, "data": svc.article_to_detail(article)}


@router.post("/batch")
async def batch_action(body: BatchActionRequest, db: AsyncSession = Depends(get_session)):
    processed = 0
    failed: list[dict] = []
    for article_id in body.ids:
        try:
            article = await svc.get_article(db, article_id)
            if not article:
                failed.append({"id": str(article_id), "reason": "Not found"})
                continue
            if article.status == "publishing":
                failed.append({"id": str(article_id), "reason": "Cannot modify while publishing"})
                continue
            if body.action == "delete":
                await db.delete(article)
                processed += 1
            elif body.action == "cancel":
                try:
                    await svc.update_status(db, article, "cancelled")
                    processed += 1
                except ValueError as e:
                    failed.append({"id": str(article_id), "reason": str(e)})
        except Exception as e:
            failed.append({"id": str(article_id), "reason": str(e)})
    await db.commit()
    return {"success": True, "data": {"processed": processed, "failed": failed}}


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


@router.post("/sync-wp")
async def sync_wp():
    result = await wordpress_service.sync_all_posts()
    return {"success": True, "data": result}
