from app.service.gemini_rate_limiter import GeminiRequestLimiter


def test_shared_limiter_spaces_consecutive_requests(tmp_path, monkeypatch):
    monkeypatch.setattr("app.service.gemini_rate_limiter.settings.assessment_documents_dir", str(tmp_path))
    monkeypatch.setattr("app.service.gemini_rate_limiter.settings.gemini_min_request_interval_seconds", 8.0)
    # Logging reads the same time module, so provide a few extra post-wait values.
    clock_values = iter((100.0, 100.0, 100.0, *((108.0,) * 10)))
    waits: list[float] = []
    monkeypatch.setattr("app.service.gemini_rate_limiter.time.time", lambda: next(clock_values))
    monkeypatch.setattr("app.service.gemini_rate_limiter.time.sleep", waits.append)

    GeminiRequestLimiter().wait_for_slot("embedding")
    GeminiRequestLimiter().wait_for_slot("reasoning")

    assert waits == [8.0]


def test_limiter_can_be_disabled_for_controlled_test_runs(tmp_path, monkeypatch):
    monkeypatch.setattr("app.service.gemini_rate_limiter.settings.assessment_documents_dir", str(tmp_path))
    monkeypatch.setattr("app.service.gemini_rate_limiter.settings.gemini_min_request_interval_seconds", 0.0)

    GeminiRequestLimiter().wait_for_slot("embedding")

    assert not (tmp_path / ".gemini-request-slot").exists()
