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
            INSERT INTO articles (id, topic, mode, status, version, wp_post_id, wp_post_url, wp_slug, source, full_html, outline)
            VALUES (:id, :topic, :mode, :status, :version, :wp_post_id, :wp_post_url, :wp_slug, :source, :full_html, :outline)
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
        },
    )
    await db.commit()
    return str(article_id)


async def _cleanup_article(db: AsyncSession, article_id: str):
    """Delete a test article by ID, ignoring if it no longer exists."""
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
