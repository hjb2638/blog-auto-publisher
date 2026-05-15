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
    UpdateWpRequest,
)
from app.models.article import Article
from app.services import article_service as svc
from app.services import publish_service
from app.services.content_service import generate_content, regenerate_sections, revise_sections
from app.services.image_service import generate_image_plan, search_and_insert_images, insert_images_into_content
from app.services.outline_service import generate_outline, revise_outline
from app.services.wordpress_service import wordpress_service

router = APIRouter(prefix="/articles", tags=["articles"])


def _outline_changed(outline: dict | None, title: str | None, sections: list | None) -> bool:
    """Check if user-approved outline differs from the stored outline."""
    if not outline:
        return True
    if title and outline.get("title") != title:
        return True
    if sections is not None:
        existing = outline.get("sections", [])
        if len(sections) != len(existing):
            return True
        for i, s in enumerate(sections):
            if isinstance(s, dict):
                if s.get("heading") != existing[i].get("heading"):
                    return True
                if s.get("key_points") != existing[i].get("key_points"):
                    return True
    return False


def _plan_changed(image_plan: dict | None, plan: dict | None) -> bool:
    """Check if the image plan changed from what was stored."""
    if plan is None:
        return False
    if not image_plan:
        return True
    return image_plan.get("inline_images") != plan.get("inline_images") or \
        image_plan.get("cover_image") != plan.get("cover_image")


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
    sort_by: str = "created_at",
    sort_order: str = "desc",
    search: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    articles, total = await svc.list_articles(
        db, page=page, limit=limit, status=status, source=source,
        sort_by=sort_by, sort_order=sort_order, search=search,
    )
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


async def _run_service_bg(article_id: UUID, fn):
    """Generic background task runner: creates session, fetches article, calls fn."""
    from app.core.database import async_session_factory
    async with async_session_factory() as db:
        article = await svc.get_article(db, article_id)
        if article:
            await fn(db, article)
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
        if (body.title or body.sections) and article.outline:
            sections = [s.model_dump() for s in body.sections] if body.sections else None
            article = await svc.update_outline(db, article, title=body.title, sections=sections)
        article = await revise_outline(db, article, body.revision_prompt)
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    if article.content and not _outline_changed(article.outline, body.title, body.sections):
        article = await svc.update_status(db, article, "outline_approved")
        article = await svc.update_status(db, article, "content_ready")
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    if (body.title or body.sections) and article.outline:
        sections = [s.model_dump() for s in body.sections] if body.sections else None
        article = await svc.update_outline(db, article, title=body.title, sections=sections)
    article = await svc.update_status(db, article, "outline_approved")
    await db.commit()
    await db.refresh(article)
    background_tasks.add_task(_run_service_bg, article.id, generate_content)
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

    if body.section_edits:
        article = await svc.update_content_sections(db, article, body.section_edits)

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
    background_tasks.add_task(_run_service_bg, article.id, generate_image_plan)
    return {"success": True, "data": svc.article_to_detail(article)}


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

    if not _plan_changed(article.image_plan, body.plan.model_dump() if body.plan else None) and article.images:
        article = await svc.update_status(db, article, "images_ready")
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}

    await db.commit()
    await db.refresh(article)
    background_tasks.add_task(_run_service_bg, article.id, search_and_insert_images)
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

    article = await svc.apply_final_images(
        db, article,
        selected=body.selected_images,
        removed=body.remove_images,
        cover_id=body.cover_image_id,
    )

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

    try:
        article = await publish_service.publish_article(
            db, article, wordpress_service,
            title=body.title,
            slug=body.slug,
            status=body.status,
            category_id=body.category_id,
            category_name=body.category_name,
            tag_ids=list(body.tag_ids) if body.tag_ids else None,
            tag_names=body.tag_names,
            auto_create_taxonomy=body.auto_create_taxonomy,
        )
        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}
    except publish_service.PublishError as e:
        raise HTTPException(502, detail=f"WordPress publish failed: {e}")


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



@router.post("/{article_id}/step-back")
async def step_back(article_id: UUID, db: AsyncSession = Depends(get_session)):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    prev = svc.STEP_BACK_MAP.get(article.status)
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
                try:
                    await svc.delete_article(
                        db, article,
                        wordpress_service=wordpress_service if body.delete_wp else None,
                        delete_wp=body.delete_wp,
                    )
                    processed += 1
                except ValueError as e:
                    failed.append({"id": str(article_id), "reason": str(e)})
            elif body.action == "unpublish":
                try:
                    await svc.unpublish_article(
                        db, article,
                        wordpress_service=wordpress_service,
                    )
                    processed += 1
                except ValueError as e:
                    failed.append({"id": str(article_id), "reason": str(e)})
            elif body.action == "cancel":
                try:
                    await svc.cancel_article(db, article)
                    processed += 1
                except ValueError as e:
                    failed.append({"id": str(article_id), "reason": str(e)})
        except Exception as e:
            failed.append({"id": str(article_id), "reason": str(e)})
    await db.commit()
    return {"success": True, "data": {"processed": processed, "failed": failed}}


@router.delete("/{article_id}")
async def delete_article(
    article_id: UUID,
    delete_wp: bool = False,
    db: AsyncSession = Depends(get_session),
):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")

    try:
        result = await svc.delete_article(
            db, article,
            wordpress_service=wordpress_service if delete_wp else None,
            delete_wp=delete_wp,
        )
        await db.commit()
        return {"success": True, "data": {"deleted": result["deleted"], "wpDeleted": result["wp_deleted"], "id": str(article_id)}}
    except ValueError as e:
        msg = str(e)
        if "auth" in msg.lower():
            raise HTTPException(502, detail="WordPress auth failed. Check application password permissions.")
        if "publishing" in msg.lower():
            raise HTTPException(409, detail=msg)
        raise HTTPException(502, detail=f"WordPress delete failed: {e}")


@router.post("/{article_id}/update-wp")
async def update_wp_article(
    article_id: UUID,
    body: UpdateWpRequest,
    db: AsyncSession = Depends(get_session),
):
    article = await svc.get_article(db, article_id)
    if not article:
        raise HTTPException(404, detail="Article not found")
    if article.status != "published" or not article.wp_post_id:
        raise HTTPException(409, detail="Article is not published to WordPress")

    try:
        await wordpress_service.update_post(
            article.wp_post_id,
            title=body.title,
            content=body.content,
            status=body.status,
            slug=body.slug,
        )

        if body.title is not None and article.outline:
            article.outline["title"] = body.title
        if body.content is not None:
            article.full_html = body.content
        if body.slug is not None:
            article.wp_slug = body.slug

        await db.commit()
        await db.refresh(article)
        return {"success": True, "data": svc.article_to_detail(article)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(502, detail=f"WordPress update failed: {e}")


@router.post("/sync-wp")
async def sync_wp():
    from app.core.database import async_session_factory

    async def _importer(post: dict) -> str:
        async with async_session_factory() as db:
            try:
                result = await svc.import_from_wordpress(db, post)
                await db.commit()
                return result
            except Exception:
                await db.rollback()
                raise

    result = await wordpress_service.sync_all_posts(importer=_importer)
    return {"success": True, "data": result}
