"""Tests for the KMH OIA Karmic Tail registry and conservative evaluator."""
import unittest

from src.karmic_tail_registry import (
    RegistryValidationError,
    evaluate_pattern,
    get_card,
    load_registry,
    validate_registry,
)


class KarmicTailRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()

    def test_registry_contains_all_22_unique_cards(self):
        cards = self.registry["archetypes"]
        self.assertEqual(len(cards), 22)
        self.assertEqual({card["id"] for card in cards}, set(range(1, 23)))

    def test_each_card_has_required_reflection_and_qa_fields(self):
        for card in self.registry["archetypes"]:
            with self.subTest(card=card["name"]):
                self.assertTrue(card["reflection_question"].strip())
                self.assertTrue(card["suggested_action"].strip())
                self.assertTrue(card["qa_rules"])

    def test_duplicate_ids_are_rejected(self):
        broken = dict(self.registry)
        broken["archetypes"] = list(self.registry["archetypes"])
        broken["archetypes"][1] = dict(broken["archetypes"][0])
        with self.assertRaises(RegistryValidationError):
            validate_registry(broken)

    def test_missing_card_is_rejected(self):
        broken = dict(self.registry)
        broken["archetypes"] = self.registry["archetypes"][:-1]
        with self.assertRaises(RegistryValidationError):
            validate_registry(broken)

    def test_missing_safety_policy_is_rejected(self):
        broken = dict(self.registry)
        broken["output_policy"] = {"require_uncertainty_language": True}
        with self.assertRaises(RegistryValidationError):
            validate_registry(broken)

    def test_unsure_remains_a_hypothesis(self):
        result = evaluate_pattern(get_card(18, self.registry), "unsure")
        self.assertEqual(result["status"], "HYPOTHESIS")

    def test_user_can_reject_a_pattern(self):
        result = evaluate_pattern(get_card(9, self.registry), "not_applicable")
        self.assertEqual(result["status"], "NOT_CONFIRMED")

    def test_confirmation_does_not_claim_the_card_proves_the_pattern(self):
        result = evaluate_pattern(get_card(1, self.registry), "confirmed")
        self.assertEqual(result["status"], "USER_CONFIRMED")
        self.assertIn("without treating the card as proof", result["next_action"])

    def test_invalid_confirmation_is_rejected(self):
        result = evaluate_pattern(get_card(1, self.registry), "probably")
        self.assertEqual(result["status"], "REJECTED")

    def test_unknown_card_id_raises_key_error(self):
        with self.assertRaises(KeyError):
            get_card(23, self.registry)

    def test_boolean_card_id_is_rejected(self):
        # bool is a subclass of int in Python; True must not silently select card 1.
        with self.assertRaises(KeyError):
            get_card(True, self.registry)

    def test_non_integer_card_id_is_rejected(self):
        with self.assertRaises(KeyError):
            get_card("1", self.registry)


if __name__ == "__main__":
    unittest.main()
