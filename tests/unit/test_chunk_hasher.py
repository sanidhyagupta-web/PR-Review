"""
Unit tests for ingestion.chunking.chunk_hasher.compute_hash.

Protects the current contract against silent regressions: compute_hash
collapses whitespace runs to a single space, trims leading/trailing
whitespace, lower-cases the result, UTF-8 encodes it, and returns the
SHA-256 hexadecimal digest. Because chunk_registry.chunk_hash is the sole
deduplication mechanism (see workers/chunking_worker.py), any change to
this normalization silently changes which chunks are treated as
duplicates.

This file does not modify ingestion/chunking/chunk_hasher.py and imports
nothing beyond the standard library, pytest, and the module under test.
"""
from __future__ import annotations

import hashlib

import pytest

from ingestion.chunking.chunk_hasher import compute_hash


# ── determinism and output shape ────────────────────────────────────────────

def test_same_text_hashed_repeatedly_returns_same_digest():
    """Repeated calls with the same text return the same digest."""
    text = "Patient presents with a mild headache."
    assert compute_hash(text) == compute_hash(text)


def test_digest_is_64_lowercase_hex_characters():
    """The digest is exactly 64 lower-case hexadecimal characters."""
    digest = compute_hash("Some representative chunk text.")
    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(c in "0123456789abcdef" for c in digest)


def test_digest_matches_explicit_normalized_sha256():
    """The digest equals the SHA-256 of the normalized text encoded as UTF-8."""
    text = "  Mixed   CASE\tand\nWhitespace  "
    normalized = "mixed case and whitespace"
    expected = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    assert compute_hash(text) == expected


# ── normalization equivalence: case ─────────────────────────────────────────

def test_case_only_difference_hashes_equal():
    """Texts differing only in letter case produce equal hashes."""
    assert compute_hash("Chest Pain") == compute_hash("chest pain")


# ── normalization equivalence: leading/trailing whitespace ─────────────────

def test_leading_and_trailing_whitespace_hashes_equal():
    """Texts differing only in leading or trailing whitespace produce equal hashes."""
    assert compute_hash("chest pain") == compute_hash("   chest pain   ")


# ── normalization equivalence: internal whitespace runs/kinds ──────────────

@pytest.mark.parametrize(
    "variant",
    [
        "chest  pain",
        "chest\tpain",
        "chest\npain",
        "chest \t\n pain",
        "chest     pain",
    ],
)
def test_internal_whitespace_variants_hash_equal(variant):
    """Different amounts or kinds of whitespace between words produce equal hashes."""
    assert compute_hash(variant) == compute_hash("chest pain")


def test_non_breaking_space_between_words_hashes_equal_to_normal_space():
    """A non-breaking space between words normalizes to a normal space."""
    assert compute_hash("chest\u00a0pain") == compute_hash("chest pain")


# ── distinction: meaningful content changes ─────────────────────────────────

def test_different_word_hashes_differ():
    """Texts differing in a word produce different hashes."""
    assert compute_hash("chest pain") != compute_hash("chest ache")


def test_different_punctuation_hashes_differ():
    """Texts differing in punctuation produce different hashes."""
    assert compute_hash("chest pain.") != compute_hash("chest pain!")


# ── edge cases: empty and whitespace-only input ─────────────────────────────

def test_empty_string_hashes_to_digest_of_empty_bytes():
    """An empty string hashes to the SHA-256 digest of empty bytes."""
    expected = hashlib.sha256(b"").hexdigest()
    assert compute_hash("") == expected


def test_whitespace_only_string_hashes_to_digest_of_empty_bytes():
    """A whitespace-only string hashes to the SHA-256 digest of empty bytes."""
    expected = hashlib.sha256(b"").hexdigest()
    assert compute_hash("   \t\n  ") == expected


def test_tab_only_string_hashes_to_digest_of_empty_bytes():
    """A tab-only string hashes to the SHA-256 digest of empty bytes."""
    expected = hashlib.sha256(b"").hexdigest()
    assert compute_hash("\t\t") == expected


# ── edge case: non-ASCII / UTF-8 input ──────────────────────────────────────

def test_non_ascii_input_hashes_successfully():
    """Non-ASCII text hashes successfully to the SHA-256 of its normalized UTF-8 bytes."""
    expected = hashlib.sha256("café".encode("utf-8")).hexdigest()
    assert compute_hash("Café") == expected
