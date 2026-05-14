import uuid

import bleach
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.prompts.images import IMAGE_KEYWORD_PROMPT_TEMPLATE, IMAGE_PLAN_PROMPT
from app.services.article_service import is_auto_mode, mark_failed, update_status
from app.services.llm_service import llm_service
from app.services.stream_service import stream_manager
from app.core.config import settings
from app.utils.logger import logger

_unsplash_remaining: int | None = None
_unsplash_limit: int = 50


def get_unsplash_remaining() -> int | None:
    return _unsplash_remaining


def get_unsplash_limit() -> int:
    return _unsplash_limit


def _update_rate_limit(headers: dict) -> None:
    global _unsplash_remaining
    remaining = headers.get("X-Ratelimit-Remaining")
    if remaining is not None:
        _unsplash_remaining = int(remaining)


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
                    _update_rate_limit(resp.headers)
                    data = resp.json()
                    for photo in data.get("results", []):
                        images.append({
                            "id": photo["id"],
                            "url": photo["urls"]["small"],
                            "full_url": photo["urls"]["regular"],
                            "thumb_url": photo["urls"]["thumb"],
                            "alt_text": keyword,
                            "source": "unsplash",
                            "source_url": photo["links"]["html"],
                            "photographer": photo["user"]["name"],
                        })
        except Exception as e:
            logger.warning("Image search failed for '%s': %s", keyword, e)
    return images


async def _search_images_by_keywords(keywords: list[str], count: int) -> list[dict]:
    if not settings.unsplash_access_key:
        logger.warning("Unsplash access key not configured, skipping image search")
        return []

    images = []
    per_keyword = max(1, (count + len(keywords) - 1) // len(keywords)) if keywords else 1
    for keyword in keywords[:3]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.unsplash.com/search/photos",
                    params={"query": keyword, "per_page": per_keyword + 1},
                    headers={"Accept-Version": "v1", "Authorization": f"Client-ID {settings.unsplash_access_key.get_secret_value()}"},
                )
                if resp.status_code == 200:
                    _update_rate_limit(resp.headers)
                    data = resp.json()
                    for photo in data.get("results", [])[:per_keyword]:
                        images.append({
                            "id": photo["id"],
                            "url": photo["urls"]["small"],
                            "full_url": photo["urls"]["regular"],
                            "thumb_url": photo["urls"]["thumb"],
                            "alt_text": keyword,
                            "source": "unsplash",
                            "source_url": photo["links"]["html"],
                            "photographer": photo["user"]["name"],
                        })
        except Exception as e:
            logger.warning("Image search failed for '%s': %s", keyword, e)
    return images


async def generate_image_plan(db: AsyncSession, article: Article) -> Article:
    article = await update_status(db, article, "image_keywords_generating")
    await stream_manager.send_status(article.id, "image_keywords_generating")

    outline = article.outline or {}
    content = article.content or {}
    sections = content.get("sections", [])
    title = outline.get("title", article.topic)

    sections_summary_parts = []
    for s in sections:
        heading = s.get("heading", "")
        slug = s.get("slug", "")
        html = s.get("html", "")
        text_preview = html[:300].replace("\n", " ")
        sections_summary_parts.append(f"- slug={slug} heading=\"{heading}\" preview=\"{text_preview}\"")

    prompt = IMAGE_PLAN_PROMPT.format(
        title=title,
        topic=article.topic,
        sections_summary="\n".join(sections_summary_parts),
    )

    try:
        result = await llm_service.generate_json(prompt)
        plan = result["parsed"]

        t_in = result.get("tokens_input", 0)
        t_out = result.get("tokens_output", 0)
        article.token_usage = {
            **(article.token_usage or {}),
            "images": {"input": t_in, "output": t_out},
        }
        token_usage = article.token_usage

        cumulative = sum(
            stage.get("input", 0) + stage.get("output", 0)
            for stage in token_usage.values()
        )

        await stream_manager.send(article.id, "token_update", {
            "stage": "images",
            "section_tokens": {"input": t_in, "output": t_out},
            "cumulative_total": cumulative,
            "per_stage": token_usage,
        })

        article.image_plan = plan
        article = await update_status(db, article, "image_keywords_ready")
        await stream_manager.send_status(article.id, "image_keywords_ready")
        logger.info("Image plan generated: id=%s inline=%d cover=%s",
                     article.id,
                     len(plan.get("inline_images", [])),
                     "yes" if plan.get("cover_image") else "no")

        if await is_auto_mode(article):
            article = await search_and_insert_images(db, article)

        return article

    except Exception as e:
        logger.error("Image plan generation failed: %s", str(e))
        await stream_manager.send_error(article.id, str(e))
        return await mark_failed(db, article, "images", str(e))


