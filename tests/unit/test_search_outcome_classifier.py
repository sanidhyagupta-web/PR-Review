"""
Tests for the RYT-5 search outcome classifier (DEC-0004: insufficient context is its
own UI state).

Covers:
- Unit: generate_answer returns an AnswerResult on a successful LLM call
- Unit: generate_answer raises LLMUnavailable when the API key is missing
- Unit: generate_answer raises LLMUnavailable when the LLM call itself fails
- Unit: generate_answer short-circuits to an empty AnswerResult with no context chunks
- Unit: resolve_search_outcome classifies top_chunks == [] as insufficient_context
  without calling generate_answer
- Unit: resolve_search_outcome classifies chunks-present/no-citations as insufficient_context
- Unit: resolve_search_outcome classifies chunks-present/citations-present as answered
- Unit: resolve_search_outcome classifies an LLMUnavailable failure as error
"""
from __future__ import annotations

import sys
import types

import pytest

from app.config import settings
import llm.claude_client as claude_client
from llm.claude_client import (
    AnswerResult,
    LLMUnavailable,
    OUTCOME_ANSWERED,
    OUTCOME_ERROR,
    OUTCOME_INSUFFICIENT_CONTEXT,
    generate_answer,
    resolve_search_outcome,
)


@pytest.fixture
def chunk():
    return {
        "text": "Patient prescribed lisinopril 10mg daily.",
        "metadata": {
            "source_section": "Medications",
            "department": "cardiology",
            "source_file": "note.pdf",
            "source_page": 2,
        },
    }


@pytest.fixture(autouse=True)
def api_key_configured(monkeypatch):
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")


def _fake_anthropic_module(response_text=None, raise_exc=None):
    """Build a fake `anthropic` module that either returns response_text or raises raise_exc."""
    module = types.ModuleType("anthropic")

    class _Content:
        def __init__(self, text):
            self.text = text

    class _Messages:
        def create(self, **kwargs):
            if raise_exc is not None:
                raise raise_exc
            return types.SimpleNamespace(content=[_Content(response_text)])

    class _Anthropic:
        def __init__(self, api_key):
            self.api_key = api_key
            self.messages = _Messages()

    module.Anthropic = _Anthropic
    return module


# ---------------------------------------------------------------------------
# Unit: generate_answer contract (AnswerResult / LLMUnavailable)
# ---------------------------------------------------------------------------

def test_generate_answer_returns_answer_result_on_success(monkeypatch, chunk):
    fake_module = _fake_anthropic_module(response_text="Prescribed lisinopril [1].")
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    result = generate_answer("What medication?", [chunk], "doctor")

    assert isinstance(result, AnswerResult)
    assert result.cited_indices == [1]
    assert "lisinopril" in result.text


def test_generate_answer_raises_llmunavailable_when_api_key_missing(monkeypatch, chunk):
    monkeypatch.setattr(settings, "anthropic_api_key", "")

    with pytest.raises(LLMUnavailable):
        generate_answer("What medication?", [chunk], "doctor")


def test_generate_answer_raises_llmunavailable_on_client_exception(monkeypatch, chunk):
    fake_module = _fake_anthropic_module(raise_exc=RuntimeError("connection reset"))
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    with pytest.raises(LLMUnavailable):
        generate_answer("What medication?", [chunk], "doctor")


def test_generate_answer_empty_chunks_returns_result_without_calling_llm(monkeypatch):
    fake_module = _fake_anthropic_module(raise_exc=AssertionError("must not call the LLM"))
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    result = generate_answer("What medication?", [], "doctor")

    assert isinstance(result, AnswerResult)
    assert result.cited_indices == []


# ---------------------------------------------------------------------------
# Unit: resolve_search_outcome classifier
# ---------------------------------------------------------------------------

def test_resolve_outcome_insufficient_context_when_no_chunks(monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("generate_answer must not be called when top_chunks is empty")

    monkeypatch.setattr(claude_client, "generate_answer", _boom)

    outcome, result = resolve_search_outcome("query", [], "doctor")

    assert outcome == OUTCOME_INSUFFICIENT_CONTEXT
    assert result is None


def test_resolve_outcome_insufficient_context_when_no_citations(monkeypatch, chunk):
    monkeypatch.setattr(
        claude_client, "generate_answer",
        lambda query, top_chunks, role: AnswerResult(
            text="The available records do not contain enough information to answer this question.",
            cited_indices=[],
        ),
    )

    outcome, result = resolve_search_outcome("query", [chunk], "doctor")

    assert outcome == OUTCOME_INSUFFICIENT_CONTEXT
    assert result.cited_indices == []


def test_resolve_outcome_answered_when_citations_present(monkeypatch, chunk):
    monkeypatch.setattr(
        claude_client, "generate_answer",
        lambda query, top_chunks, role: AnswerResult(text="Prescribed lisinopril [1].", cited_indices=[1]),
    )

    outcome, result = resolve_search_outcome("query", [chunk], "doctor")

    assert outcome == OUTCOME_ANSWERED
    assert result.cited_indices == [1]


@pytest.mark.parametrize("failure", [
    LLMUnavailable("Anthropic API key is not configured."),
    LLMUnavailable("LLM unavailable: connection reset"),
])
def test_resolve_outcome_error_on_llm_unavailable(monkeypatch, chunk, failure):
    def _raise(query, top_chunks, role):
        raise failure

    monkeypatch.setattr(claude_client, "generate_answer", _raise)

    outcome, result = resolve_search_outcome("query", [chunk], "doctor")

    assert outcome == OUTCOME_ERROR
    assert result is None
