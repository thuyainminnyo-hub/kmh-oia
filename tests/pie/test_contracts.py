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


class PIEIntegrityRemediationTests(unittest.TestCase):
    # R-01: caller-owned collections are normalized into immutable tuples.
    def test_r01_scope_list_is_normalized_to_tuple(self):
        value = brief(scope=["one", "two"])
        self.assertEqual(value.scope, ("one", "two"))
        self.assertIsInstance(value.scope, tuple)

    def test_r01_mutating_original_scope_list_does_not_change_brief_or_hash(self):
        original = ["one"]
        value = brief(scope=original)
        original.append("tampered")
        self.assertEqual(value.scope, ("one",))
        self.assertEqual(value.content_hash, brief(scope=("one",)).content_hash)

    def test_r01_pac_requirement_ids_are_normalized_and_isolated(self):
        original = ["REQ-001"]
        value = criterion(req_ids=original)
        original.append("REQ-002")
        self.assertEqual(value.requirement_ids, ("REQ-001",))
        self.assertIsInstance(value.requirement_ids, tuple)

    def test_r01_non_goals_are_normalized_and_hash_mismatch_is_rejected(self):
        original = ["not production"]
        value = brief(non_goals=original)
        original.append("external side effects")
        self.assertEqual(value.non_goals, ("not production",))
        with self.assertRaises(ContractError):
            brief(content_hash="0" * 64)

    # R-02: an approval reference is bound once to project, version and content hash.
    def test_r02_approval_reference_cannot_be_reused_after_intervening_draft(self):
        registry = ProjectRegistry()
        registry.register(brief(status=ProjectStatus.APPROVED, approval_ref="approval-unique"))
        registry.register(brief(brief_version=2, status=ProjectStatus.DRAFT, project_name="Draft revision"))
        with self.assertRaises(ContractError):
            registry.register(brief(brief_version=3, status=ProjectStatus.APPROVED, approval_ref="approval-unique"))

    def test_r02_changed_content_cannot_reuse_old_approval_reference(self):
        registry = ProjectRegistry()
        registry.register(brief(status=ProjectStatus.APPROVED, approval_ref="approval-content"))
        changed = brief(brief_version=2, project_name="Changed content", status=ProjectStatus.APPROVED,
                        approval_ref="approval-content")
        with self.assertRaises(ContractError):
            registry.register(changed)

    def test_r02_approval_reference_cannot_be_reused_across_projects(self):
        registry = ProjectRegistry()
        registry.register(brief(status=ProjectStatus.APPROVED, approval_ref="approval-global"))
        other_project = brief(project_id="PRJ-002", status=ProjectStatus.APPROVED,
                              approval_ref="approval-global")
        with self.assertRaises(ContractError):
            registry.register(other_project)

    def test_r02_approval_binding_records_exact_project_version_and_hash(self):
        registry = ProjectRegistry()
        approved = brief(status=ProjectStatus.APPROVED, approval_ref="approval-bound")
        registry.register(approved)
        self.assertEqual(registry._approval_bindings["approval-bound"],
                         (approved.project_id, approved.brief_version, approved.content_hash))

    # R-03: malformed Python values fail deterministically with ContractError.
    def test_r03_integer_project_id_raises_contract_error(self):
        with self.assertRaises(ContractError):
            brief(project_id=123)

    def test_r03_null_requirement_id_raises_contract_error(self):
        with self.assertRaises(ContractError):
            requirement(req_id=None)

    def test_r03_boolean_brief_version_raises_contract_error(self):
        with self.assertRaises(ContractError):
            brief(brief_version=True)

    def test_r03_invalid_enum_value_raises_contract_error(self):
        with self.assertRaises(ContractError):
            brief(status="NOT_A_STATUS")

    def test_r03_invalid_nested_collection_raises_contract_error(self):
        with self.assertRaises(ContractError):
            brief(scope="not-a-collection-of-scope-items")

    def test_r03_null_status_raises_contract_error(self):
        with self.assertRaises(ContractError):
            Requirement("REQ-001", "PRJ-001", "A testable requirement", RequirementType.FUNCTIONAL,
                        RequirementPriority.P1, "brief:PRJ-001:v1", status=None)

    def test_r03_invalid_acceptance_requirement_collection_raises_contract_error(self):
        with self.assertRaises(ContractError):
            criterion(req_ids=None)


if __name__ == "__main__":
    unittest.main()
