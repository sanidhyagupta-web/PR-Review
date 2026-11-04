"""
Unit tests for the regex fallback of ingestion.ocr.ocr_quality.correct_medical_terms.

The Sapling API key is cleared on the settings object, so the fallback runs
directly and no network call is made. Inputs are isolated misspelling strings
only — no patient data.
"""
from __future__ import annotations

import logging

import pytest

from ingestion.ocr import ocr_quality
from ingestion.ocr.ocr_quality import correct_medical_terms

_COUNT_PREFIX = "Regex fallback corrected"


@pytest.fixture(autouse=True)
def no_sapling_key(monkeypatch):
    monkeypatch.setattr(ocr_quality.settings, "sapling_api_key", "")


def _run(caplog, text: str) -> tuple[str, list[logging.LogRecord]]:
    with caplog.at_level(logging.DEBUG, logger=ocr_quality.__name__):
        result = correct_medical_terms(text)
    records = [
        r for r in caplog.records
        if r.name == ocr_quality.__name__ and r.getMessage().startswith(_COUNT_PREFIX)
    ]
    return result, records


def test_regex_single_replacement_logs_count_of_one(caplog):
    result, records = _run(caplog, "History of diabetis.")
    assert result == "History of diabetes."
    assert len(records) == 1
    assert records[0].levelno == logging.DEBUG
    assert records[0].getMessage() == "Regex fallback corrected 1 term(s) in OCR text"


def test_regex_repeated_occurrences_counted_individually(caplog):
    result, records = _run(caplog, "diabetis, diabetis and Diabetis")
    assert result == "diabetes, diabetes and diabetes"
    assert len(records) == 1
    assert records[0].getMessage() == "Regex fallback corrected 3 term(s) in OCR text"


def test_regex_multiple_entries_aggregated_in_one_message(caplog):
    result, records = _run(caplog, "arrythmia and pneumona; also arrythmia")
    assert result == "arrhythmia and pneumonia; also arrhythmia"
    assert len(records) == 1
    assert records[0].getMessage() == "Regex fallback corrected 3 term(s) in OCR text"


def test_regex_entries_with_same_replacement_both_counted(caplog):
    result, records = _run(caplog, "fibrilatoin then fibrilaton")
    assert result == "fibrillation then fibrillation"
    assert len(records) == 1
    assert records[0].getMessage() == "Regex fallback corrected 2 term(s) in OCR text"


def test_regex_case_insensitive_matching_preserved(caplog):
    result, records = _run(caplog, "HYPERTENSHUN")
    assert result == "hypertension"
    assert len(records) == 1
    assert records[0].getMessage() == "Regex fallback corrected 1 term(s) in OCR text"


def test_regex_preserves_word_boundaries(caplog):
    text = "xdiabetis diabetisy pneumonaa"
    result, records = _run(caplog, text)
    assert result == text
    assert records == []


def test_regex_punctuation_is_a_word_boundary(caplog):
    result, records = _run(caplog, "(myocardail) tachycarida, bradycarida.")
    assert result == "(myocardial) tachycardia, bradycardia."
    assert len(records) == 1
    assert records[0].getMessage() == "Regex fallback corrected 3 term(s) in OCR text"


def test_regex_zero_replacements_logs_no_count(caplog):
    text = "Patient has diabetes and hypertension."
    result, records = _run(caplog, text)
    assert result == text
    assert records == []


def test_regex_empty_text_logs_no_count(caplog):
    result, records = _run(caplog, "")
    assert result == ""
    assert records == []


def test_regex_counts_reset_per_invocation(caplog):
    first, first_records = _run(caplog, "diabetis diabetis")
    caplog.clear()
    second, second_records = _run(caplog, "pneumona")
    assert first == "diabetes diabetes"
    assert second == "pneumonia"
    assert [r.getMessage() for r in first_records] == [
        "Regex fallback corrected 2 term(s) in OCR text"
    ]
    assert [r.getMessage() for r in second_records] == [
        "Regex fallback corrected 1 term(s) in OCR text"
    ]


def test_regex_count_message_does_not_contain_ocr_text(caplog):
    _, records = _run(caplog, "diabetis")
    assert len(records) == 1
    assert "diabetis" not in records[0].getMessage()
    assert "diabetes" not in records[0].getMessage()
