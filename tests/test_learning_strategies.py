import unittest

from src.learning_strategies import (
    FeedbackTiming, RevisionPlan, Strategy, build_revision_plan,
    get_strategy_guidance, select_feedback_timing,
)


class TestLearningStrategies(unittest.TestCase):
    def test_all_strategies_have_guidance(self):
        for strategy in Strategy:
            with self.subTest(strategy=strategy):
                guidance = get_strategy_guidance(strategy)
                self.assertEqual(guidance.strategy, strategy)
                self.assertTrue(guidance.boundary_condition)

    def test_unknown_strategy_rejected(self):
        with self.assertRaises(TypeError):
            get_strategy_guidance("retrieval")

    def test_revision_plan_accepts_educator_authored_intervals(self):
        plan = build_revision_plan((1, 3, 7, 14))
        self.assertEqual(plan.intervals_days, (1, 3, 7, 14))

    def test_revision_plan_requires_intervals(self):
        with self.assertRaises(ValueError):
            RevisionPlan(())

    def test_revision_plan_rejects_zero_negative_and_boolean(self):
        for intervals in ((0,), (-1,), (True,)):
            with self.subTest(intervals=intervals):
                with self.assertRaises(ValueError):
                    RevisionPlan(intervals)

    def test_revision_plan_requires_unique_ascending_intervals(self):
        for intervals in ((1, 1, 3), (3, 1), (1, 3, 2)):
            with self.subTest(intervals=intervals):
                with self.assertRaises(ValueError):
                    RevisionPlan(intervals)

    def test_feedback_policy_is_explicit_not_inferred(self):
        for timing in FeedbackTiming:
            self.assertIs(select_feedback_timing(timing), timing)

    def test_feedback_policy_rejects_unknown_value(self):
        with self.assertRaises(TypeError):
            select_feedback_timing("always_delayed")


if __name__ == "__main__":
    unittest.main()
