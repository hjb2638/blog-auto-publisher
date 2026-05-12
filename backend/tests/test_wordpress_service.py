import pytest
from unittest.mock import AsyncMock, patch
from app.services.wordpress_service import WordPressService


@pytest.mark.asyncio
async def test_wordpress_service_initialization():
    service = WordPressService()
    assert service.api_url is not None
    assert "bojinhu.xyz" in service.api_url


@pytest.mark.asyncio
async def test_check_connection():
    service = WordPressService()
    with patch.object(service, '_request', new_callable=AsyncMock, return_value=[{"id": 1}]):
        result = await service.check_connection()
        assert result is True


@pytest.mark.asyncio
async def test_check_connection_failure():
    service = WordPressService()
    with patch.object(service, '_request', new_callable=AsyncMock, side_effect=Exception("Connection refused")):
        result = await service.check_connection()
        assert result is False


@pytest.mark.asyncio
async def test_create_post_success():
    service = WordPressService()
    mock_return = {"id": 123, "link": "https://www.bojinhu.xyz/test-post", "slug": "test-post"}
    with patch.object(service, '_request', new_callable=AsyncMock, return_value=mock_return):
        result = await service.create_post(
            title="Test Post",
            content="<p>Test content</p>",
            slug="test-post",
        )
        assert result["id"] == 123
        assert result["link"] == "https://www.bojinhu.xyz/test-post"
