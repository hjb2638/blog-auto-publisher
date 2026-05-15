from uuid import UUID

import httpx
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.schemas.article import (
    ArticleDetail,
    ArticleImageSchema,
    ArticleListItem,
    ProgressSchema,
    OutlineSchema,
    ContentSectionSchema,
    ArticleContentSchema,
    ArticleStatus,
)
from app.utils.logger import logger


VALID_TRANSITIONS = {
    "draft": {"outline_generating", "cancelled"},
    "outline_generating": {"outline_ready", "failed"},
    "outline_ready": {"outline_approved", "outline_generating", "cancelled"},
    "outline_approved": {"content_generating", "content_ready", "cancelled"},
    "content_generating": {"content_ready", "failed"},
    "content_ready": {"content_approved", "content_generating", "outline_ready", "cancelled"},
    "content_approved": {"image_keywords_generating", "image_keywords_ready", "cancelled"},
    "image_keywords_generating": {"image_keywords_ready", "failed"},
    "image_keywords_ready": {"image_searching", "images_ready", "image_keywords_generating", "content_ready", "cancelled"},
    "image_searching": {"images_ready", "failed"},
    "images_ready": {"final_approved", "image_searching", "image_keywords_ready", "cancelled"},
    "final_approved": {"publishing", "images_ready", "cancelled"},
    "publishing": {"published", "failed"},
    "published": {"final_approved"},
    "failed": {"outline_generating", "content_generating", "image_searching", "publishing"},
}

GENERATING_STATES = {"outline_generating", "content_generating", "image_keywords_generating", "image_searching", "publishing"}

STEP_BACK_MAP = {
    "outline_ready": "draft",
    "content_ready": "outline_ready",
    "image_keywords_generating": "content_ready",
    "image_keywords_ready": "content_ready",
    "images_ready": "image_keywords_ready",
    "final_approved": "images_ready",
}


def validate_transition(from_status: str, to_status: str) -> bool:
    return to_status in VALID_TRANSITIONS.get(from_status, set())


async def create_article(db: AsyncSession, topic: str, requirements: str | None, mode: str) -> Article:
    article = Article(topic=topic, requirements=requirements, mode=mode, status="draft")
    db.add(article)
    await db.flush()
    await db.refresh(article)
    logger.info("Article created: id=%s topic=%s", article.id, topic)
    return article


async def get_article(db: AsyncSession, article_id: UUID) -> Article | None:
    return await db.get(Article, article_id)


async def list_articles(
    db: AsyncSession, page: int = 1, limit: int = 20, status: str | None = None, source: str | None = None,
    sort_by: str = "created_at", sort_order: str = "desc", search: str | None = None,
) -> tuple[list[Article], int]:
    query = select(Article)
    count_query = select(func.count(Article.id))

    if status:
        query = query.where(Article.status == status)
        count_query = count_query.where(Article.status == status)
    if source:
        query = query.where(Article.source == source)
        count_query = count_query.where(Article.source == source)

    if search:
        pattern = f"%{search}%"
        condition = Article.outline["title"].astext.ilike(pattern) | Article.topic.ilike(pattern)
        query = query.where(condition)
        count_query = count_query.where(condition)

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    order_fn = asc if sort_order == "asc" else desc
    sort_cols = {"created_at": Article.created_at, "updated_at": Article.updated_at}
    order_col = sort_cols.get(sort_by, Article.created_at)

    offset = (page - 1) * limit

    if sort_by == "total_tokens":
        # Fetch all matching rows, sort by tokens in Python, then paginate.
        # This does not scale beyond ~10K rows — consider a dedicated column.
        all_result = await db.execute(query)
        all_articles = list(all_result.scalars().all())

        def _tokens(a: Article) -> int:
            if not a.token_usage:
                return 0
            return sum(stage.get("input", 0) + stage.get("output", 0) for stage in a.token_usage.values())

        all_articles.sort(key=_tokens, reverse=(sort_order == "desc"))
        articles = all_articles[offset:offset + limit]
    else:
        query = query.order_by(order_fn(order_col)).offset(offset).limit(limit)
        result = await db.execute(query)
        articles = list(result.scalars().all())

    return articles, total


async def update_status(db: AsyncSession, article: Article, new_status: str) -> Article:
    allowed = VALID_TRANSITIONS.get(article.status, set())
    if new_status not in allowed:
        raise ValueError(f"Invalid transition: {article.status} -> {new_status}. Allowed: {allowed}")
    article.status = new_status
    article.version += 1
    await db.flush()
    logger.info("Article status: id=%s %s -> %s", article.id, article.status, new_status)
    return article


async def mark_failed(db: AsyncSession, article: Article, stage: str, error: str) -> Article:
    article.error_message = error
    article.error_stage = stage
    return await update_status(db, article, "failed")


