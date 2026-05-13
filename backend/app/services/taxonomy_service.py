from app.services.wordpress_service import WordPressService
from app.utils.logger import logger


async def match_or_create_taxonomy(
    wp_service: WordPressService,
    outline_category: str | None,
    outline_tags: list[str] | None,
    auto_create: bool = False,
) -> tuple[int | None, list[int]]:
    """Match LLM-generated category/tags to existing WP taxonomy IDs.

    Returns (category_id, [tag_ids]).
    If auto_create is True, creates missing taxonomy items.
    """
    category_id = None
    tag_ids: list[int] = []

    if outline_category:
        try:
            categories = await wp_service.get_categories()
            match = next(
                (c for c in categories if c.get("name", "").lower() == outline_category.lower()),
                None,
            )
            if match:
                category_id = match["id"]
                logger.info("Matched category: %s -> id=%d", outline_category, category_id)
            elif auto_create:
                new_cat = await wp_service.create_category(outline_category)
                category_id = new_cat["id"]
                logger.info("Created category: %s -> id=%d", outline_category, category_id)
        except Exception as e:
            logger.warning("Failed to match/create category '%s': %s", outline_category, e)

    if outline_tags:
        try:
            existing_tags = await wp_service.get_tags()
            tag_name_map: dict[str, int] = {
                t.get("name", "").lower(): t["id"] for t in existing_tags
            }
            for tag_name in outline_tags:
                match_id = tag_name_map.get(tag_name.lower())
                if match_id:
                    tag_ids.append(match_id)
                    logger.info("Matched tag: %s -> id=%d", tag_name, match_id)
                elif auto_create:
                    try:
                        new_tag = await wp_service.create_tag(tag_name)
                        tag_ids.append(new_tag["id"])
                        logger.info("Created tag: %s -> id=%d", tag_name, new_tag["id"])
                    except Exception as e:
                        logger.warning("Failed to create tag '%s': %s", tag_name, e)
        except Exception as e:
            logger.warning("Failed to match/create tags: %s", e)

    return category_id, tag_ids