async def search_and_insert_images(db: AsyncSession, article: Article) -> Article:
    article = await update_status(db, article, "image_searching")
    await stream_manager.send_status(article.id, "image_searching")

    image_plan = article.image_plan or {}
    content = article.content or {}
    sections = content.get("sections", [])
    section_map = {s.get("slug", ""): s for s in sections}

    all_images = []
    seen_ids: set[str] = set()
    inline_placements = image_plan.get("inline_images", [])

    try:
        total = len(inline_placements)
        for i, placement in enumerate(inline_placements):
            slug = placement.get("section_slug", "")
            keywords = placement.get("keywords", [])
            count = placement.get("suggested_count", 1)
            position = placement.get("position", "before")

            section = section_map.get(slug, {})
            heading = section.get("heading", slug)

            await stream_manager.send_progress(article.id, {
                "stage": "images",
                "current_section": i + 1,
                "total_sections": max(total, 1),
                "heading": heading,
            })

            found = await _search_images_by_keywords(keywords, count)
            for img in found:
                if img["id"] in seen_ids:
                    continue
                seen_ids.add(img["id"])
                img["section_slug"] = slug
                img["position"] = position
                img["type"] = "inline"
                all_images.append(img)

        cover_plan = image_plan.get("cover_image")
        if cover_plan:
            cover_keywords = cover_plan.get("keywords", [])
            cover_count = cover_plan.get("suggested_count", 1)
            found = await _search_images_by_keywords(cover_keywords, cover_count)
            for img in found:
                if img["id"] in seen_ids:
                    continue
                seen_ids.add(img["id"])
                img["section_slug"] = ""
                img["position"] = "cover"
                img["type"] = "cover"
                all_images.append(img)

        article.images = all_images
        article = await update_status(db, article, "images_ready")
        await stream_manager.send_status(article.id, "images_ready")

    except Exception as e:
        logger.error("Image search failed: %s", str(e))
        await stream_manager.send_error(article.id, str(e))
        return await mark_failed(db, article, "images", str(e))

    if await is_auto_mode(article):
        try:
            article = insert_images_into_content(article)
        except Exception as e:
            logger.error("Image insertion failed: %s", str(e))
            return await mark_failed(db, article, "images", str(e))
        article = await update_status(db, article, "final_approved")
        await stream_manager.send_status(article.id, "final_approved")

    return article


def insert_images_into_content(article: Article) -> Article:
    content = article.content or {}
    sections = content.get("sections", [])
    images = article.images or []

    inline_images = [img for img in images if img.get("type") == "inline"]
    images_by_section: dict[str, list[dict]] = {}
    for img in inline_images:
        slug = img.get("section_slug", "")
        if slug not in images_by_section:
            images_by_section[slug] = []
        images_by_section[slug].append(img)

    if not images_by_section:
        return article

    for section in sections:
        slug = section.get("slug", "")
        section_images = images_by_section.get(slug, [])
        if not section_images:
            continue

        before_images = [img for img in section_images if img.get("position") == "before"]
        after_images = [img for img in section_images if img.get("position") != "before"]

        figures = []
        for img in before_images:
            figures.append(_build_figure(img))
        figures.append(section.get("html", ""))
        for img in after_images:
            figures.append(_build_figure(img))

        section["html"] = "".join(figures)

    full_html = "".join(s.get("html", "") for s in sections)
    total_words = sum(s.get("word_count", 0) for s in sections)
    article.content = {
        "sections": sections,
        "full_html": full_html,
        "total_word_count": total_words,
    }
    article.full_html = full_html
    return article


def _build_figure(img: dict) -> str:
    url = img.get("full_url") or img.get("url", "")
    alt = img.get("alt_text", "")
    photographer = img.get("photographer", "")
    source_url = img.get("source_url", "")
    caption = f"Photo by {photographer}" if photographer else ""
    if source_url:
        caption = f'<a href="{source_url}" target="_blank" rel="noopener">{caption}</a>' if caption else ""
    figcaption = f"<figcaption>{caption}</figcaption>" if caption else ""
    html = f'<figure><img src="{url}" alt="{alt}" loading="lazy"/>{figcaption}</figure>'
    return bleach.clean(html, tags=["figure", "img", "figcaption", "a"], attributes={
        "img": ["src", "alt", "loading"],
        "a": ["href", "target", "rel"],
    })
