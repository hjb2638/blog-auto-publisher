"""Publish orchestration: taxonomy matching, cover upload, WP post creation."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.services import article_service as svc
from app.services.wordpress_service import WordPressService
from app.services.taxonomy_service import match_or_create_taxonomy
from app.utils.logger import logger


class PublishError(Exception):
    """Raised when publish fails for a known reason."""

    def __init__(self, message: str, stage: str = "publishing"):
        super().__init__(message)
        self.stage = stage


async def publish_article(
    db: AsyncSession,
    article: Article,
    wordpress_service: WordPressService,
    *,
    title: str | None = None,
    content: str | None = None,
    slug: str | None = None,
    status: str = "publish",
    category_id: int | None = None,
    category_name: str | None = None,
    tag_ids: list[int] | None = None,
    tag_names: list[str] | None = None,
    auto_create_taxonomy: bool = True,
) -> Article:
    """Orchestrate the full publish flow: taxonomy, cover upload, WP post creation."""
    outline = article.outline or {}

    resolved_title = title or outline.get("title", article.topic)

    article = await svc.update_status(db, article, "publishing")

    try:
        resolved_category_id = category_id
        resolved_tag_ids = list(tag_ids) if tag_ids else []

        if resolved_category_id is None and category_name:
            new_cat = await wordpress_service.create_category(category_name)
            resolved_category_id = new_cat["id"]
            logger.info("Created custom category: %s -> id=%d", category_name, resolved_category_id)
        elif resolved_category_id is None and outline.get("category"):
            matched_cat, _ = await match_or_create_taxonomy(
                wordpress_service, outline["category"], None,
                auto_create=auto_create_taxonomy,
            )
            if matched_cat is not None:
                resolved_category_id = matched_cat

        if tag_names:
            for tag_name in tag_names:
                new_tag = await wordpress_service.create_tag(tag_name)
                resolved_tag_ids.append(new_tag["id"])
                logger.info("Created custom tag: %s -> id=%d", tag_name, new_tag["id"])
        elif not resolved_tag_ids and outline.get("tags"):
            _, matched_tags = await match_or_create_taxonomy(
                wordpress_service, None, outline["tags"],
                auto_create=auto_create_taxonomy,
            )
            if matched_tags:
                resolved_tag_ids = matched_tags

        featured_media_id = None
        cover_image = None
        if article.images:
            cover_image = next((img for img in article.images if img.get("type") == "cover"), None)
        if cover_image:
            try:
                alt = cover_image.get("alt_text", resolved_title)
                media = await wordpress_service.upload_media(
                    cover_image.get("full_url") or cover_image["url"], alt
                )
                featured_media_id = media["id"]
                logger.info("Cover image uploaded: wp_media_id=%d", featured_media_id)
            except Exception as e:
                logger.warning("Failed to upload cover image: %s", e)
                article.error_message = f"Cover image upload failed: {str(e)}"

        wp_post = await wordpress_service.create_post(
            title=resolved_title,
            content=content or article.full_html or (article.content or {}).get("full_html", ""),
            slug=slug,
            status=status,
            category_id=resolved_category_id,
            tag_ids=resolved_tag_ids if resolved_tag_ids else None,
            featured_media_id=featured_media_id,
        )

        article.wp_post_id = wp_post["id"]
        article.wp_post_url = wp_post["link"]
        article.wp_slug = wp_post["slug"]
        article = await svc.update_status(db, article, "published")

        logger.info("Article published: id=%s wp_post_id=%s url=%s",
                     article.id, wp_post["id"], wp_post["link"])
        return article

    except Exception as e:
        await svc.mark_failed(db, article, "publishing", str(e))
        raise PublishError(str(e)) from e
