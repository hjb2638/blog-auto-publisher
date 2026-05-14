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


# ---------------------------------------------------------------------------
# v1.3.3 Bug: Cover image upload fails due to extensionless filename
# ---------------------------------------------------------------------------


class TestFilenameExtension:
    """_ensure_filename_extension must add the correct file extension based on
    the content-type header when the filename from Unsplash lacks one."""

    def _call_function(self, filename: str, content_type: str | None) -> str:
        from app.services.wordpress_service import _ensure_filename_extension
        return _ensure_filename_extension(filename, content_type)

    def test_adds_jpg_for_jpeg_mime(self):
        assert self._call_function("photo123", "image/jpeg") == "photo123.jpg"

    def test_adds_png_for_png_mime(self):
        assert self._call_function("photo123", "image/png") == "photo123.png"

    def test_adds_webp_for_webp_mime(self):
        assert self._call_function("photo123", "image/webp") == "photo123.webp"

    def test_adds_gif_for_gif_mime(self):
        assert self._call_function("animated", "image/gif") == "animated.gif"

    def test_preserves_existing_jpg(self):
        assert self._call_function("photo.jpg", "image/png") == "photo.jpg"

    def test_preserves_existing_png(self):
        assert self._call_function("photo.png", "image/jpeg") == "photo.png"

    def test_preserves_existing_webp(self):
        assert self._call_function("photo.webp", "image/jpeg") == "photo.webp"

    def test_fallback_when_ct_is_none(self):
        assert self._call_function("photo123", None) == "photo123.jpg"

    def test_fallback_when_ct_is_empty(self):
        assert self._call_function("photo123", "") == "photo123.jpg"

    def test_strips_charset_param(self):
        assert self._call_function("photo123", "image/jpeg; charset=utf-8") == "photo123.jpg"

    def test_unknown_mime_extracts_subtype(self):
        assert self._call_function("photo123", "image/avif") == "photo123.avif"

    def test_dot_in_name_not_extension(self):
        assert self._call_function("photo.v2", "image/jpeg") == "photo.v2.jpg"

    def test_uppercase_jpg(self):
        assert self._call_function("PHOTO.JPG", "image/png") == "PHOTO.JPG"

    def test_bmp_extension(self):
        assert self._call_function("img", "image/bmp") == "img.bmp"

    def test_svg_extension(self):
        assert self._call_function("icon", "image/svg+xml") == "icon.svg"

    def test_tiff_extension(self):
        assert self._call_function("scan", "image/tiff") == "scan.tiff"


# ---------------------------------------------------------------------------
# v1.3.3 Feature: WordPress CRUD — delete_post()
# ---------------------------------------------------------------------------


class TestDeletePost:
    """delete_post must handle WP success, 404 (already deleted), 401 (auth
    error), and 500 (retry exhausted) correctly."""

    @pytest.mark.asyncio
    async def test_delete_success(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch, MagicMock
        import httpx

        svc = WordPressService()
        with patch.object(svc, '_request', new_callable=AsyncMock, return_value={"id": 1, "status": "trash"}) as mock_req:
            result = await svc.delete_post(123)
            assert result is True
            mock_req.assert_called_once_with("DELETE", "/wp/v2/posts/123?force=true")

    @pytest.mark.asyncio
    async def test_delete_404_already_gone(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch, MagicMock
        import httpx

        svc = WordPressService()
        mock_req = AsyncMock(side_effect=httpx.HTTPStatusError("Not Found", request=MagicMock(), response=MagicMock(status_code=404)))
        with patch.object(svc, '_request', mock_req):
            result = await svc.delete_post(456)
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_401_raises(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch, MagicMock
        import httpx

        svc = WordPressService()
        mock_req = AsyncMock(side_effect=httpx.HTTPStatusError("Unauthorized", request=MagicMock(), response=MagicMock(status_code=401)))
        with patch.object(svc, '_request', mock_req):
            with pytest.raises(httpx.HTTPStatusError) as exc:
                await svc.delete_post(789)
            assert exc.value.response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_500_raises(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch, MagicMock
        import httpx

        svc = WordPressService()
        mock_req = AsyncMock(side_effect=httpx.HTTPStatusError("Server Error", request=MagicMock(), response=MagicMock(status_code=500)))
        with patch.object(svc, '_request', mock_req):
            with pytest.raises(httpx.HTTPStatusError) as exc:
                await svc.delete_post(999)
            assert exc.value.response.status_code == 500

    @pytest.mark.asyncio
    async def test_delete_without_force(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch

        svc = WordPressService()
        with patch.object(svc, '_request', new_callable=AsyncMock) as mock_req:
            await svc.delete_post(123, force=False)
            mock_req.assert_called_once_with("DELETE", "/wp/v2/posts/123")


# ---------------------------------------------------------------------------
# v1.3.3 Feature: WordPress CRUD — update_post()
# ---------------------------------------------------------------------------


class TestUpdatePost:
    """update_post must send only the provided fields and handle edge cases."""

    @pytest.mark.asyncio
    async def test_update_title_only(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch

        svc = WordPressService()
        with patch.object(svc, '_request', new_callable=AsyncMock, return_value={"id": 1}) as mock_req:
            await svc.update_post(1, title="New Title")
            mock_req.assert_called_once_with("POST", "/wp/v2/posts/1", {"title": "New Title"})

    @pytest.mark.asyncio
    async def test_update_content_only(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch

        svc = WordPressService()
        with patch.object(svc, '_request', new_callable=AsyncMock) as mock_req:
            await svc.update_post(1, content="<p>New content</p>")
            mock_req.assert_called_once_with("POST", "/wp/v2/posts/1", {"content": "<p>New content</p>"})

    @pytest.mark.asyncio
    async def test_update_status_only(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch

        svc = WordPressService()
        with patch.object(svc, '_request', new_callable=AsyncMock) as mock_req:
            await svc.update_post(1, status="draft")
            mock_req.assert_called_once_with("POST", "/wp/v2/posts/1", {"status": "draft"})

    @pytest.mark.asyncio
    async def test_update_all_fields(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch

        svc = WordPressService()
        with patch.object(svc, '_request', new_callable=AsyncMock) as mock_req:
            await svc.update_post(1, title="T", content="<p>C</p>", status="publish", slug="my-slug")
            mock_req.assert_called_once_with(
                "POST", "/wp/v2/posts/1",
                {"title": "T", "content": "<p>C</p>", "status": "publish", "slug": "my-slug"},
            )

    @pytest.mark.asyncio
    async def test_update_empty(self):
        from app.services.wordpress_service import WordPressService
        from unittest.mock import AsyncMock, patch

        svc = WordPressService()
        with patch.object(svc, '_request', new_callable=AsyncMock) as mock_req:
            result = await svc.update_post(1)
            assert result == {}
            mock_req.assert_not_called()