async def delete_article(
    db: AsyncSession,
    article: Article,
    wordpress_service=None,
    delete_wp: bool = False,
) -> dict:
    """Delete an article, optionally syncing to WordPress.

    Returns: {"deleted": True, "wp_deleted": bool}
    """
    if article.status == "publishing":
        raise ValueError("Cannot delete article while publishing")

    wp_deleted = False
    if delete_wp and article.wp_post_id and wordpress_service:
        try:
            wp_deleted = await wordpress_service.delete_post(article.wp_post_id)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("WordPress auth failed")
            raise

    await db.delete(article)
    await db.flush()
    logger.info("Article deleted: id=%s wp_deleted=%s", article.id, wp_deleted)
    return {"deleted": True, "wp_deleted": wp_deleted}


async def cancel_article(db: AsyncSession, article: Article) -> Article:
    """Cancel an article, transitioning it to cancelled state."""
    return await update_status(db, article, "cancelled")


async def unpublish_article(
    db: AsyncSession,
    article: Article,
    wordpress_service=None,
) -> Article:
    """Unpublish a published article: set WP post to draft + article to final_approved."""
    if article.status != "published":
        raise ValueError("Can only unpublish published articles")
    if not article.wp_post_id:
        raise ValueError(f"Article {article.id} has no WordPress post ID")

    if wordpress_service:
        try:
            await wordpress_service.update_post(article.wp_post_id, status="draft")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("WordPress auth failed")
            raise

    return await update_status(db, article, "final_approved")


async def update_outline(
    db: AsyncSession, article: Article,
    title: str | None = None, sections: list[dict] | None = None,
) -> Article:
    """Update an article's outline fields."""
    if article.outline is None:
        article.outline = {}
    if title is not None:
        article.outline["title"] = title
    if sections is not None:
        article.outline["sections"] = sections
    await db.flush()
    return article


async def update_content_sections(
    db: AsyncSession, article: Article, section_edits: dict[str, str],
) -> Article:
    """Apply section-level HTML edits to an article's content."""
    if not article.content:
        article.content = {}
    sections = article.content.get("sections", [])
    for s in sections:
        slug = s.get("slug", "")
        if slug in section_edits:
            s["html"] = section_edits[slug]
    article.content["sections"] = sections
    await db.flush()
    return article


async def apply_final_images(
    db: AsyncSession, article: Article,
    selected: list[str] | None = None,
    removed: list[str] | None = None,
    cover_id: str | None = None,
) -> Article:
    """Apply final image selections: filter, remove, and set cover."""
    images = article.images or []
    if selected:
        images = [img for img in images if img.get("id") in selected]
    elif removed:
        images = [img for img in images if img.get("id") not in removed]
    if cover_id:
        for img in images:
            img["type"] = "cover" if img.get("id") == cover_id else "inline"
    article.images = images
    await db.flush()
    return article


async def import_from_wordpress(db: AsyncSession, post: dict) -> str:
    """Import a single WordPress post as an Article. Returns 'imported' or 'skipped'."""
    existing = (await db.execute(
        select(Article).where(Article.wp_post_id == post["id"])
    )).scalar()
    if existing:
        return "skipped"

    topic = post["title"]["rendered"]
    if len(topic) < 10:
        topic = topic + " - Technical Article"
    topic = topic[:500]

    article = Article(
        topic=topic,
        mode="manual",
        status="published",
        source="wordpress",
        wp_post_id=post["id"],
        wp_post_url=post["link"],
        wp_slug=post["slug"],
        full_html=post["content"]["rendered"],
    )
    db.add(article)
    await db.flush()
    return "imported"


async def is_auto_mode(article: Article) -> bool:
    return article.mode == "auto"



def article_to_list_item(a: Article) -> ArticleListItem:
    total = None
    if a.token_usage:
        total = sum(
            stage.get("input", 0) + stage.get("output", 0)
            for stage in a.token_usage.values()
        )
    display_title = a.topic[:80]
    if a.outline and isinstance(a.outline, dict) and a.outline.get("title"):
        display_title = a.outline["title"][:80] if len(a.outline["title"]) > 80 else a.outline["title"]

    return ArticleListItem(
        id=a.id,
        topic=a.topic[:80] if len(a.topic) > 80 else a.topic,
        display_title=display_title,
        status=ArticleStatus(a.status),
        mode=a.mode,
        wp_post_url=a.wp_post_url,
        total_tokens=total,
        source=a.source,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


def article_to_detail(a: Article) -> ArticleDetail:
    return ArticleDetail(
        id=a.id,
        topic=a.topic,
        requirements=a.requirements,
        mode=a.mode,
        status=ArticleStatus(a.status),
        outline=a.outline,
        content=a.content,
        images=a.images,
        image_plan=a.image_plan,
        full_html=a.full_html,
        progress=a.progress,
        wp_post_id=a.wp_post_id,
        wp_post_url=a.wp_post_url,
        wp_slug=a.wp_slug,
        error_message=a.error_message,
        token_usage=a.token_usage,
        source=a.source,
        version=a.version,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )
