import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_article_topic_too_short(client: AsyncClient):
    response = await client.post("/api/v1/articles", json={
        "topic": "Short",
        "mode": "manual",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_article_topic_too_long(client: AsyncClient):
    response = await client.post("/api/v1/articles", json={
        "topic": "X" * 501,
        "mode": "manual",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_article_invalid_mode(client: AsyncClient):
    response = await client.post("/api/v1/articles", json={
        "topic": "A valid topic about machine learning and AI systems",
        "mode": "invalid",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_articles(client: AsyncClient):
    response = await client.get("/api/v1/articles")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "meta" in data


@pytest.mark.asyncio
async def test_list_articles_with_pagination(client: AsyncClient):
    response = await client.get("/api/v1/articles?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["limit"] == 5


@pytest.mark.asyncio
async def test_get_article_not_found(client: AsyncClient):
    response = await client.get("/api/v1/articles/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "database" in str(data["data"])


@pytest.mark.asyncio
async def test_create_article_success(client: AsyncClient):
    mock_article = AsyncMock()
    mock_article.id = "550e8400-e29b-41d4-a716-446655440000"
    mock_article.topic = "How to finetune LoRA models for NLP tasks"
    mock_article.requirements = None
    mock_article.mode = "manual"
    mock_article.status = "outline_ready"
    mock_article.version = 1
    mock_article.outline = None
    mock_article.content = None
    mock_article.images = None
    mock_article.image_plan = None
    mock_article.full_html = None
    mock_article.progress = None
    mock_article.wp_post_id = None
    mock_article.wp_post_url = None
    mock_article.wp_slug = None
    mock_article.error_message = None
    mock_article.token_usage = None
    mock_article.source = "local"
    mock_article.created_at = "2024-01-01T00:00:00Z"
    mock_article.updated_at = "2024-01-01T00:00:00Z"

    with (
        patch('app.routers.articles.generate_outline', new_callable=AsyncMock, return_value=mock_article),
        patch.object(AsyncSession, 'refresh', new_callable=AsyncMock),
    ):
        response = await client.post("/api/v1/articles", json={
            "topic": "How to finetune LoRA models for NLP tasks",
            "mode": "manual",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["topic"] == "How to finetune LoRA models for NLP tasks"


# ---------------------------------------------------------------------------
# v1.3.3: Delete endpoint with WP sync & Update-WP endpoint
# ---------------------------------------------------------------------------


from sqlalchemy import text
from uuid import UUID


async def _create_test_article(db: AsyncSession, **kwargs) -> str:
    """Helper to insert a test article and return its UUID string."""
    from uuid import uuid4
    article_id = kwargs.pop("id", uuid4())
    await db.execute(
        text("""
            INSERT INTO articles (id, topic, mode, status, version, wp_post_id, wp_post_url, wp_slug, source, full_html, outline, content)
            VALUES (:id, :topic, :mode, :status, :version, :wp_post_id, :wp_post_url, :wp_slug, :source, :full_html, :outline, cast(:content AS jsonb))
        """),
        {
            "id": article_id,
            "topic": kwargs.get("topic", "A comprehensive test article for integration testing"),
            "mode": kwargs.get("mode", "manual"),
            "status": kwargs.get("status", "published"),
            "version": kwargs.get("version", 1),
            "wp_post_id": kwargs.get("wp_post_id"),
            "wp_post_url": kwargs.get("wp_post_url"),
            "wp_slug": kwargs.get("wp_slug"),
            "source": kwargs.get("source", "local"),
            "full_html": kwargs.get("full_html"),
            "outline": kwargs.get("outline"),
            "content": kwargs.get("content"),
        },
    )
    await db.commit()
    return str(article_id)


async def _cleanup_article(db: AsyncSession, article_id: str):
    """Delete a test article by ID, ignoring if it no longer exists."""
    try:
        await db.execute(text("DELETE FROM articles WHERE id = :id"), {"id": UUID(article_id)})
        await db.commit()
    except Exception:
        await db.rollback()
        await db.execute(text("DELETE FROM articles WHERE id = :id"), {"id": UUID(article_id)})
        await db.commit()


class TestDeleteArticleWithWPSync:
    """DELETE /{id} with optional delete_wp query param."""

    @pytest.mark.asyncio
    async def test_delete_local_only(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, patch
        article_id = await _create_test_article(test_session, wp_post_id=123, wp_post_url="https://example.com/post")
        with patch('app.routers.articles.wordpress_service.delete_post', new_callable=AsyncMock) as mock_del:
            response = await client.delete(f"/api/v1/articles/{article_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["deleted"] is True
            mock_del.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_with_wp_sync(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, patch
        article_id = await _create_test_article(test_session, wp_post_id=123)
        with patch('app.routers.articles.wordpress_service.delete_post', new_callable=AsyncMock, return_value=True) as mock_del:
            response = await client.delete(f"/api/v1/articles/{article_id}?delete_wp=true")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["deleted"] is True
            assert data["data"]["wpDeleted"] is True
            mock_del.assert_called_once_with(123)

    @pytest.mark.asyncio
    async def test_delete_with_wp_404(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, patch
        article_id = await _create_test_article(test_session, wp_post_id=456)
        with patch('app.routers.articles.wordpress_service.delete_post', new_callable=AsyncMock, return_value=False) as mock_del:
            response = await client.delete(f"/api/v1/articles/{article_id}?delete_wp=true")
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["wpDeleted"] is False
            assert data["data"]["deleted"] is True

    @pytest.mark.asyncio
    async def test_delete_no_wp_id_skips_wp(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, patch
        article_id = await _create_test_article(test_session, wp_post_id=None)
        with patch('app.routers.articles.wordpress_service.delete_post', new_callable=AsyncMock) as mock_del:
            response = await client.delete(f"/api/v1/articles/{article_id}?delete_wp=true")
            assert response.status_code == 200
            mock_del.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_publishing_article(self, client: AsyncClient, test_session: AsyncSession):
        article_id = await _create_test_article(test_session, status="publishing")
        try:
            response = await client.delete(f"/api/v1/articles/{article_id}")
            assert response.status_code == 409
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, client: AsyncClient):
        response = await client.delete("/api/v1/articles/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestUpdateWpArticle:
    """POST /{id}/update-wp endpoint."""

    @pytest.mark.asyncio
    async def test_update_wp_title(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, patch
        article_id = await _create_test_article(test_session, wp_post_id=100, outline='{"title":"Old Title","sections":[]}')
        try:
            with patch('app.routers.articles.wordpress_service.update_post', new_callable=AsyncMock) as mock_upd:
                response = await client.post(f"/api/v1/articles/{article_id}/update-wp", json={"title": "New Title"})
                assert response.status_code == 200
                mock_upd.assert_called_once()
                call_args = mock_upd.call_args
                assert call_args[0][0] == 100
                assert call_args[1]["title"] == "New Title"
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_update_wp_content(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, patch
        article_id = await _create_test_article(test_session, wp_post_id=100)
        try:
            with patch('app.routers.articles.wordpress_service.update_post', new_callable=AsyncMock) as mock_upd:
                response = await client.post(f"/api/v1/articles/{article_id}/update-wp", json={"content": "<p>new</p>"})
                assert response.status_code == 200
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_update_wp_status_draft(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, patch
        article_id = await _create_test_article(test_session, wp_post_id=100)
        try:
            with patch('app.routers.articles.wordpress_service.update_post', new_callable=AsyncMock) as mock_upd:
                response = await client.post(f"/api/v1/articles/{article_id}/update-wp", json={"status": "draft"})
                assert response.status_code == 200
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_update_wp_not_published(self, client: AsyncClient, test_session: AsyncSession):
        article_id = await _create_test_article(test_session, status="content_ready", wp_post_id=None)
        try:
            response = await client.post(f"/api/v1/articles/{article_id}/update-wp", json={"title": "New"})
            assert response.status_code == 409
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_update_wp_no_wp_post_id(self, client: AsyncClient, test_session: AsyncSession):
        article_id = await _create_test_article(test_session, status="published", wp_post_id=None)
        try:
            response = await client.post(f"/api/v1/articles/{article_id}/update-wp", json={"title": "New"})
            assert response.status_code == 409
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_update_wp_invalid_status(self, client: AsyncClient, test_session: AsyncSession):
        article_id = await _create_test_article(test_session, wp_post_id=100)
        try:
            response = await client.post(f"/api/v1/articles/{article_id}/update-wp", json={"status": "invalid"})
            assert response.status_code == 422
        finally:
            await _cleanup_article(test_session, article_id)


# ---------------------------------------------------------------------------
# Batch 2: Service method unit tests
# ---------------------------------------------------------------------------


class TestServiceUpdateOutline:
    """article_service.update_outline()"""

    @pytest.mark.asyncio
    async def test_updates_title(self, test_session: AsyncSession):
        from app.services.article_service import update_outline
        from app.models.article import Article

        article_id = await _create_test_article(test_session, outline='{"title":"Old","sections":[]}')
        try:
            result = await update_outline(db=test_session,
                article=await test_session.get(Article, UUID(article_id)),
                title="New Title")
            assert result.outline["title"] == "New Title"
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_updates_sections(self, test_session: AsyncSession):
        from app.services.article_service import update_outline
        from app.models.article import Article

        article_id = await _create_test_article(test_session, outline='{"title":"T","sections":[{"heading":"A"}]}')
        try:
            sections = [{"heading": "Updated A"}, {"heading": "New B"}]
            result = await update_outline(db=test_session,
                article=await test_session.get(Article, UUID(article_id)),
                sections=sections)
            assert len(result.outline["sections"]) == 2
            assert result.outline["sections"][0]["heading"] == "Updated A"
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_none_outline_sets_empty_dict(self, test_session: AsyncSession):
        from app.services.article_service import update_outline
        from app.models.article import Article

        article_id = await _create_test_article(test_session, outline=None)
        try:
            article = await test_session.get(Article, UUID(article_id))
            assert article.outline is None
            result = await update_outline(db=test_session, article=article, title="Started fresh")
            assert result.outline["title"] == "Started fresh"
        finally:
            await _cleanup_article(test_session, article_id)


class TestServiceUpdateContentSections:
    """article_service.update_content_sections()"""

    @pytest.mark.asyncio
    async def test_updates_section_html(self, test_session: AsyncSession):
        from app.services.article_service import update_content_sections
        from app.models.article import Article

        import json
        content = json.dumps({"sections": [{"slug": "intro", "html": "<p>old</p>"}]})
        article_id = await _create_test_article(test_session, content=content)
        try:
            result = await update_content_sections(
                test_session,
                await test_session.get(Article, UUID(article_id)),
                {"intro": "<p>new</p>"},
            )
            assert result.content["sections"][0]["html"] == "<p>new</p>"
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_ignores_unknown_slug(self, test_session: AsyncSession):
        from app.services.article_service import update_content_sections
        from app.models.article import Article

        import json
        content = json.dumps({"sections": [{"slug": "intro", "html": "<p>stay</p>"}]})
        article_id = await _create_test_article(test_session, content=content)
        try:
            result = await update_content_sections(
                test_session,
                await test_session.get(Article, UUID(article_id)),
                {"nonexistent": "<p>ignored</p>"},
            )
            assert result.content["sections"][0]["html"] == "<p>stay</p>"
        finally:
            await _cleanup_article(test_session, article_id)


class TestServiceApplyFinalImages:
    """article_service.apply_final_images()"""

    @pytest.mark.asyncio
    async def test_selects_images(self, test_session: AsyncSession):
        from app.services.article_service import apply_final_images
        from app.models.article import Article

        import json
        images = json.dumps([
            {"id": "img-1", "url": "https://example.com/1.jpg"},
            {"id": "img-2", "url": "https://example.com/2.jpg"},
            {"id": "img-3", "url": "https://example.com/3.jpg"},
        ])
        article_id = await _create_test_article(test_session, full_html="<p>content</p>")
        await test_session.execute(
            text("UPDATE articles SET images = :images WHERE id = :id"),
            {"images": images, "id": UUID(article_id)},
        )
        await test_session.commit()
        try:
            result = await apply_final_images(
                test_session,
                await test_session.get(Article, UUID(article_id)),
                selected=["img-1", "img-3"],
            )
            assert len(result.images) == 2
            assert result.images[0]["id"] == "img-1"
            assert result.images[1]["id"] == "img-3"
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_removes_images(self, test_session: AsyncSession):
        from app.services.article_service import apply_final_images
        from app.models.article import Article

        import json
        images = json.dumps([
            {"id": "img-1", "url": "https://example.com/1.jpg"},
            {"id": "img-2", "url": "https://example.com/2.jpg"},
        ])
        article_id = await _create_test_article(test_session, full_html="<p>content</p>")
        await test_session.execute(
            text("UPDATE articles SET images = :images WHERE id = :id"),
            {"images": images, "id": UUID(article_id)},
        )
        await test_session.commit()
        try:
            result = await apply_final_images(
                test_session,
                await test_session.get(Article, UUID(article_id)),
                removed=["img-1"],
            )
            assert len(result.images) == 1
            assert result.images[0]["id"] == "img-2"
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_sets_cover_image(self, test_session: AsyncSession):
        from app.services.article_service import apply_final_images
        from app.models.article import Article

        import json
        images = json.dumps([
            {"id": "img-1", "url": "https://example.com/1.jpg"},
            {"id": "img-2", "url": "https://example.com/2.jpg"},
        ])
        article_id = await _create_test_article(test_session, full_html="<p>content</p>")
        await test_session.execute(
            text("UPDATE articles SET images = :images WHERE id = :id"),
            {"images": images, "id": UUID(article_id)},
        )
        await test_session.commit()
        try:
            result = await apply_final_images(
                test_session,
                await test_session.get(Article, UUID(article_id)),
                cover_id="img-1",
            )
            assert result.images[0]["type"] == "cover"
            assert result.images[1]["type"] == "inline"
        finally:
            await _cleanup_article(test_session, article_id)


class TestPublishService:
    """publish_service.publish_article()"""

    @pytest.mark.asyncio
    async def test_publishes_with_minimal_params(self, test_session: AsyncSession):
        from unittest.mock import AsyncMock, MagicMock, patch
        from app.models.article import Article
        from app.services import publish_service
        import json

        article_id = await _create_test_article(
            test_session,
            status="final_approved",
            outline=json.dumps({"title": "Test Pub", "sections": []}),
        )
        try:
            article = await test_session.get(Article, UUID(article_id))

            wp_mock = MagicMock()
            wp_mock.create_post = AsyncMock(return_value={
                "id": 999, "link": "https://example.com/test", "slug": "test-pub",
            })

            result = await publish_service.publish_article(
                db=test_session,
                article=article,
                wordpress_service=wp_mock,
                status="publish",
            )

            assert result.wp_post_id == 999
            assert result.wp_post_url == "https://example.com/test"
            assert result.wp_slug == "test-pub"
            assert result.status == "published"
            wp_mock.create_post.assert_called_once()
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_raises_publish_error_on_failure(self, test_session: AsyncSession):
        from unittest.mock import AsyncMock, MagicMock, patch
        from app.models.article import Article
        from app.services import publish_service
        import json

        article_id = await _create_test_article(
            test_session,
            status="final_approved",
            outline=json.dumps({"title": "Fail Pub", "sections": []}),
        )
        try:
            article = await test_session.get(Article, UUID(article_id))

            wp_mock = MagicMock()
            wp_mock.create_post = AsyncMock(side_effect=Exception("WP API down"))

            with pytest.raises(publish_service.PublishError):
                await publish_service.publish_article(
                    db=test_session,
                    article=article,
                    wordpress_service=wp_mock,
                    status="publish",
                )

            await test_session.refresh(article)
            assert article.status == "failed"
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_uploads_cover_image(self, test_session: AsyncSession):
        from unittest.mock import AsyncMock, MagicMock, patch
        from app.models.article import Article
        from app.services import publish_service
        import json

        images = json.dumps([
            {"id": "cover-1", "url": "https://images.unsplash.com/photo-1", "type": "cover", "alt_text": "Cover image"},
            {"id": "inline-1", "url": "https://images.unsplash.com/photo-2", "type": "inline"},
        ])
        article_id = await _create_test_article(
            test_session,
            status="final_approved",
            outline=json.dumps({"title": "Cover Test", "sections": []}),
            full_html="<p>content</p>",
        )
        await test_session.execute(
            text("UPDATE articles SET images = :images WHERE id = :id"),
            {"images": images, "id": UUID(article_id)},
        )
        await test_session.commit()
        try:
            article = await test_session.get(Article, UUID(article_id))

            wp_mock = MagicMock()
            wp_mock.create_post = AsyncMock(return_value={
                "id": 1000, "link": "https://example.com/cover-test", "slug": "cover-test",
            })
            wp_mock.upload_media = AsyncMock(return_value={"id": 555})

            result = await publish_service.publish_article(
                db=test_session,
                article=article,
                wordpress_service=wp_mock,
                status="publish",
            )

            assert result.wp_post_id == 1000
            wp_mock.upload_media.assert_called_once()
            wp_mock.create_post.assert_called_once()
            _, kwargs = wp_mock.create_post.call_args
            assert kwargs["featured_media_id"] == 555
        finally:
            await _cleanup_article(test_session, article_id)


# ---------------------------------------------------------------------------
# Batch 3: Service layer consolidation tests
# ---------------------------------------------------------------------------


class TestFetchUnsplashImages:
    """_fetch_unsplash_images() — new shared helper for Unsplash API calls."""

    @pytest.mark.asyncio
    async def test_parses_response_correctly(self):
        """Verify successful Unsplash API call returns parsed image dicts."""
        from app.services.image_service import _fetch_unsplash_images
        from unittest.mock import MagicMock

        mock_response_data = {
            "results": [
                {
                    "id": "photo-abc",
                    "urls": {"small": "https://ex.com/s.jpg", "regular": "https://ex.com/r.jpg", "thumb": "https://ex.com/t.jpg"},
                    "links": {"html": "https://unsplash.com/photo-abc"},
                    "user": {"name": "Jane Photo"},
                }
            ]
        }

        mock_secret = MagicMock()
        mock_secret.get_secret_value.return_value = "mock-key"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response_data
        mock_resp.headers = {}
        mock_get = AsyncMock(return_value=mock_resp)

        with (
            patch('app.services.image_service.settings.unsplash_access_key', mock_secret),
            patch('app.services.image_service.httpx.AsyncClient.get', mock_get),
        ):
            results = await _fetch_unsplash_images("test keyword", per_page=3)

        assert len(results) == 1
        assert results[0]["id"] == "photo-abc"
        assert results[0]["alt_text"] == "test keyword"
        assert results[0]["source"] == "unsplash"
        assert results[0]["photographer"] == "Jane Photo"
        assert "full_url" in results[0]

    @pytest.mark.asyncio
    async def test_returns_empty_list_on_api_error(self):
        """Verify non-200 response returns empty list gracefully."""
        from app.services.image_service import _fetch_unsplash_images
        from unittest.mock import MagicMock

        mock_secret = MagicMock()
        mock_secret.get_secret_value.return_value = "mock-key"

        with (
            patch('app.services.image_service.settings.unsplash_access_key', mock_secret),
            patch('app.services.image_service.httpx.AsyncClient') as mock_client_cls,
        ):
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            mock_resp = AsyncMock()
            mock_resp.status_code = 403
            mock_resp.headers = {}
            mock_client.get.return_value = mock_resp

            results = await _fetch_unsplash_images("test", per_page=3)

        assert results == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_key_missing(self):
        """Verify missing Unsplash key returns empty list."""
        from app.services.image_service import _fetch_unsplash_images

        with patch('app.services.image_service.settings.unsplash_access_key', None):
            results = await _fetch_unsplash_images("test", per_page=3)

        assert results == []


class TestSyncAllPostsWithImporter:
    """sync_all_posts(importer=...) callback pattern."""

    @pytest.mark.asyncio
    async def test_importer_receives_posts(self):
        """Verify importer callback is invoked for fetched posts."""
        from unittest.mock import AsyncMock, MagicMock
        from app.services.wordpress_service import wordpress_service

        mock_page_1 = [
            {"id": 101, "title": {"rendered": "Post 1"}},
            {"id": 102, "title": {"rendered": "Post 2"}},
        ]
        mock_headers = {"x-wp-totalpages": "1", "x-wp-total": "2"}

        with patch.object(wordpress_service, '_request_with_headers', new_callable=AsyncMock) as mock_req:
            mock_req.return_value = (mock_page_1, mock_headers)

            call_count = 0
            results = []

            async def _importer(post: dict) -> str:
                nonlocal call_count, results
                call_count += 1
                results.append(post["id"])
                return "imported"

            result = await wordpress_service.sync_all_posts(importer=_importer)

            assert call_count == 2
            assert results == [101, 102]
            assert result["imported"] == 2


class TestImportFromWordPress:
    """article_service.import_from_wordpress()"""

    @pytest.mark.asyncio
    async def test_creates_article_from_wp_post(self, test_session: AsyncSession):
        """Verify WP post dict creates a new Article with correct fields."""
        from app.services.article_service import import_from_wordpress

        wp_post = {
            "id": 99999,
            "title": {"rendered": "A Test WordPress Post"},
            "link": "https://example.com/test-wp-post",
            "slug": "test-wp-post",
            "content": {"rendered": "<p>Hello from WordPress</p>"},
        }

        try:
            result = await import_from_wordpress(test_session, wp_post)
            assert result == "imported"

            from app.models.article import Article
            from sqlalchemy import select
            article = (await test_session.execute(
                select(Article).where(Article.wp_post_id == 99999)
            )).scalar()
            assert article is not None
            assert article.topic == "A Test WordPress Post"
            assert article.wp_slug == "test-wp-post"
            assert article.wp_post_url == "https://example.com/test-wp-post"
            assert article.full_html == "<p>Hello from WordPress</p>"
            assert article.status == "published"
            assert article.source == "wordpress"
        finally:
            await test_session.execute(
                text("DELETE FROM articles WHERE wp_post_id = 99999")
            )
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_skips_existing_wp_post(self, test_session: AsyncSession):
        """Verify existing wp_post_id returns 'skipped'."""
        from app.services.article_service import import_from_wordpress

        article_id = await _create_test_article(
            test_session,
            wp_post_id=88888,
            topic="Existing WP Article",
        )
        try:
            wp_post = {
                "id": 88888,
                "title": {"rendered": "Existing WP Article"},
                "link": "https://example.com/existing",
                "slug": "existing",
                "content": {"rendered": "<p>Existing</p>"},
            }

            result = await import_from_wordpress(test_session, wp_post)
            assert result == "skipped"
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_short_title_appends_suffix(self, test_session: AsyncSession):
        """Verify short title gets '- Technical Article' appended."""
        from app.services.article_service import import_from_wordpress

        short_post = {
            "id": 77777,
            "title": {"rendered": "Short"},
            "link": "https://example.com/short",
            "slug": "short",
            "content": {"rendered": "<p>Short content</p>"},
        }

        try:
            await import_from_wordpress(test_session, short_post)

            from app.models.article import Article
            from sqlalchemy import select
            article = (await test_session.execute(
                select(Article).where(Article.wp_post_id == 77777)
            )).scalar()
            assert article is not None
            assert "Technical Article" in article.topic
            assert len(article.topic) > 10
        finally:
            await test_session.execute(
                text("DELETE FROM articles WHERE wp_post_id = 77777")
            )
            await test_session.commit()


class TestStepBackMap:
    """STEP_BACK_MAP in article_service.py"""

    def test_has_expected_values(self):
        """Verify STEP_BACK_MAP contains all expected step-back targets."""
        from app.services.article_service import STEP_BACK_MAP

        expected = {
            "outline_ready": "draft",
            "content_ready": "outline_ready",
            "image_keywords_generating": "content_ready",
            "image_keywords_ready": "content_ready",
            "images_ready": "image_keywords_ready",
            "final_approved": "images_ready",
        }

        assert STEP_BACK_MAP == expected


# ---------------------------------------------------------------------------
# v1.5.1: Batch operations unification (unpublish + delete_wp flag)
# ---------------------------------------------------------------------------


class TestUnpublishArticle:
    """article_service.unpublish_article() — unpublish from WordPress + set to final_approved."""

    @pytest.mark.asyncio
    async def test_unpublishes_published_article(self, test_session: AsyncSession):
        from unittest.mock import AsyncMock, MagicMock
        from app.services.article_service import unpublish_article
        from app.models.article import Article
        import json

        article_id = await _create_test_article(
            test_session,
            status="published",
            wp_post_id=500,
            outline=json.dumps({"title": "Unpublish Test", "sections": []}),
        )
        try:
            article = await test_session.get(Article, UUID(article_id))

            wp_mock = MagicMock()
            wp_mock.update_post = AsyncMock(return_value={"status": "draft"})

            result = await unpublish_article(
                db=test_session,
                article=article,
                wordpress_service=wp_mock,
            )

            assert result.status == "final_approved"
            wp_mock.update_post.assert_called_once_with(500, status="draft")
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_raises_for_non_published(self, test_session: AsyncSession):
        from unittest.mock import MagicMock
        from app.services.article_service import unpublish_article
        from app.models.article import Article
        import json

        article_id = await _create_test_article(
            test_session,
            status="draft",
            outline=json.dumps({"title": "Draft"}),
        )
        try:
            article = await test_session.get(Article, UUID(article_id))
            wp_mock = MagicMock()

            with pytest.raises(ValueError, match="Can only unpublish published articles"):
                await unpublish_article(
                    db=test_session,
                    article=article,
                    wordpress_service=wp_mock,
                )
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_raises_for_no_wp_post_id(self, test_session: AsyncSession):
        from unittest.mock import MagicMock
        from app.services.article_service import unpublish_article
        from app.models.article import Article
        import json

        article_id = await _create_test_article(
            test_session,
            status="published",
            wp_post_id=None,
            outline=json.dumps({"title": "No WP ID"}),
        )
        try:
            article = await test_session.get(Article, UUID(article_id))
            wp_mock = MagicMock()

            with pytest.raises(ValueError, match="no WordPress post ID"):
                await unpublish_article(
                    db=test_session,
                    article=article,
                    wordpress_service=wp_mock,
                )
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_raises_on_wp_401(self, test_session: AsyncSession):
        from unittest.mock import AsyncMock, MagicMock
        from app.services.article_service import unpublish_article
        from app.models.article import Article
        from httpx import HTTPStatusError, Request, Response
        import json

        article_id = await _create_test_article(
            test_session,
            status="published",
            wp_post_id=501,
            outline=json.dumps({"title": "Auth Fail"}),
        )
        try:
            article = await test_session.get(Article, UUID(article_id))
            wp_mock = MagicMock()
            req = Request("POST", "https://example.com")
            resp = Response(401, request=req)
            wp_mock.update_post = AsyncMock(
                side_effect=HTTPStatusError("Unauthorized", request=req, response=resp)
            )

            with pytest.raises(ValueError, match="WordPress auth failed"):
                await unpublish_article(
                    db=test_session,
                    article=article,
                    wordpress_service=wp_mock,
                )
        finally:
            await _cleanup_article(test_session, article_id)


class TestBatchUnpublish:
    """POST /articles/batch with action=unpublish"""

    @pytest.mark.asyncio
    async def test_batch_unpublish_success(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, MagicMock, patch
        import json

        article_id = await _create_test_article(
            test_session,
            status="published",
            wp_post_id=600,
            outline=json.dumps({"title": "Batch Unpublish"}),
        )
        try:
            wp_mock = MagicMock()
            wp_mock.update_post = AsyncMock(return_value={"status": "draft"})

            with patch('app.routers.articles.wordpress_service', wp_mock):
                response = await client.post("/api/v1/articles/batch", json={
                    "ids": [article_id],
                    "action": "unpublish",
                })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["processed"] == 1
            assert data["data"]["failed"] == []
            wp_mock.update_post.assert_called_once_with(600, status="draft")
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_batch_unpublish_not_published(self, client: AsyncClient, test_session: AsyncSession):
        import json

        article_id = await _create_test_article(
            test_session,
            status="draft",
            outline=json.dumps({"title": "Draft Article"}),
        )
        try:
            response = await client.post("/api/v1/articles/batch", json={
                "ids": [article_id],
                "action": "unpublish",
            })

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["processed"] == 0
            assert len(data["data"]["failed"]) == 1
            assert "Can only unpublish published articles" in data["data"]["failed"][0]["reason"]
        finally:
            await _cleanup_article(test_session, article_id)


class TestBatchDeleteWithDeleteWp:
    """POST /articles/batch with action=delete and delete_wp flag"""

    @pytest.mark.asyncio
    async def test_batch_delete_with_wp(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, MagicMock, patch

        article_id = await _create_test_article(
            test_session,
            wp_post_id=700,
        )
        try:
            wp_mock = MagicMock()
            wp_mock.delete_post = AsyncMock(return_value=True)

            with patch('app.routers.articles.wordpress_service', wp_mock):
                response = await client.post("/api/v1/articles/batch", json={
                    "ids": [article_id],
                    "action": "delete",
                    "deleteWp": True,
                })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["processed"] == 1
            wp_mock.delete_post.assert_called_once_with(700)
        finally:
            await _cleanup_article(test_session, article_id)

    @pytest.mark.asyncio
    async def test_batch_delete_without_wp(self, client: AsyncClient, test_session: AsyncSession):
        from unittest.mock import AsyncMock, MagicMock, patch

        article_id = await _create_test_article(
            test_session,
            wp_post_id=701,
        )
        try:
            wp_mock = MagicMock()
            wp_mock.delete_post = AsyncMock(return_value=True)

            with patch('app.routers.articles.wordpress_service', wp_mock):
                response = await client.post("/api/v1/articles/batch", json={
                    "ids": [article_id],
                    "action": "delete",
                    "deleteWp": False,
                })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["processed"] == 1
            wp_mock.delete_post.assert_not_called()
        finally:
            await _cleanup_article(test_session, article_id)


class TestValidTransitionsUnpublish:
    """VALID_TRANSITIONS must include published → final_approved"""

    def test_published_can_transition_to_final_approved(self):
        from app.services.article_service import VALID_TRANSITIONS

        assert "final_approved" in VALID_TRANSITIONS.get("published", set())


class TestArticleDisplayTitle:
    """article_to_list_item display_title computation."""

    def _make_mock(self, **kwargs):
        from unittest.mock import MagicMock
        from uuid import uuid4

        article = MagicMock()
        article.id = uuid4()
        article.topic = "A test topic about machine learning and AI"
        article.outline = None
        article.status = "published"
        article.mode = "manual"
        article.wp_post_url = None
        article.token_usage = None
        article.source = "local"
        article.created_at = "2024-01-01T00:00:00Z"
        article.updated_at = "2024-01-01T00:00:00Z"
        article.version = 1
        for k, v in kwargs.items():
            setattr(article, k, v)
        return article

    def test_display_title_uses_outline_title(self):
        from app.services.article_service import article_to_list_item

        article = self._make_mock(topic="a long topic about rag technology", outline={"title": "RAG技术详解：从原理到生产级应用"})

        result = article_to_list_item(article)

        assert result.display_title == "RAG技术详解：从原理到生产级应用"

    def test_display_title_falls_back_to_topic(self):
        from app.services.article_service import article_to_list_item

        article = self._make_mock(topic="A test topic about machine learning and AI", outline=None)

        result = article_to_list_item(article)

        assert result.display_title == "A test topic about machine learning and AI"

    def test_display_title_truncates_long_outline_title(self):
        from app.services.article_service import article_to_list_item

        article = self._make_mock(topic="a topic", outline={"title": "X" * 100})

        result = article_to_list_item(article)

        assert len(result.display_title) <= 80
        assert result.display_title == "X" * 80

    def test_display_title_falls_back_to_truncated_topic(self):
        from app.services.article_service import article_to_list_item

        article = self._make_mock(topic="Y" * 100, outline=None)

        result = article_to_list_item(article)

        assert result.display_title == "Y" * 80


class TestArticleSorting:
    """GET /api/v1/articles with sort params."""

    @pytest.mark.asyncio
    async def test_sort_by_created_at_asc(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from datetime import datetime, timezone
        from sqlalchemy import text

        id1 = uuid4()
        id2 = uuid4()
        id3 = uuid4()

        await test_session.execute(
            text("""
                INSERT INTO articles (id, topic, mode, status, source, version, created_at, updated_at)
                VALUES (:id1, :t1, 'manual', 'draft', 'local', 1, :c1, :c1),
                       (:id2, :t2, 'manual', 'draft', 'local', 1, :c2, :c2),
                       (:id3, :t3, 'manual', 'draft', 'local', 1, :c3, :c3)
            """),
            {
                "id1": id1, "t1": "Z article - latest", "c1": datetime(2024, 3, 1, tzinfo=timezone.utc),
                "id2": id2, "t2": "M article - middle", "c2": datetime(2024, 2, 1, tzinfo=timezone.utc),
                "id3": id3, "t3": "A article - oldest", "c3": datetime(2024, 1, 1, tzinfo=timezone.utc),
            },
        )
        await test_session.commit()

        try:
            response = await client.get("/api/v1/articles?sort_by=created_at&sort_order=asc&limit=50")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            topics = [item["topic"] for item in data["data"]]
            assert topics.index("A article - oldest") < topics.index("M article - middle")
            assert topics.index("M article - middle") < topics.index("Z article - latest")
        finally:
            for aid in [id1, id2, id3]:
                await test_session.execute(text("DELETE FROM articles WHERE id = :id"), {"id": aid})
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_sort_by_created_at_desc_default(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from datetime import datetime, timezone
        from sqlalchemy import text

        id1 = uuid4()
        id2 = uuid4()

        await test_session.execute(
            text("""
                INSERT INTO articles (id, topic, mode, status, source, version, created_at, updated_at)
                VALUES (:id1, :t1, 'manual', 'draft', 'local', 1, :c1, :c1),
                       (:id2, :t2, 'manual', 'draft', 'local', 1, :c2, :c2)
            """),
            {
                "id1": id1, "t1": "Older article", "c1": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "id2": id2, "t2": "Newer article", "c2": datetime(2024, 3, 1, tzinfo=timezone.utc),
            },
        )
        await test_session.commit()

        try:
            response = await client.get("/api/v1/articles?limit=50")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            topics = [item["topic"] for item in data["data"]]
            assert topics.index("Newer article") < topics.index("Older article")
        finally:
            for aid in [id1, id2]:
                await test_session.execute(text("DELETE FROM articles WHERE id = :id"), {"id": aid})
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_sort_by_total_tokens_asc(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from sqlalchemy import text

        id1 = uuid4()
        id2 = uuid4()
        id3 = uuid4()

        await test_session.execute(
            text("""
                INSERT INTO articles (id, topic, mode, status, source, version, token_usage)
                VALUES (:id1, :t1, 'manual', 'draft', 'local', 1, :tu1),
                       (:id2, :t2, 'manual', 'draft', 'local', 1, :tu2),
                       (:id3, :t3, 'manual', 'draft', 'local', 1, :tu3)
            """),
            {
                "id1": id1, "t1": "High tokens", "tu1": '{"gen": {"input": 500, "output": 500}}',
                "id2": id2, "t2": "Low tokens", "tu2": '{"gen": {"input": 50, "output": 50}}',
                "id3": id3, "t3": "Medium tokens", "tu3": '{"gen": {"input": 200, "output": 200}}',
            },
        )
        await test_session.commit()

        try:
            response = await client.get("/api/v1/articles?sort_by=total_tokens&sort_order=asc&limit=50")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            topics = [item["topic"] for item in data["data"]]
            assert topics.index("Low tokens") < topics.index("Medium tokens")
            assert topics.index("Medium tokens") < topics.index("High tokens")
        finally:
            for aid in [id1, id2, id3]:
                await test_session.execute(text("DELETE FROM articles WHERE id = :id"), {"id": aid})
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_sort_by_total_tokens_desc(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from sqlalchemy import text

        id1 = uuid4()
        id2 = uuid4()

        await test_session.execute(
            text("""
                INSERT INTO articles (id, topic, mode, status, source, version, token_usage)
                VALUES (:id1, :t1, 'manual', 'draft', 'local', 1, :tu1),
                       (:id2, :t2, 'manual', 'draft', 'local', 1, :tu2)
            """),
            {
                "id1": id1, "t1": "High tokens", "tu1": '{"gen": {"input": 800, "output": 200}}',
                "id2": id2, "t2": "Low tokens", "tu2": '{"gen": {"input": 60, "output": 40}}',
            },
        )
        await test_session.commit()

        try:
            response = await client.get("/api/v1/articles?sort_by=total_tokens&sort_order=desc&limit=50")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            topics = [item["topic"] for item in data["data"]]
            assert topics.index("High tokens") < topics.index("Low tokens")
        finally:
            for aid in [id1, id2]:
                await test_session.execute(text("DELETE FROM articles WHERE id = :id"), {"id": aid})
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_sort_by_total_tokens_pagination(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from sqlalchemy import text

        ids = []
        for i in range(5):
            aid = uuid4()
            tokens = 100 * (i + 1)  # 100, 200, 300, 400, 500
            await test_session.execute(
                text("""
                    INSERT INTO articles (id, topic, mode, status, source, version, token_usage)
                    VALUES (:id, :t, 'manual', 'draft', 'local', 1, :tu)
                """),
                {"id": aid, "t": f"Article number {i}", "tu": f'{{"gen": {{"input": {tokens // 2}, "output": {tokens // 2}}}}}'},
            )
            ids.append(aid)
        await test_session.commit()

        try:
            response = await client.get("/api/v1/articles?sort_by=total_tokens&sort_order=asc&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            page1_topics = [item["topic"] for item in data["data"]]
            assert len(page1_topics) == 2
            assert page1_topics == ["Article number 0", "Article number 1"]

            response = await client.get("/api/v1/articles?sort_by=total_tokens&sort_order=asc&limit=2&page=2")
            assert response.status_code == 200
            data = response.json()
            page2_topics = [item["topic"] for item in data["data"]]
            assert len(page2_topics) == 2
            assert page2_topics == ["Article number 2", "Article number 3"]

            response = await client.get("/api/v1/articles?sort_by=total_tokens&sort_order=asc&limit=2&page=3")
            assert response.status_code == 200
            data = response.json()
            page3_topics = [item["topic"] for item in data["data"]]
            assert len(page3_topics) == 1
            assert page3_topics == ["Article number 4"]
        finally:
            for aid in ids:
                await test_session.execute(text("DELETE FROM articles WHERE id = :id"), {"id": aid})
            await test_session.commit()


class TestArticleSearch:
    """GET /api/v1/articles with search param."""

    @pytest.mark.asyncio
    async def test_search_by_topic(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from sqlalchemy import text

        id1 = uuid4()
        id2 = uuid4()

        await test_session.execute(
            text("""
                INSERT INTO articles (id, topic, mode, status, source, version)
                VALUES (:id1, :t1, 'manual', 'draft', 'local', 1),
                       (:id2, :t2, 'manual', 'draft', 'local', 1)
            """),
            {"id1": id1, "t1": "RAG technology deep dive", "id2": id2, "t2": "Machine learning basics"},
        )
        await test_session.commit()

        try:
            response = await client.get("/api/v1/articles?search=rag")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            topics = [item["topic"] for item in data["data"]]
            assert "RAG technology deep dive" in topics
            assert "Machine learning basics" not in topics
        finally:
            for aid in [id1, id2]:
                await test_session.execute(text("DELETE FROM articles WHERE id = :id"), {"id": aid})
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_search_outline_title(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from sqlalchemy import text

        id1 = uuid4()
        id2 = uuid4()

        await test_session.execute(
            text("""
                INSERT INTO articles (id, topic, mode, status, source, version, outline)
                VALUES (:id1, :t1, 'manual', 'draft', 'local', 1, :o1),
                       (:id2, :t2, 'manual', 'draft', 'local', 1, :o2)
            """),
            {
                "id1": id1, "t1": "some user input topic", "o1": '{"title": "RAG技术详解：从原理到生产级应用"}',
                "id2": id2, "t2": "another topic", "o2": '{"title": "Machine Learning 101"}',
            },
        )
        await test_session.commit()

        try:
            response = await client.get("/api/v1/articles?search=rag")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            topics = [item["topic"] for item in data["data"]]
            assert "some user input topic" in topics
            assert "another topic" not in topics
        finally:
            for aid in [id1, id2]:
                await test_session.execute(text("DELETE FROM articles WHERE id = :id"), {"id": aid})
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_search_no_matches(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from sqlalchemy import text

        await test_session.execute(
            text("INSERT INTO articles (id, topic, mode, status, source, version) VALUES (:id, :t, 'manual', 'draft', 'local', 1)"),
            {"id": uuid4(), "t": "Some article about programming"},
        )
        await test_session.commit()

        response = await client.get("/api/v1/articles?search=nonexistent_keyword_xyz")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 0


class TestArticleDisplayTitleInApi:
    """displayTitle field appears in GET /api/v1/articles response."""

    @pytest.mark.asyncio
    async def test_display_title_from_outline(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from sqlalchemy import text

        aid = uuid4()
        await test_session.execute(
            text("""
                INSERT INTO articles (id, topic, mode, status, source, version, outline)
                VALUES (:id, :t, 'manual', 'draft', 'local', 1, :o)
            """),
            {"id": aid, "t": "user input topic", "o": '{"title": "WP Title From Outline"}'},
        )
        await test_session.commit()

        try:
            response = await client.get("/api/v1/articles?limit=50")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            items = [item for item in data["data"] if item["id"] == str(aid)]
            assert len(items) == 1
            assert items[0]["displayTitle"] == "WP Title From Outline"
        finally:
            await test_session.execute(text("DELETE FROM articles WHERE id = :id"), {"id": aid})
            await test_session.commit()

    @pytest.mark.asyncio
    async def test_display_title_falls_back_to_topic(self, client: AsyncClient, test_session: AsyncSession):
        from uuid import uuid4
        from sqlalchemy import text

        aid = uuid4()
        await test_session.execute(
            text("""
                INSERT INTO articles (id, topic, mode, status, source, version)
                VALUES (:id, :t, 'manual', 'draft', 'local', 1)
            """),
            {"id": aid, "t": "Fallback topic title"},
        )
        await test_session.commit()

        try:
            response = await client.get("/api/v1/articles?limit=50")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            items = [item for item in data["data"] if item["id"] == str(aid)]
            assert len(items) == 1
            assert items[0]["displayTitle"] == "Fallback topic title"
        finally:
            await test_session.execute(text("DELETE FROM articles WHERE id = :id"), {"id": aid})
            await test_session.commit()
