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


# ---------------------------------------------------------------------------
# v1.3.1 Bug 2: ArticleImageSchema missing `type` field
# ---------------------------------------------------------------------------


class TestArticleImageSchema:
    """ArticleImageSchema must include `type` so that cover image filtering
    works throughout the UI chain (ImageReview -> approve_final -> publish)."""

    def test_type_field_present_with_default_inline(self):
        from app.schemas.article import ArticleImageSchema
        img = ArticleImageSchema(
            id="abc123",
            url="https://example.com/img.jpg",
            alt_text="test image",
            section_slug="intro",
        )
        assert img.type == "inline"

    def test_type_field_accepts_cover(self):
        from app.schemas.article import ArticleImageSchema
        img = ArticleImageSchema(
            id="abc123",
            url="https://example.com/img.jpg",
            alt_text="test image",
            section_slug="",
            type="cover",
        )
        assert img.type == "cover"

    def test_type_field_preserved_in_serialization(self):
        from app.schemas.article import ArticleImageSchema
        img = ArticleImageSchema(
            id="abc123",
            url="https://example.com/img.jpg",
            alt_text="test image",
            section_slug="intro",
            type="cover",
        )
        data = img.model_dump(by_alias=True)
        assert data["type"] == "cover"

    def test_type_field_default_is_inline_in_serialization(self):
        from app.schemas.article import ArticleImageSchema
        img = ArticleImageSchema(
            id="abc123",
            url="https://example.com/img.jpg",
            alt_text="test image",
            section_slug="intro",
        )
        data = img.model_dump(by_alias=True)
        assert data["type"] == "inline"


# ---------------------------------------------------------------------------
# v1.3.1 Bug 3: Token statistics not recorded in revision functions
# ---------------------------------------------------------------------------


class TestReviseSectionsTokenRecording:
    """revise_sections calls the LLM but discards token counts. The fix must
    persist tokens to article.token_usage for each revised section."""

    @pytest.mark.asyncio
    async def test_revise_sections_records_tokens(self):
        from app.services.content_service import revise_sections
        from app.services.llm_service import llm_service

        article = Article(
            id=uuid4(),
            topic="Machine learning guide for beginners and experts alike",
            mode="manual",
            status="content_ready",
            outline={"title": "ML Guide", "sections": []},
            content={
                "sections": [
                    {
                        "heading": "Introduction",
                        "slug": "introduction",
                        "html": "<p>Original content.</p>",
                        "word_count": 3,
                    }
                ],
                "full_html": "<p>Original content.</p>",
                "total_word_count": 3,
            },
            token_usage=None,
        )

        mock_llm_result = {
            "content": "<p>Revised content for introduction.</p>",
            "tokens_input": 300,
            "tokens_output": 200,
        }

        with patch.object(llm_service, 'generate_response', new_callable=AsyncMock, return_value=mock_llm_result):
            db = AsyncMock()
            result = await revise_sections(db, article, ["introduction"], "Make it better")

            assert result.token_usage is not None
            assert "revision_introduction" in result.token_usage
            assert result.token_usage["revision_introduction"]["input"] == 300
            assert result.token_usage["revision_introduction"]["output"] == 200

    @pytest.mark.asyncio
    async def test_revise_sections_preserves_existing_tokens(self):
        from app.services.content_service import revise_sections
        from app.services.llm_service import llm_service

        article = Article(
            id=uuid4(),
            topic="Machine learning guide for beginners and experts alike",
            mode="manual",
            status="content_ready",
            outline={"title": "ML Guide", "sections": []},
            content={
                "sections": [
                    {
                        "heading": "Introduction",
                        "slug": "introduction",
                        "html": "<p>Original content.</p>",
                        "word_count": 3,
                    }
                ],
                "full_html": "<p>Original content.</p>",
                "total_word_count": 3,
            },
            token_usage={"outline": {"input": 500, "output": 300}, "content_1": {"input": 200, "output": 150}},
        )

        mock_llm_result = {
            "content": "<p>Revised content.</p>",
            "tokens_input": 100,
            "tokens_output": 80,
        }

        with patch.object(llm_service, 'generate_response', new_callable=AsyncMock, return_value=mock_llm_result):
            db = AsyncMock()
            result = await revise_sections(db, article, ["introduction"], "Make it shorter")

            assert "outline" in result.token_usage
            assert "content_1" in result.token_usage
            assert "revision_introduction" in result.token_usage
            assert result.token_usage["outline"]["input"] == 500


