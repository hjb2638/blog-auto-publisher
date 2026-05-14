"""Real WordPress API tests.

These tests make actual HTTP requests to the configured WordPress site.
Set RUN_REAL_API_TESTS=1 to enable them. They create and delete real
WordPress resources.

Usage:
  RUN_REAL_API_TESTS=1 python3 -m pytest tests/test_wp_api.py -v
  RUN_REAL_API_TESTS=1 python3 -m pytest tests/ -v -m real_api
"""

import os

import pytest

from app.services.wordpress_service import WordPressService, _ensure_filename_extension

pytestmark = [
    pytest.mark.real_api,
    pytest.mark.skipif(
        os.environ.get("RUN_REAL_API_TESTS") != "1",
        reason="Set RUN_REAL_API_TESTS=1 to run real WordPress API tests",
    ),
]


@pytest.fixture
def wp_service():
    return WordPressService()


@pytest.mark.asyncio
class TestRealWPFilenameExtension:
    """Verify _ensure_filename_extension resolves the actual bug:
    Unsplash URLs produce extensionless filenames that WP rejects."""

    def test_unsplash_url_with_jpeg_mime(self):
        """Simulates the exact scenario: extensionless filename + image/jpeg."""
        filename = "photo-1551288049-bebda4e38f71"
        result = _ensure_filename_extension(filename, "image/jpeg")
        assert result == "photo-1551288049-bebda4e38f71.jpg"

    def test_unsplash_url_with_webp_mime(self):
        """Unsplash CDN can serve WebP based on Accept headers."""
        filename = "photo-1551288049-bebda4e38f71"
        result = _ensure_filename_extension(filename, "image/webp")
        assert result == "photo-1551288049-bebda4e38f71.webp"


@pytest.mark.asyncio
class TestRealWPMediaUpload:
    """Upload a real image to WordPress and verify media is created."""

    async def test_upload_jpeg_image_succeeds(self, wp_service: WordPressService):
        """Upload a small JPEG from Unsplash and verify it gets an ID."""
        test_url = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=200&q=80&fit=crop"
        media = await wp_service.upload_media(test_url, alt_text="Test upload from blog system")
        assert "id" in media
        assert isinstance(media["id"], int)
        assert media["id"] > 0

        await wp_service._request("DELETE", f"/wp/v2/media/{media['id']}?force=true")

    async def test_upload_with_extensionless_filename_works(self, wp_service: WordPressService):
        """The exact scenario that was broken: no extension in filename.
        With _ensure_filename_extension, this should now succeed."""
        import httpx

        test_url = "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=200&q=80&fit=crop"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                test_url,
                headers={"User-Agent": "blog-project/1.0"},
            )
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            assert content_type.startswith("image/"), f"Expected image/*, got {content_type}"

            raw_filename = "photo-1551288049-bebda4e38f71"
            fixed = _ensure_filename_extension(raw_filename, content_type)
            assert "." in fixed, f"Expected extension in filename, got: {fixed}"

        media = await wp_service.upload_media(test_url, alt_text="Test extensionless upload")
        assert "id" in media
        assert media["id"] > 0

        await wp_service._request("DELETE", f"/wp/v2/media/{media['id']}?force=true")


@pytest.mark.asyncio
class TestRealWPPostCRUD:
    """Full lifecycle: create -> update -> delete on WordPress."""

    async def test_create_update_delete_draft_post(self, wp_service: WordPressService):
        """Create a draft, update its title, verify, then delete."""
        post = await wp_service.create_post(
            title="Test Draft Post - Blog System",
            content="<p>This is a test post created by automated tests.</p>",
            status="draft",
        )
        post_id = post["id"]
        assert post_id > 0
        assert post["title"]["rendered"] == "Test Draft Post - Blog System"

        updated = await wp_service.update_post(post_id, title="Updated: Test Draft Post")
        assert updated["title"]["rendered"] == "Updated: Test Draft Post"

        result = await wp_service.delete_post(post_id, force=True)
        assert result is True

    async def test_update_post_status_publish_to_draft(self, wp_service: WordPressService):
        """Change a draft to publish, then back to draft."""
        post = await wp_service.create_post(
            title="Status Toggle Test - Blog System",
            content="<p>Testing status toggling.</p>",
            status="draft",
        )
        post_id = post["id"]
        assert post["status"] == "draft"

        pub = await wp_service.update_post(post_id, status="publish")
        assert pub["status"] == "publish"

        draft = await wp_service.update_post(post_id, status="draft")
        assert draft["status"] == "draft"

        await wp_service.delete_post(post_id, force=True)

    async def test_delete_nonexistent_post_returns_false(self, wp_service: WordPressService):
        """Deleting a post that doesn't exist returns False."""
        result = await wp_service.delete_post(999999, force=True)
        assert result is False

    async def test_update_post_empty_returns_empty_dict(self, wp_service: WordPressService):
        """Calling update_post with no fields should return {} without HTTP call."""
        result = await wp_service.update_post(1)
        assert result == {}
