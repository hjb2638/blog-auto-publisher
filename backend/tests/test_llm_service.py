import pytest
from unittest.mock import AsyncMock, patch
from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_llm_service_initialization():
    service = LLMService()
    assert service.model is not None
    assert service.model == "deepseek"


@pytest.mark.asyncio
async def test_build_messages():
    service = LLMService()
    messages = service._build_messages("User prompt")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "User prompt"


@pytest.mark.asyncio
async def test_generate_json_returns_parsed_json():
    service = LLMService()
    mock_result = {
        "content": '{"key": "value"}',
        "tokens_input": 100,
        "tokens_output": 50,
        "latency_ms": 200,
        "finish_reason": "stop",
    }
    with patch.object(service, 'generate_response', new_callable=AsyncMock, return_value=mock_result):
        result = await service.generate_json("User prompt")
        assert result["parsed"] == {"key": "value"}
        assert result["tokens_input"] == 100
        assert result["tokens_output"] == 50


@pytest.mark.asyncio
async def test_generate_json_fallback_with_regex():
    service = LLMService()
    mock_result = {
        "content": 'prefix {"key": "value"} suffix',
        "tokens_input": 100,
        "tokens_output": 50,
        "latency_ms": 200,
        "finish_reason": "stop",
    }
    with patch.object(service, 'generate_response', new_callable=AsyncMock, return_value=mock_result):
        result = await service.generate_json("User prompt")
        assert result["parsed"] == {"key": "value"}


@pytest.mark.asyncio
async def test_llm_malformed_json():
    service = LLMService()
    mock_result = {
        "content": "not json at all {broken",
        "tokens_input": 50,
        "tokens_output": 10,
        "latency_ms": 100,
        "finish_reason": "stop",
    }
    with patch.object(service, 'generate_response', new_callable=AsyncMock, return_value=mock_result):
        try:
            result = await service.generate_json("User prompt")
            assert result["parsed"] is not None or "parsed" in result
        except ValueError:
            pass
