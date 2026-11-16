import unittest

from src.pie.contracts import (
    AcceptanceCriterion, ContractError, Environment, ProjectBrief, ProjectStatus,
    Requirement, RequirementPriority, RequirementType,
)
from src.pie.registry import ProjectRegistry
from src.pie.validation import validate_project_bundle


def brief(**changes):
    values = dict(
        project_id="PRJ-001", brief_version=1, project_name="Synthetic demo",
        objective="Validate a synthetic project brief", scope=("contract validation",),
        non_goals=("production execution", "external integrations"),
        requested_environment="production", effective_environment=Environment.LOCAL_SYNTHETIC,
        created_by="principal-ref:test", status=ProjectStatus.DRAFT,
    )
    values.update(changes)
    return ProjectBrief(**values)


def requirement(req_id="REQ-001", project_id="PRJ-001"):
    return Requirement(req_id, project_id, "A testable requirement", RequirementType.FUNCTIONAL,
                       RequirementPriority.P1, "brief:PRJ-001:v1")


def criterion(pac_id="PAC-PRJ-001-001", req_ids=("REQ-001",), project_id="PRJ-001"):
    return AcceptanceCriterion(pac_id, project_id, req_ids, "The requirement is met",
                               "critical", "automated_contract_check")


class PIEContractTests(unittest.TestCase):
    def test_brief_hash_is_stable_and_covers_effective_environment(self):
        first = brief()
        self.assertEqual(first.content_hash, brief().content_hash)
        with self.assertRaises(ContractError):
            brief(content_hash="0" * 64)

    def test_production_effective_environment_is_not_supported(self):
        with self.assertRaises(ContractError):
            brief(effective_environment="production")

    def test_invalid_project_status_is_rejected(self):
        with self.assertRaises(ContractError):
            brief(status="APPROVED")

    def test_approved_brief_requires_approval_reference(self):
        with self.assertRaises(ContractError):
            brief(status=ProjectStatus.APPROVED)

    def test_pac_namespace_is_enforced(self):
        with self.assertRaises(ContractError):
            criterion(pac_id="AC-01")

    def test_pac_project_segment_must_match_project_id(self):
        with self.assertRaises(ContractError):
            criterion(pac_id="PAC-PRJ-002-001")

    def test_valid_project_requirement_pac_chain(self):
        result = validate_project_bundle(brief(), [requirement()], [criterion()])
        self.assertTrue(result["valid"])
        self.assertEqual(result["traceability"], "PRJ->REQ->PAC")
        self.assertFalse(result["execution_performed"])

    def test_missing_requirement_reference_is_rejected(self):
        with self.assertRaises(ContractError):
            validate_project_bundle(brief(), [requirement()], [criterion(req_ids=("REQ-999",))])

    def test_uncovered_requirement_is_rejected(self):
        with self.assertRaises(ContractError):
            validate_project_bundle(brief(), [requirement(), requirement("REQ-002")], [criterion()])

    def test_duplicate_requirement_is_rejected(self):
        with self.assertRaises(ContractError):
            validate_project_bundle(brief(), [requirement(), requirement()], [criterion()])

    def test_cross_project_requirement_is_rejected(self):
        with self.assertRaises(ContractError):
            validate_project_bundle(brief(), [requirement(project_id="PRJ-002")], [criterion()])

    def test_invalid_downstream_reference_is_rejected(self):
        with self.assertRaises(ContractError):
            validate_project_bundle(brief(), [requirement()], [criterion()], test_refs={"": "EVD-1"})


class PIERegistryTests(unittest.TestCase):
    def test_registry_requires_brief_and_preserves_immutable_ids(self):
        registry = ProjectRegistry()
        with self.assertRaises(ContractError):
            registry.add_requirement(requirement())
        registry.register(brief())
        registry.add_requirement(requirement())
        with self.assertRaises(ContractError):
            registry.add_requirement(requirement())

    def test_registry_validates_complete_bundle(self):
        registry = ProjectRegistry()
        registry.register(brief())
        registry.add_requirement(requirement())
        registry.add_acceptance_criterion(criterion())
        self.assertTrue(registry.validate("PRJ-001")["valid"])

    def test_registry_retains_prior_brief_versions(self):
        registry = ProjectRegistry()
        first = brief()
        registry.register(first)
        second = brief(brief_version=2, project_name="Synthetic demo v2")
        registry.register(second)
        self.assertEqual(registry.get_brief_version("PRJ-001", 1), first)
        self.assertEqual(registry.get_brief_version("PRJ-001", 2), second)

    def test_approved_new_version_requires_distinct_approval_reference(self):
        registry = ProjectRegistry()
        registry.register(brief(status=ProjectStatus.APPROVED, approval_ref="approval-1"))
        with self.assertRaises(ContractError):
            registry.register(brief(brief_version=2, status=ProjectStatus.APPROVED, approval_ref="approval-1"))
        registry.register(brief(brief_version=2, status=ProjectStatus.APPROVED, approval_ref="approval-2"))


if __name__ == "__main__":
    unittest.main()
