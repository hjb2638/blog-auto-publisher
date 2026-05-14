import json
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import json

from app.models.article import Article
from app.prompts.outline import OUTLINE_PROMPT_TEMPLATE
from app.prompts.revision import OUTLINE_REVISION_PROMPT
from app.services.article_service import is_auto_mode, mark_failed, update_status
from app.services.llm_service import llm_service
from app.services.stream_service import stream_manager
from app.utils.logger import logger


def _slugify(heading: str) -> str:
    slug = re.sub(r'[^\w\s-]', '', heading.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug or "section"


async def generate_outline(db: AsyncSession, article: Article) -> Article:
    article = await update_status(db, article, "outline_generating")
    await stream_manager.send_status(article.id, "outline_generating")

    prompt = OUTLINE_PROMPT_TEMPLATE.format(
        topic=article.topic,
        requirements=article.requirements or "No specific requirements.",
        language="Chinese" if any('一' <= c <= '鿿' for c in article.topic) else "English",
    )

    try:
        result = await llm_service.generate_json(prompt)
        outline = result["parsed"]

        t_in = result.get("tokens_input", 0)
        t_out = result.get("tokens_output", 0)
        article.token_usage = {
            **(article.token_usage or {}),
            "outline": {"input": t_in, "output": t_out},
        }

        await stream_manager.send(article.id, "token_update", {
            "stage": "outline",
            "section_tokens": {"input": t_in, "output": t_out},
            "cumulative_total": t_in + t_out,
            "per_stage": article.token_usage,
        })

        for section in outline.get("sections", []):
            if "slug" not in section or not section["slug"]:
                section["slug"] = _slugify(section.get("heading", f"section-{uuid.uuid4().hex[:8]}"))

        article.outline = outline
        article = await update_status(db, article, "outline_ready")
        await stream_manager.send_status(article.id, "outline_ready")

        if await is_auto_mode(article):
            article = await update_status(db, article, "outline_approved")
            await stream_manager.send_status(article.id, "outline_approved")
            from app.services.content_service import generate_content
            article = await generate_content(db, article)

        return article

    except Exception as e:
        logger.error("Outline generation failed: %s", str(e))
        await stream_manager.send_error(article.id, str(e))
        return await mark_failed(db, article, "outline", str(e))


async def revise_outline(db: AsyncSession, article: Article, revision_prompt: str) -> Article:
    current_json = json.dumps(article.outline, ensure_ascii=False, indent=2)
    prompt = OUTLINE_REVISION_PROMPT.format(
        current_outline_json=current_json,
        revision_prompt=revision_prompt,
    )

    try:
        result = await llm_service.generate_json(prompt)
        t_in = result.get("tokens_input", 0)
        t_out = result.get("tokens_output", 0)
        article.token_usage = {
            **(article.token_usage or {}),
            "outline_revision": {"input": t_in, "output": t_out},
        }
        outline = result["parsed"]
        for section in outline.get("sections", []):
            if "slug" not in section or not section["slug"]:
                section["slug"] = _slugify(section.get("heading", f"section-{uuid.uuid4().hex[:8]}"))
        article.outline = outline
        logger.info("Outline revised: id=%s", article.id)
        return article
    except Exception as e:
        logger.error("Outline revision failed: %s", str(e))
        raise
