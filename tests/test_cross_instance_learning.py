import unittest
from src.cross_instance_learning import CrossInstanceLearningEngine
from src.operating_memory import OperatingMemoryRecord

class CrossInstanceLearningTests(unittest.TestCase):
    def record(self, command_id, learned, confidence=1.0):
        return OperatingMemoryRecord(command_id, "2026-01-01T00:00:00+00:00", "wanted", "did", "actual", "verified", "decision", learned, "changed", "next", confidence)

    def test_ingest_preserves_instance_identity(self):
        engine = CrossInstanceLearningEngine()
        result = engine.ingest("instance-a", [self.record("c1", "evidence-first")])
        self.assertEqual(result[0].instance_id, "instance-a")
        self.assertEqual(result[0].memory.command_id, "c1")

    def test_repeated_learning_across_instances_becomes_shared_insight(self):
        engine = CrossInstanceLearningEngine()
        records = []
        records += list(engine.ingest("instance-a", [self.record("a1", "evidence-first", .8)]))
        records += list(engine.ingest("instance-b", [self.record("b1", "evidence-first", 1.0)]))
        insights = engine.synthesize(records)
        self.assertEqual(len(insights), 1)
        self.assertEqual(insights[0].instance_count, 2)
        self.assertEqual(insights[0].observation_count, 2)
        self.assertEqual(insights[0].confidence, .9)

    def test_distinct_patterns_remain_distinct(self):
        engine = CrossInstanceLearningEngine()
        records = list(engine.ingest("a", [self.record("1", "pattern-a")])) + list(engine.ingest("b", [self.record("2", "pattern-b")]))
        self.assertEqual({x.pattern for x in engine.synthesize(records)}, {"pattern-a", "pattern-b"})

if __name__ == "__main__":
    unittest.main()
