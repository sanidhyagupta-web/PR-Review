"""
Tests for startup recovery in run.py (ENG-36).

Covers:
- recover_stuck_docs() emits one final "Recovery summary" INFO record from the
  ``run`` logger: positive format with both status counts, or the zero-result
  wording when nothing was actually re-queued
- Documents skipped for a missing redacted file are never counted
- An EXTRACTED document routed to two queues counts once
- Existing recovery log lines, queue destinations and payloads are preserved
- Query / queue failures propagate without a summary and the session closes
- main() runs recovery (and so logs the summary) before optional seeding

run.py imports the database layer, the workers and the process-local queues at
import time. Those heavy dependencies are replaced by light fakes here, only
inside the ``run_mod`` fixture, so the real recover_stuck_docs() and main()
are what get exercised.
"""
from __future__ import annotations

import importlib
import logging
import sys
import types
from types import SimpleNamespace

import pytest

POSITIVE = "Recovery summary: {total} re-queued (PII_PROCESSED: {pii}, EXTRACTED: {ext})"
NOTHING = "Recovery summary: nothing to re-queue"


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _Column:
    def in_(self, values):
        return ("status_in", list(values))


class _DocumentRegistry:
    status = _Column()


class _RecordingQueue:
    def __init__(self, name, calls):
        self.name = name
        self._calls = calls
        self.on_put = None

    def put(self, msg):
        self._calls.append((self.name, msg))
        if self.on_put is not None:
            self.on_put(msg)


class _FakeSession:
    def __init__(self, docs, state):
        self._docs = docs
        self._state = state

    def query(self, model):
        if self._state.get("query_error"):
            raise self._state["query_error"]
        self._state["queried_model"] = model
        return self

    def filter(self, predicate):
        self._state["filter"] = predicate
        return self

    def all(self):
        return list(self._docs)

    def close(self):
        self._state["closed"] = self._state.get("closed", 0) + 1

    # Any write would be a recovery-policy change: record it.
    def add(self, *a, **k):
        self._state.setdefault("writes", []).append("add")

    def commit(self):
        self._state.setdefault("writes", []).append("commit")

    def execute(self, *a, **k):
        self._state.setdefault("writes", []).append("execute")


