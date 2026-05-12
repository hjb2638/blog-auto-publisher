import pytest
from app.services.article_service import validate_transition, VALID_TRANSITIONS


def test_valid_outline_generating_to_ready():
    assert validate_transition("outline_generating", "outline_ready") is True


def test_valid_content_generating_to_ready():
    assert validate_transition("content_generating", "content_ready") is True


def test_valid_publishing_to_published():
    assert validate_transition("publishing", "published") is True


def test_invalid_transition_draft_to_published():
    assert validate_transition("draft", "published") is False


def test_invalid_transition_published_to_draft():
    assert validate_transition("published", "draft") is False


def test_all_generating_to_failed():
    for state in ["outline_generating", "content_generating", "image_searching", "publishing"]:
        assert validate_transition(state, "failed") is True, f"{state} -> failed should be valid"


def test_non_generating_to_failed_invalid():
    assert validate_transition("draft", "failed") is False
    assert validate_transition("outline_ready", "failed") is False


def test_any_to_cancelled():
    cancellable = ["draft", "outline_ready", "outline_approved", "content_ready",
                   "content_approved", "images_ready", "final_approved"]
    for state in cancellable:
        assert validate_transition(state, "cancelled") is True, f"{state} -> cancelled should be valid"


def test_terminal_published_no_transitions():
    assert validate_transition("published", "draft") is False
    assert validate_transition("published", "cancelled") is False


def test_validate_transition_unknown_state():
    assert validate_transition("nonexistent", "draft") is False


def test_transition_count():
    transitions = 0
    for src in VALID_TRANSITIONS:
        transitions += len(VALID_TRANSITIONS[src])
    assert transitions >= 20
