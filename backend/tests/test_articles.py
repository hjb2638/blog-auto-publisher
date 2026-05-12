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
    mock_article.full_html = None
    mock_article.progress = None
    mock_article.wp_post_id = None
    mock_article.wp_post_url = None
    mock_article.wp_slug = None
    mock_article.error_message = None
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