def _module(name, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


class _Env:
    """Handle returned by the run_mod fixture."""

    def __init__(self, run, tmp_path):
        self.run = run
        self.processed = tmp_path / "processed"
        self.docs: list = []
        self.calls: list = []        # (queue name, msg) in call order
        self.state: dict = {}        # session observations
        self.queues = None
        self.seed_calls: list = []
        self.started_workers: list = []

    def add_doc(self, doc_id, status, *, redacted=True, raw_path="s3://raw/x",
                uploader_id="u1", filename=None):
        doc = SimpleNamespace(
            doc_id=doc_id,
            original_filename=filename or f"{doc_id}.pdf",
            raw_path=raw_path,
            uploader_id=uploader_id,
            status=status,
        )
        if redacted:
            path = self.processed / "redacted" / doc_id / "redacted_chunks.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("[]")
        self.docs.append(doc)
        return doc

    def redacted_path(self, doc_id):
        return str(self.processed / "redacted" / doc_id / "redacted_chunks.json")


@pytest.fixture
def run_mod(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    # Keep the import-time logging setup from touching real handlers/files.
    monkeypatch.setattr(logging, "FileHandler", lambda *a, **k: logging.NullHandler())
    monkeypatch.setattr(logging, "basicConfig", lambda *a, **k: None)

    # env is filled in below, once the module is imported.
    env = _Env(None, tmp_path)
    calls = env.calls

    env.queues = SimpleNamespace(
        extraction_queue=_RecordingQueue("extraction_queue", calls),
        embedding_queue=_RecordingQueue("embedding_queue", calls),
        keyword_queue=_RecordingQueue("keyword_queue", calls),
    )

    def sessionmaker(bind=None):
        return lambda: _FakeSession(env.docs, env.state)

    def make_worker(name):
        class _Worker:
            def start(self):
                env.started_workers.append(name)

            def stop(self):
                pass
        _Worker.__name__ = name
        return _Worker

    def seed(count):
        env.seed_calls.append(count)
        logging.getLogger("scripts.seed_mock_records").info("SEEDED %d", count)

    fakes = {
        "db.database": _module("db.database", init_db=lambda: None, engine=object()),
        "db.models": _module("db.models", DocumentRegistry=_DocumentRegistry),
        "app.config": _module("app.config", settings=SimpleNamespace(processed_dir=env.processed)),
        "sqlalchemy": _module("sqlalchemy"),
        "sqlalchemy.orm": _module("sqlalchemy.orm", sessionmaker=sessionmaker),
        "queues": _module(
            "queues",
            extraction_queue=env.queues.extraction_queue,
            embedding_queue=env.queues.embedding_queue,
            keyword_queue=env.queues.keyword_queue,
        ),
        "scripts.seed_mock_records": _module("scripts.seed_mock_records", seed=seed),
    }
    for mod_name, cls in [
        ("parser_worker", "ParserWorker"),
        ("markdown_worker", "MarkdownWorker"),
        ("chunking_worker", "ChunkingWorker"),
        ("pii_worker", "PiiWorker"),
        ("extraction_worker", "ExtractionWorker"),
        ("embedding_worker", "EmbeddingWorker"),
        ("keyword_index_worker", "KeywordIndexWorker"),
    ]:
        fakes[f"workers.{mod_name}"] = _module(f"workers.{mod_name}", **{cls: make_worker(cls)})

    for name, module in fakes.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.delitem(sys.modules, "run", raising=False)

    env.run = importlib.import_module("run")
    yield env
    sys.modules.pop("run", None)


def _run_records(caplog):
    return [r for r in caplog.records if r.name == "run"]


def _recover(env, caplog):
    caplog.set_level(logging.INFO, logger="run")
    caplog.clear()
    env.run.recover_stuck_docs()
    return _run_records(caplog)


def _summaries(records):
    return [r for r in records if r.getMessage().startswith("Recovery summary")]


# ---------------------------------------------------------------------------
# Summary line: positive results
# ---------------------------------------------------------------------------

def test_mixed_recovery_counts_and_payloads(run_mod, caplog):
    run_mod.add_doc("p1", "PII_PROCESSED")
    run_mod.add_doc("p2", "PII_PROCESSED")
    run_mod.add_doc("e1", "EXTRACTED")

    records = _recover(run_mod, caplog)

    summaries = _summaries(records)
    assert len(summaries) == 1
    assert summaries[0].levelno == logging.INFO
    assert summaries[0].name == "run"
    assert summaries[0].getMessage() == "Recovery summary: 3 re-queued (PII_PROCESSED: 2, EXTRACTED: 1)"
    assert summaries[0].getMessage() == POSITIVE.format(total=3, pii=2, ext=1)

    # Destinations and payloads are unchanged.
    def payload(doc_id, raw="s3://raw/x", uploader="u1"):
        return {
            "doc_id": doc_id,
            "original_filename": f"{doc_id}.pdf",
            "raw_s3_key": raw,
            "uploader_id": uploader,
            "redacted_path": run_mod.redacted_path(doc_id),
        }

    assert run_mod.calls == [
        ("extraction_queue", payload("p1")),
        ("extraction_queue", payload("p2")),
        ("embedding_queue", payload("e1")),
        ("keyword_queue", payload("e1")),
    ]


def test_payload_fallbacks_for_missing_raw_path_and_uploader(run_mod, caplog):
    run_mod.add_doc("p1", "PII_PROCESSED", raw_path=None, uploader_id=None)

    _recover(run_mod, caplog)

    assert run_mod.calls == [("extraction_queue", {
        "doc_id": "p1",
        "original_filename": "p1.pdf",
        "raw_s3_key": "",
        "uploader_id": "system",
        "redacted_path": run_mod.redacted_path("p1"),
    })]


def test_single_status_summary_pii_only_keeps_zero_extracted(run_mod, caplog):
    run_mod.add_doc("p1", "PII_PROCESSED")
    run_mod.add_doc("p2", "PII_PROCESSED")

    records = _recover(run_mod, caplog)

    assert [r.getMessage() for r in _summaries(records)] == [
        "Recovery summary: 2 re-queued (PII_PROCESSED: 2, EXTRACTED: 0)"
    ]


def test_single_status_summary_extracted_only_keeps_zero_pii(run_mod, caplog):
    run_mod.add_doc("e1", "EXTRACTED")
    run_mod.add_doc("e2", "EXTRACTED")
    run_mod.add_doc("e3", "EXTRACTED")

    records = _recover(run_mod, caplog)

    assert [r.getMessage() for r in _summaries(records)] == [
        "Recovery summary: 3 re-queued (PII_PROCESSED: 0, EXTRACTED: 3)"
    ]


def test_extracted_fan_out_counts_once(run_mod, caplog):
    run_mod.add_doc("e1", "EXTRACTED")

    records = _recover(run_mod, caplog)

    assert [name for name, _ in run_mod.calls] == ["embedding_queue", "keyword_queue"]
    assert [r.getMessage() for r in _summaries(records)] == [
        "Recovery summary: 1 re-queued (PII_PROCESSED: 0, EXTRACTED: 1)"
    ]


def test_counts_use_routing_branch_when_status_changes(run_mod, caplog):
    pii = run_mod.add_doc("p1", "PII_PROCESSED")
    ext = run_mod.add_doc("e1", "EXTRACTED")

    # Workers are already running: a queue consumer may advance the status
    # while recovery is still enqueueing.
    run_mod.queues.extraction_queue.on_put = lambda msg: setattr(pii, "status", "EXTRACTED")
    run_mod.queues.embedding_queue.on_put = lambda msg: setattr(ext, "status", "INDEXED")

    records = _recover(run_mod, caplog)

    assert [name for name, _ in run_mod.calls] == [
        "extraction_queue", "embedding_queue", "keyword_queue"
    ]
    assert [r.getMessage() for r in _summaries(records)] == [
        "Recovery summary: 2 re-queued (PII_PROCESSED: 1, EXTRACTED: 1)"
    ]


# ---------------------------------------------------------------------------
# Skipped documents and the zero-result line
# ---------------------------------------------------------------------------

def test_mixed_success_and_skips_preserves_logs_and_summary_order(run_mod, caplog):
    run_mod.add_doc("p1", "PII_PROCESSED")
    run_mod.add_doc("p2", "PII_PROCESSED", redacted=False)
    run_mod.add_doc("e1", "EXTRACTED", redacted=False)
    run_mod.add_doc("e2", "EXTRACTED")

    records = _recover(run_mod, caplog)

    assert [(r.levelno, r.getMessage()) for r in records] == [
        (logging.INFO, "Recovery: found 4 stuck document(s) — re-queuing"),
        (logging.INFO, "Recovery: re-queued p1 -> extraction_queue"),
        (logging.WARNING, "Recovery: skipping p2 — redacted file missing"),
        (logging.WARNING, "Recovery: skipping e1 — redacted file missing"),
        (logging.INFO, "Recovery: re-queued e2 -> embedding + keyword queues"),
        (logging.INFO, "Recovery summary: 2 re-queued (PII_PROCESSED: 1, EXTRACTED: 1)"),
    ]
    # Skipped documents were never queued.
    assert {msg["doc_id"] for _, msg in run_mod.calls} == {"p1", "e2"}


def test_all_skipped_reports_nothing(run_mod, caplog):
    run_mod.add_doc("p1", "PII_PROCESSED", redacted=False)
    run_mod.add_doc("e1", "EXTRACTED", redacted=False)

    records = _recover(run_mod, caplog)

    assert [(r.levelno, r.getMessage()) for r in records] == [
        (logging.INFO, "Recovery: found 2 stuck document(s) — re-queuing"),
        (logging.WARNING, "Recovery: skipping p1 — redacted file missing"),
        (logging.WARNING, "Recovery: skipping e1 — redacted file missing"),
        (logging.INFO, NOTHING),
    ]
    assert run_mod.calls == []


def test_no_candidates_reports_nothing(run_mod, caplog):
    records = _recover(run_mod, caplog)

    assert [(r.name, r.levelno, r.getMessage()) for r in records] == [
        ("run", logging.INFO, "Recovery summary: nothing to re-queue")
    ]
    assert run_mod.calls == []
    assert run_mod.state["closed"] == 1


# ---------------------------------------------------------------------------
# Unchanged behaviour: selection, cleanup, exceptions
# ---------------------------------------------------------------------------

def test_recovery_selects_only_recoverable_statuses(run_mod, caplog):
    run_mod.add_doc("p1", "PII_PROCESSED")

    _recover(run_mod, caplog)

    assert run_mod.state["queried_model"] is _DocumentRegistry
    assert run_mod.state["filter"] == ("status_in", ["PII_PROCESSED", "EXTRACTED"])
    assert "writes" not in run_mod.state


def test_recovery_closes_session(run_mod, caplog):
    run_mod.add_doc("p1", "PII_PROCESSED")
    run_mod.add_doc("e1", "EXTRACTED", redacted=False)

    _recover(run_mod, caplog)

    assert run_mod.state["closed"] == 1


@pytest.mark.parametrize("failure", ["query", "extraction_put", "embedding_put", "keyword_put"])
def test_recovery_exception_propagates_without_summary(run_mod, caplog, failure):
    run_mod.add_doc("p1", "PII_PROCESSED")
    run_mod.add_doc("e1", "EXTRACTED")
    boom = RuntimeError(f"{failure} failed")

    def raiser(msg):
        raise boom

    if failure == "query":
        run_mod.state["query_error"] = boom
    else:
        getattr(run_mod.queues, failure.replace("_put", "_queue")).on_put = raiser

    caplog.set_level(logging.INFO, logger="run")
    caplog.clear()
    with pytest.raises(RuntimeError, match=f"{failure} failed"):
        run_mod.run.recover_stuck_docs()

    assert _summaries(_run_records(caplog)) == []
    assert run_mod.state["closed"] == 1


# ---------------------------------------------------------------------------
# Startup sequencing
# ---------------------------------------------------------------------------

def test_main_recovery_summary_precedes_optional_seeding(run_mod, caplog, monkeypatch):
    run_mod.add_doc("p1", "PII_PROCESSED")
    monkeypatch.setattr(sys, "argv", ["run.py", "--seed", "5"])
    monkeypatch.setattr(run_mod.run.signal, "signal", lambda *a, **k: None)

    def stop_loop(_seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(run_mod.run.time, "sleep", stop_loop)
    caplog.set_level(logging.INFO)
    caplog.clear()

    with pytest.raises(SystemExit):
        run_mod.run.main()

    messages = [r.getMessage() for r in caplog.records]
    summary = "Recovery summary: 1 re-queued (PII_PROCESSED: 1, EXTRACTED: 0)"
    assert messages.count(summary) == 1
    assert messages.index(summary) < messages.index("SEEDED 5")
    assert len(run_mod.started_workers) == 7
    assert run_mod.seed_calls == [5]
