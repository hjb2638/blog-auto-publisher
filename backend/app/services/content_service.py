import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.prompts.content import CONTENT_PROMPT_TEMPLATE
from app.services.article_service import is_auto_mode, mark_failed, update_status
from app.services.llm_service import llm_service
from app.services.stream_service import stream_manager
from app.utils.logger import logger
from app.utils.sanitizer import sanitize_html


def _count_words(html: str) -> int:
    text = re.sub(r'<[^>]+>', ' ', html)
    return len(text.split())


async def generate_content(db: AsyncSession, article: Article, sections_to_generate: list[str] | None = None) -> Article:
    article = await update_status(db, article, "content_generating")
    await stream_manager.send_status(article.id, "content_generating")

    outline = article.outline or {}
    sections = outline.get("sections", [])
    existing_content = (article.content or {}).get("sections", [])

    if sections_to_generate:
        sections = [s for s in sections if s.get("slug") in sections_to_generate]
        existing_content = [c for c in existing_content if c.get("slug") not in sections_to_generate]
    else:
        existing_content = []

    total = len(sections)
    language = "Chinese" if any('一' <= c <= '鿿' for c in article.topic) else "English"

    try:
        for i, section in enumerate(sections):
            heading = section.get("heading", "")
            key_points = section.get("key_points", [])
            estimated_words = section.get("estimated_words", 300)
            include_code = section.get("include_code_example", False)
            slug = section.get("slug", f"section-{i}")

            prev_summary = ""
            if existing_content:
                prev = existing_content[-1]
                prev_summary = prev.get("heading", "") + ": " + prev.get("html", "")[:200]
            next_heading = sections[i + 1].get("heading", "Conclusion") if i + 1 < total else "Conclusion"

            await stream_manager.send_progress(article.id, {
                "stage": "content",
                "current_section": i + 1,
                "total_sections": total,
                "heading": heading,
            })

            prompt = CONTENT_PROMPT_TEMPLATE.format(
                title=outline.get("title", article.topic),
                topic=article.topic,
                previous_section_summary=prev_summary,
                next_section_heading=next_heading,
                heading=heading,
                key_points="\n".join(f"- {p}" for p in key_points) if key_points else "No specific key points",
                estimated_words=estimated_words,
                include_code_example="Yes" if include_code else "No",
                section_number=i + 1,
                total_sections=total,
                language=language,
            )

            result = await llm_service.generate_response(prompt)
            html = sanitize_html(result["content"])
            word_count = _count_words(html)

            existing_content.append({
                "heading": heading,
                "slug": slug,
                "html": html,
                "word_count": word_count,
            })

            await stream_manager.send(article.id, "section_complete", {
                "section_index": i + 1,
                "heading": heading,
                "word_count": word_count,
            })

        full_html = "\n".join(s.get("html", "") for s in existing_content)
        total_words = sum(s.get("word_count", 0) for s in existing_content)

        article.content = {
            "sections": existing_content,
            "full_html": full_html,
            "total_word_count": total_words,
        }
        article = await update_status(db, article, "content_ready")
        await stream_manager.send_status(article.id, "content_ready")

        if await is_auto_mode(article):
            article = await update_status(db, article, "content_approved")
            await stream_manager.send_status(article.id, "content_approved")

        return article

    except Exception as e:
        logger.error("Content generation failed: %s", str(e))
        await stream_manager.send_error(article.id, str(e))
        return await mark_failed(db, article, "content", str(e))


async def regenerate_sections(db: AsyncSession, article: Article, slugs: list[str]) -> Article:
    return await generate_content(db, article, sections_to_generate=slugs)
