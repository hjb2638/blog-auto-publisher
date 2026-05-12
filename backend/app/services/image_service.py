import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.prompts.images import IMAGE_KEYWORD_PROMPT_TEMPLATE
from app.services.article_service import is_auto_mode, mark_failed, update_status
from app.services.llm_service import llm_service
from app.services.stream_service import stream_manager
from app.core.config import settings
from app.utils.logger import logger


async def _search_images(section_heading: str, content_preview: str) -> list[dict]:
    prompt = IMAGE_KEYWORD_PROMPT_TEMPLATE.format(
        heading=section_heading,
        content_preview=content_preview[:500],
    )
    try:
        result = await llm_service.generate_json(prompt)
        keywords = result["parsed"].get("keywords", [])
    except Exception as e:
        logger.warning("Image keyword generation failed: %s", e)
        keywords = [section_heading]

    if not settings.unsplash_access_key:
        logger.warning("Unsplash access key not configured, skipping image search")
        return []

    images = []
    for keyword in keywords[:2]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.unsplash.com/search/photos",
                    params={"query": keyword, "per_page": 3},
                    headers={"Accept-Version": "v1", "Authorization": f"Client-ID {settings.unsplash_access_key.get_secret_value()}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for photo in data.get("results", []):
                        images.append({
                            "id": photo["id"],
                            "url": photo["urls"]["regular"],
                            "alt_text": keyword,
                            "source": "unsplash",
                            "source_url": photo["links"]["html"],
                            "photographer": photo["user"]["name"],
                        })
        except Exception as e:
            logger.warning("Image search failed for '%s': %s", keyword, e)
    return images


async def search_and_insert_images(db: AsyncSession, article: Article) -> Article:
    article = await update_status(db, article, "image_searching")
    await stream_manager.send_status(article.id, "image_searching")

    content = article.content or {}
    sections = content.get("sections", [])
    all_images = []

    try:
        for i, section in enumerate(sections):
            heading = section.get("heading", f"Section {i}")
            html = section.get("html", "")

            await stream_manager.send_progress(article.id, {
                "stage": "images",
                "current_section": i + 1,
                "total_sections": len(sections),
                "heading": heading,
            })

            found = await _search_images(heading, html)
            for img in found:
                img["section_slug"] = section.get("slug", "")
                img["position"] = "before"
            all_images.extend(found)

        article.images = all_images
        article = await update_status(db, article, "images_ready")
        await stream_manager.send_status(article.id, "images_ready")

        if await is_auto_mode(article):
            article = await update_status(db, article, "final_approved")
            await stream_manager.send_status(article.id, "final_approved")

        return article

    except Exception as e:
        logger.error("Image search failed: %s", str(e))
        await stream_manager.send_error(article.id, str(e))
        return await mark_failed(db, article, "images", str(e))
