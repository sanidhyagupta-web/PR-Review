"""
Unit tests for ingestion.chunking.chunk_hasher.compute_hash.

The hash is the chunk identity used for deduplication, so these tests pin the
normalisation (case, whitespace), the UTF-8 SHA-256 digest format, and the
empty-input behaviour. Expected digests are built with hashlib from explicit,
already-normalised strings rather than by reusing the module's own helpers.
"""
from __future__ import annotations

import hashlib
import re

import pytest

from ingestion.chunking.chunk_hasher import compute_hash


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_EMPTY_DIGEST = hashlib.sha256(b"").hexdigest()
_BASELINE = "hello world"


# ---------------------------------------------------------------------------
# Determinism and digest format
# ---------------------------------------------------------------------------


def test_same_text_returns_same_digest_on_repeated_calls():
    digests = {compute_hash("Patient takes Aspirin 81 mg daily.") for _ in range(5)}

    assert len(digests) == 1


@pytest.mark.parametrize(
    "text",
    ["hello world", "  Mixed CASE\ttext\n", "", "Café", "Dose: 5 mg, twice daily."],
)
def test_digest_is_64_lowercase_hex_characters(text):
    digest = compute_hash(text)

    assert re.fullmatch(r"[0-9a-f]{64}", digest) is not None


def test_digest_equals_sha256_of_normalised_utf8_text():
    digest = compute_hash("  Hello \t\n WORLD  ")

    assert digest == _sha256_hex("hello world")


# ---------------------------------------------------------------------------
# Inputs that must hash identically
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    ["HELLO WORLD", "Hello World", "hElLo wOrLd"],
    ids=["upper", "title", "alternating"],
)
def test_case_only_differences_produce_equal_hashes(text):
    assert compute_hash(text) == compute_hash(_BASELINE)


@pytest.mark.parametrize(
    "text",
    [
        "   hello world",
        "hello world   ",
        "   hello world   ",
        "\thello world",
        "hello world\n",
        "\n\t hello world \t\n",
    ],
    ids=[
        "leading-spaces",
        "trailing-spaces",
        "both-spaces",
        "leading-tab",
        "trailing-newline",
        "mixed-both-ends",
    ],
)
def test_leading_and_trailing_whitespace_produce_equal_hashes(text):
    assert compute_hash(text) == compute_hash(_BASELINE)


@pytest.mark.parametrize(
    "text",
    [
        "hello    world",
        "hello\tworld",
        "hello\t\t\tworld",
        "hello\nworld",
        "hello\r\nworld",
        "hello \n\n \t world",
    ],
    ids=[
        "many-spaces",
        "tab",
        "many-tabs",
        "newline",
        "crlf",
        "mixed-whitespace",
    ],
)
def test_inter_word_whitespace_differences_produce_equal_hashes(text):
    assert compute_hash(text) == compute_hash(_BASELINE)


# ---------------------------------------------------------------------------
# Inputs that must hash differently
# ---------------------------------------------------------------------------


def test_different_word_produces_different_hash():
    assert compute_hash("hello world") != compute_hash("hello there")


def test_different_punctuation_produces_different_hash():
    assert compute_hash("hello world") != compute_hash("hello, world")
    assert compute_hash("hello world.") != compute_hash("hello world!")


def test_removing_inter_word_whitespace_entirely_produces_different_hash():
    assert compute_hash("hello world") != compute_hash("helloworld")


# ---------------------------------------------------------------------------
# Empty and non-ASCII input
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    ["", " ", "   ", "\t", "\n", " \t\r\n "],
    ids=["empty", "space", "spaces", "tab", "newline", "mixed"],
)
def test_empty_and_whitespace_only_text_hash_to_empty_string_digest(text):
    assert compute_hash(text) == _EMPTY_DIGEST


def test_non_ascii_text_matches_digest_of_normalised_utf8_text():
    digest = compute_hash("  CAFÉ\tMenu\n")

    assert digest == hashlib.sha256("café menu".encode("utf-8")).hexdigest()


def test_non_ascii_text_is_hashed_as_utf8_not_ascii_stripped():
    assert compute_hash("Café") == _sha256_hex("café")
    assert compute_hash("Café") != compute_hash("Cafe")
