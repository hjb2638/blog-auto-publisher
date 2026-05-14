from uuid import UUID

from sqlalchemy import desc, func, select
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
    "failed": {"outline_generating", "content_generating", "image_searching", "publishing"},
}

GENERATING_STATES = {"outline_generating", "content_generating", "image_keywords_generating", "image_searching", "publishing"}


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
) -> tuple[list[Article], int]:
    query = select(Article)
    count_query = select(func.count(Article.id))

    if status:
        query = query.where(Article.status == status)
        count_query = count_query.where(Article.status == status)
    if source:
        query = query.where(Article.source == source)
        count_query = count_query.where(Article.source == source)

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(desc(Article.created_at)).offset(offset).limit(limit)
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


async def is_auto_mode(article: Article) -> bool:
    return article.mode == "auto"


def _outline_changed(outline: dict | None, title: str | None, sections: list | None) -> bool:
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
    if plan is None:
        return False
    if not image_plan:
        return True
    return image_plan.get("inline_images") != plan.get("inline_images") or \
        image_plan.get("cover_image") != plan.get("cover_image")


def article_to_list_item(a: Article) -> ArticleListItem:
    total = None
    if a.token_usage:
        total = sum(
            stage.get("input", 0) + stage.get("output", 0)
            for stage in a.token_usage.values()
        )
    return ArticleListItem(
        id=a.id,
        topic=a.topic[:80] if len(a.topic) > 80 else a.topic,
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
