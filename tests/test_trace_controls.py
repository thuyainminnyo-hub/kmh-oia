import unittest

from src.trace import (
    ExecutionContext,
    InMemoryTracer,
    TraceEvent,
    TraceRedactor,
)


def event(context, **kwargs):
    metadata = context.as_metadata()
    metadata.update(kwargs.pop("metadata", {}))
    return TraceEvent(
        stage=kwargs.pop("stage", "model.admission"),
        status=kwargs.pop("status", "ok"),
        metadata=metadata,
        error_category=kwargs.pop("error_category", None),
        duration_ms=kwargs.pop("duration_ms", None),
    )


class TraceRedactorTests(unittest.TestCase):
    def test_sensitive_metadata_keys_are_redacted(self):
        safe = TraceRedactor().redact({
            "api_key": "secret-value",
            "Authorization": "Bearer abc123",
            "ordinary": "safe",
        })
        self.assertEqual(safe["api_key"], "[REDACTED]")
        self.assertEqual(safe["Authorization"], "[REDACTED]")
        self.assertEqual(safe["ordinary"], "safe")

    def test_secret_patterns_and_email_are_redacted(self):
        safe = TraceRedactor().redact({
            "message": "Bearer abc.def token and contact alice@example.com",
            "provider_error": "api_key=supersecret",
        })
        self.assertNotIn("alice@example.com", safe["message"])
        self.assertNotIn("Bearer abc.def", safe["message"])
        self.assertNotIn("supersecret", safe["provider_error"])

    def test_metadata_size_and_types_are_bounded(self):
        with self.assertRaisesRegex(ValueError, "64 fields"):
            TraceRedactor().redact({str(i): "x" for i in range(65)})
        with self.assertRaisesRegex(ValueError, "must be strings"):
            TraceRedactor().redact({"bad": 123})
        with self.assertRaisesRegex(ValueError, "size limit"):
            TraceRedactor().redact({"large": "x" * 2_001})


class InMemoryTracerTests(unittest.TestCase):
    def setUp(self):
        self.context = ExecutionContext.create("session-1")
        self.tracer = InMemoryTracer()

    def test_context_ids_are_carried_through_events(self):
        self.tracer.emit(event(self.context, metadata={"operation": "test"}))
        self.tracer.validate_integrity()
        self.assertEqual(
            self.tracer.events[0].metadata["trace_id"],
            self.context.trace_id,
        )

    def test_sensitive_values_are_redacted_before_retention(self):
        self.tracer.emit(event(
            self.context,
            metadata={
                "api_key": "do-not-store",
                "message": "contact user@example.com",
            },
        ))
        stored = self.tracer.events[0].metadata
        self.assertEqual(stored["api_key"], "[REDACTED]")
        self.assertNotIn("user@example.com", stored["message"])

    def test_missing_context_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing required context"):
            self.tracer.emit(TraceEvent("stage", "ok", {"request_id": "r1"}))

    def test_context_drift_is_detected(self):
        first = event(self.context)
        second_context = ExecutionContext.create("session-2")
        self.tracer.emit(first)
        self.tracer.emit(event(second_context))
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            self.tracer.validate_integrity()

    def test_invalid_terminal_status_is_rejected(self):
        self.tracer.emit(event(self.context, status="running"))
        with self.assertRaisesRegex(ValueError, "final status"):
            self.tracer.validate_integrity()

    def test_empty_trace_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least one"):
            self.tracer.validate_integrity()

    def test_invalid_duration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duration_ms"):
            self.tracer.emit(event(self.context, duration_ms=-1))

    def test_error_category_and_duration_are_retained(self):
        self.tracer.emit(event(
            self.context, status="error",
            error_category="provider_timeout", duration_ms=120,
        ))
        stored = self.tracer.events[0]
        self.assertEqual(stored.error_category, "provider_timeout")
        self.assertEqual(stored.duration_ms, 120)
        self.tracer.validate_integrity()


if __name__ == "__main__":
    unittest.main()
