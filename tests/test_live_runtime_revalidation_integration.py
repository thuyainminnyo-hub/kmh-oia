import unittest

from src.active_standard_resolver import ActiveStandardResolver
from src.live_operating_console import LiveOperatingConsole
from src.live_runtime_bridge import LiveRuntimeBridge
from src.runtime_revalidation_pipeline import RuntimeRevalidationPipeline
from src.standard_control_plane import StandardControlPlane
from src.standardization_engine import OperatingStandard


class LiveRuntimeRevalidationIntegrationTests(unittest.TestCase):
    def test_live_execution_feeds_drift_into_revalidation(self):
        console = LiveOperatingConsole("2026-10-05", "Governed execution")
        command = console.add_command(
            "cmd:reval",
            objective="execute governed task",
            priority="P1",
            owner="system",
            expected_output="successful execution",
        )
        control_plane = StandardControlPlane()
        resolver = ActiveStandardResolver(control_plane.registry)
        standard = OperatingStandard(
            "std:reval:v1", "reval", "Require evidence",
            "Trace-backed execution", 1, "ACTIVE"
        )
        resolver.register(standard)
        pipeline = RuntimeRevalidationPipeline(control_plane)
        record = LiveRuntimeBridge(
            console,
            control_plane=control_plane,
            standard_resolver=resolver,
        ).execute(
            command.id,
            source_adaptation_id="reval",
            applied_rule="Skip evidence",
        )
        self.assertEqual(record.final_status, "LEARNED")
        result = pipeline.process(
            standard,
            command.id,
            applied_rule="Skip evidence",
            evidence_id=record.evidence[0].split("=", 1)[1],
            observed_effect=0.0,
            outcome_positive=False,
        )
        self.assertTrue(result.revalidated)
        self.assertEqual(
            result.control_result.revalidation.revalidation.verdict,
            "REVISE",
        )

if __name__ == "__main__":
    unittest.main()
