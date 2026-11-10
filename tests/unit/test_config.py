"""
Unit tests for the ingestion defaults on app.config.Settings.

The values come from the files attached to ENG-40. These tests only check the
stored defaults and that the existing retry/queue consumers still read the
existing fields; no worker threads, AWS, database or models are involved.
"""
from __future__ import annotations

import pytest

from app.config import Settings, settings
from queues.queue_client import QueueClient
from workers.base_worker import BaseWorker


_LOG_TEMPLATE = "ingest: skipped {count} rows with no patient id"

# (field, expected value, expected exact type)
_INGESTION_DEFAULTS = [
    ("max_retries", 7, int),
    ("queue_max_size", 500, int),
    ("max_workers", 12, int),
    ("timeout_seconds", 45, int),
    ("batch_size", 250, int),
    ("skipped_rows_log_template", _LOG_TEMPLATE, str),
    ("strict_ingest", True, bool),
]


@pytest.fixture(params=["Settings()", "shared settings"])
def config(request):
    return Settings() if request.param == "Settings()" else settings


@pytest.mark.parametrize("field_name, expected, expected_type", _INGESTION_DEFAULTS)
def test_ingestion_defaults(config, field_name, expected, expected_type):
    value = getattr(config, field_name)
    # Exact type check so that True can never satisfy an int assertion.
    assert type(value) is expected_type
    assert value == expected


def test_log_template_is_stored_unformatted():
    template = Settings().skipped_rows_log_template
    assert template == _LOG_TEMPLATE
    assert "{count}" in template
    assert template.format(count=3) == "ingest: skipped 3 rows with no patient id"


def test_strict_ingest_is_boolean_true():
    assert Settings().strict_ingest is True


def test_existing_processing_defaults(config):
    assert config.worker_poll_timeout == 1.0
    assert type(config.worker_poll_timeout) is float
    assert config.embedding_batch_size == 32
    # New fields are separate from the existing runtime controls.
    assert config.timeout_seconds != config.worker_poll_timeout
    assert config.batch_size != config.embedding_batch_size


def test_queue_defaults():
    client = QueueClient("test_queue")
    assert client._q.maxsize == 500
    assert client._q.maxsize == settings.queue_max_size


class _FakeQueue:
    """Stand-in input queue: replays re-enqueued messages, then stops the worker."""

    def __init__(self):
        self.pending: list[dict] = []
        self.dlq: list[dict] = []
        self.get_timeouts: list[float] = []
        self.task_done_calls = 0
        self.worker: BaseWorker | None = None

    def get(self, timeout=None):
        self.get_timeouts.append(timeout)
        if self.pending:
            return self.pending.pop(0)
        self.worker._stop_event.set()
        return None

    def put(self, message):
        self.pending.append(message)

    def send_to_dlq(self, message, reason):
        self.dlq.append({"message": message, "reason": reason})

    def task_done(self):
        self.task_done_calls += 1


class _FailingWorker(BaseWorker):
    def __init__(self, input_queue):
        super().__init__("failing", input_queue)
        self.attempts = 0

    def process(self, message):
        self.attempts += 1
        raise RuntimeError("boom")


def test_worker_uses_retry_default():
    fake = _FakeQueue()
    worker = _FailingWorker(fake)
    fake.worker = worker
    message = {"doc_id": "doc-1"}
    fake.pending.append(message)

    worker.run()

    # retry_count 0..6 are re-enqueued; the attempt at retry_count 7 goes to the DLQ.
    assert worker.attempts == 8
    assert message["retry_count"] == 7
    assert len(fake.dlq) == 1
    assert fake.dlq[0]["message"] is message
    assert fake.dlq[0]["reason"] == "boom"
    assert fake.pending == []
    assert fake.task_done_calls == 8
    # The worker still polls with worker_poll_timeout, not timeout_seconds.
    assert set(fake.get_timeouts) == {1.0}
