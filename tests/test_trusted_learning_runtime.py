"""Composition tests for the explicit trusted learning runtime factory."""
from pathlib import Path

from src.live_operating_console import LiveOperatingConsole
from src.trusted_learning_runtime import TrustedLearningRuntimeConfig, build_trusted_learning_runtime


class StubAdapter:
    provider_name = "test-provider"
    def fetch_receipt(self, source_record_id, execution_id):
        return None
    def verify_receipt(self, receipt):
        return False
    def match_execution(self, receipt, execution_id):
        return False


class StubClassifier:
    def classify(self, decision, execution, receipt):
        raise AssertionError("not called by a composition test")


def test_factory_shares_memory_verifier_and_durable_replay_store(tmp_path):
    config = TrustedLearningRuntimeConfig(
        memory_path=str(tmp_path / "memory.json"),
        proposal_sqlite_path=str(tmp_path / "proposals.sqlite3"),
        replay_sqlite_path=str(tmp_path / "replay.sqlite3"),
        allowed_source_providers=("test-provider",),
    )
    built = build_trusted_learning_runtime(
        console=LiveOperatingConsole(),
        config=config,
        trusted_source_adapter=StubAdapter(),
        classifier=StubClassifier(),
    )
    assert built.bridge.memory is built.memory
    assert built.learning_service._memory is built.memory
    assert built.learning_service._receipt_verifier is built.bridge.trusted_source_verifier
    assert built.bridge.trusted_source_verifier.replay_store is built.replay_store
    assert built.replay_store.health_check()


def test_factory_rejects_unallowlisted_provider(tmp_path):
    config = TrustedLearningRuntimeConfig(
        memory_path=str(tmp_path / "memory.json"),
        proposal_sqlite_path=str(tmp_path / "proposals.sqlite3"),
        replay_sqlite_path=str(tmp_path / "replay.sqlite3"),
        allowed_source_providers=("other-provider",),
    )
    try:
        build_trusted_learning_runtime(
            console=LiveOperatingConsole(), config=config,
            trusted_source_adapter=StubAdapter(), classifier=StubClassifier(),
        )
    except ValueError as error:
        assert "not explicitly allowlisted" in str(error)
    else:
        raise AssertionError("unallowlisted provider must be rejected")


def test_factory_rejects_duplicate_resolved_paths(tmp_path):
    config = TrustedLearningRuntimeConfig(
        memory_path=str(tmp_path / "memory.json"),
        proposal_sqlite_path=str(tmp_path / "." / "memory.json"),
        replay_sqlite_path=str(tmp_path / "replay.sqlite3"),
        allowed_source_providers=("test-provider",),
    )
    try:
        config.validate()
    except ValueError as error:
        assert "distinct files" in str(error)
    else:
        raise AssertionError("path aliases must be rejected")