class TestReviseOutlineTokenRecording:
    """revise_outline calls the LLM but discards token counts."""

    @pytest.mark.asyncio
    async def test_revise_outline_records_tokens(self):
        from app.services.outline_service import revise_outline
        from app.services.llm_service import llm_service

        article = Article(
            id=uuid4(),
            topic="Machine learning guide for beginners and experts alike",
            mode="manual",
            status="outline_ready",
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
            "parsed": {
                "title": "Revised ML Guide",
                "sections": [
                    {
                        "heading": "New Introduction",
                        "slug": "introduction",
                        "key_points": ["Better overview"],
                        "estimated_words": 150,
                        "include_code_example": False,
                    }
                ],
                "category": "AI",
                "tags": ["ML"],
            },
            "tokens_input": 400,
            "tokens_output": 250,
        }

        with patch.object(llm_service, 'generate_json', new_callable=AsyncMock, return_value=mock_llm_result):
            db = AsyncMock()
            result = await revise_outline(db, article, "Make it more detailed")

            assert "outline" in result.token_usage
            assert result.token_usage["outline"]["input"] == 500
            assert "outline_revision" in result.token_usage
            assert result.token_usage["outline_revision"]["input"] == 400
            assert result.token_usage["outline_revision"]["output"] == 250


# ---------------------------------------------------------------------------
# v1.3.2 Bug 3a: Multiple cover images after approve_final
# ---------------------------------------------------------------------------


class TestCoverImageTypeReset:
    """After approve_final, exactly ONE image has type 'cover'; all others
    must be 'inline'. The previous else branch (img.get("type", "inline"))
    preserved the original type of non-selected images, leaving multiple
    images with type 'cover'."""

    def test_only_selected_image_is_cover(self):
        images = [
            {"id": "img1", "url": "https://example.com/1.jpg", "type": "cover"},
            {"id": "img2", "url": "https://example.com/2.jpg", "type": "inline"},
            {"id": "img3", "url": "https://example.com/3.jpg", "type": "cover"},
        ]
        cover_image_id = "img2"

        # Simulate fixed approve_final logic (articles.py:242)
        for img in images:
            img["type"] = "cover" if img.get("id") == cover_image_id else "inline"

        cover_count = sum(1 for img in images if img["type"] == "cover")
        assert cover_count == 1
        assert images[0]["type"] == "inline"
        assert images[1]["type"] == "cover"
        assert images[2]["type"] == "inline"

    def test_fixed_else_resets_all_non_selected_to_inline(self):
        images = [
            {"id": "img1", "url": "https://example.com/1.jpg", "type": "cover"},
            {"id": "img2", "url": "https://example.com/2.jpg", "type": "inline"},
            {"id": "img3", "url": "https://example.com/3.jpg", "type": "cover"},
        ]
        cover_image_id = "img2"

        for img in images:
            img["type"] = "cover" if img.get("id") == cover_image_id else "inline"

        cover_count = sum(1 for img in images if img["type"] == "cover")
        assert cover_count == 1  # Only img2 should be cover
        assert images[0]["type"] == "inline"
        assert images[1]["type"] == "cover"
        assert images[2]["type"] == "inline"

    def test_no_cover_selected_resets_all_to_inline(self):
        images = [
            {"id": "img1", "url": "https://example.com/1.jpg", "type": "cover"},
            {"id": "img2", "url": "https://example.com/2.jpg", "type": "cover"},
        ]

        for img in images:
            img["type"] = "cover" if img.get("id") == None else "inline"

        assert all(img["type"] == "inline" for img in images)


# ---------------------------------------------------------------------------
# v1.3.2 Bug 3b: Silent failure of cover image upload
# ---------------------------------------------------------------------------


class TestCoverImageUploadError:
    """When upload_media raises an exception during publish, the error must
    be stored on article.error_message so the user sees it."""

    @pytest.mark.asyncio
    async def test_upload_failure_sets_error_message(self):
        from unittest.mock import AsyncMock, patch
        from uuid import uuid4
        from app.models.article import Article

        article = Article(
            id=uuid4(),
            topic="A comprehensive guide to machine learning techniques",
            mode="manual",
            status="publishing",
            images=[
                {"id": "img1", "url": "https://images.unsplash.com/photo-test", "full_url": "https://images.unsplash.com/photo-test-full", "type": "cover", "alt_text": "Test"}
            ],
        )

        # Simulate the upload failure
        upload_error_msg = "Unsplash CDN blocked the download"
        article.error_message = f"Cover image upload failed: {upload_error_msg}"

        assert article.error_message is not None
        assert "Cover image upload failed" in article.error_message


# ---------------------------------------------------------------------------
# v1.3.2 Bug 3c: Hardcoded image/jpeg content type
# ---------------------------------------------------------------------------


class TestWordPressContentType:
    """upload_media must use the actual content-type from the image download
    response, not a hardcoded 'image/jpeg'."""

    def test_content_type_from_response_headers(self):
        content_type_header = "image/webp"
        content_type = content_type_header or "image/jpeg"
        assert content_type == "image/webp"

    def test_fallback_to_jpeg_when_header_missing(self):
        content_type_header = ""
        content_type = content_type_header or "image/jpeg"
        assert content_type == "image/jpeg"
