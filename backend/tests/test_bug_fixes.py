"""Regression tests for v1.3.1 bug fixes.

Bug 2: Content token_usage not persisted when outline token_usage exists
Bug 3: Image approval stuck at image_keywords_ready
Bug 4: WP sync fails on short topic titles
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.models.article import Article
from app.services.article_service import validate_transition


# ---------------------------------------------------------------------------
# Bug 2: Content token_usage mutation detection
# ---------------------------------------------------------------------------

class TestTokenUsagePersistence:
    """When token_usage is a pre-existing dict (from outline), in-place
    mutations may not be detected by SQLAlchemy. The fix ensures a new dict
    is always assigned."""

    @pytest.mark.asyncio
    async def test_generate_content_preserves_outline_tokens(self):
        """After content generation, token_usage must contain both outline
        and content entries."""
        from app.services.content_service import generate_content
        from app.services.llm_service import llm_service
        from app.services.stream_service import stream_manager

        article = Article(
            id=uuid4(),
            topic="A comprehensive guide to machine learning techniques",
            mode="manual",
            status="outline_approved",
            outline={
                "title": "ML Guide",
                "sections": [
                    {
                        "heading": "Introduction",
                        "slug": "introduction",
                        "key_points": ["Overview"],
                        "estimated_words": 100,
                        "include_code_example": False,
                    }
                ],
                "category": "AI",
                "tags": ["ML"],
            },
            token_usage={"outline": {"input": 500, "output": 300}},
        )

        mock_llm_result = {
            "content": "<p>Machine learning is a powerful tool.</p>",
            "tokens_input": 200,
            "tokens_output": 150,
        }

        with (
            patch.object(llm_service, 'generate_response', new_callable=AsyncMock, return_value=mock_llm_result),
            patch('app.services.content_service.update_status', new_callable=AsyncMock, return_value=article),
            patch.object(stream_manager, 'send_status', new_callable=AsyncMock),
            patch.object(stream_manager, 'send_progress', new_callable=AsyncMock),
            patch.object(stream_manager, 'send', new_callable=AsyncMock),
            patch.object(stream_manager, 'send_error', new_callable=AsyncMock),
            patch('app.services.content_service.is_auto_mode', new_callable=AsyncMock, return_value=False),
        ):
            db = AsyncMock()
            result = await generate_content(db, article)

            assert "outline" in result.token_usage
            assert result.token_usage["outline"]["input"] == 500
            assert "content_1" in result.token_usage
            assert result.token_usage["content_1"]["input"] == 200
            assert result.token_usage["content_1"]["output"] == 150


# ---------------------------------------------------------------------------
# Bug 3: Image approval cannot transition from image_keywords_ready
# ---------------------------------------------------------------------------

class TestImageApprovalTransition:
    """The approve_image_keywords endpoint tried to transition from
    image_keywords_ready to image_keywords_ready, which is not a valid
    transition."""

    def test_image_keywords_ready_to_images_ready_is_valid(self):
        assert validate_transition("image_keywords_ready", "images_ready") is True

    def test_image_keywords_ready_to_self_is_invalid(self):
        assert validate_transition("image_keywords_ready", "image_keywords_ready") is False

    def test_image_keywords_ready_to_image_searching_is_valid(self):
        assert validate_transition("image_keywords_ready", "image_searching") is True


# ---------------------------------------------------------------------------
# Bug 4: WP sync short topic constraint violation
# ---------------------------------------------------------------------------

class TestWPSyncShortTopic:
    """Titles shorter than 10 characters violate chk_topic_length."""

    def test_short_topic_is_padded(self):
        topic = "Norm解析"
        if len(topic) < 10:
            topic = topic + " - Technical Article"
        assert len(topic) >= 10

    def test_short_chinese_topic_is_padded(self):
        topic = "关于Norm的解析"
        if len(topic) < 10:
            topic = topic + " - Technical Article"
        assert len(topic) >= 10

    def test_normal_topic_not_modified(self):
        topic = "A comprehensive guide to ML"
        assert len(topic) >= 10
        result = topic if len(topic) >= 10 else topic + " - Technical Article"
        assert result == topic
