"""Generate SHA-256 evidence for the exact MIDI byte fixtures exercised by golden tests."""
import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_PATH = ROOT / "tests" / "test_midi_parser_golden.py"
MANIFEST_PATH = ROOT / "tests" / "fixtures" / "midi_golden_manifest.json"


def load_test_module():
    spec = importlib.util.spec_from_file_location(
        "kmh_midi_golden_tests_for_evidence", TEST_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_case_bytes(module, method_name):
    from src.music_intelligence import ingest

    test_class = (
        module.TestMIDIGoldenValidFixtures
        if method_name.startswith("test_g")
        else module.TestMIDIGoldenInvalidFixtures
    )
    captured = []
    original_test_parser = module.parse_midi
    original_ingest_parser = ingest.parse_midi

    def capture(parser):
        def wrapped(data, *args, **kwargs):
            if isinstance(data, (bytes, bytearray)):
                captured.append(bytes(data))
            return parser(data, *args, **kwargs)
        return wrapped

    case = test_class(method_name)
    result = unittest.TestResult()
    with patch.object(module, "parse_midi", capture(original_test_parser)), patch.object(
        ingest, "parse_midi", capture(original_ingest_parser)
    ):
        unittest.TestSuite([case]).run(result)

    if result.errors or result.failures or not result.wasSuccessful():
        details = "\n".join(item[1] for item in result.errors + result.failures)
        raise RuntimeError(f"{method_name} did not pass while collecting fixtures:\n{details}")
    if not captured:
        raise RuntimeError(f"{method_name} did not submit any fixture bytes to the parser")
    return [hashlib.sha256(raw).hexdigest() for raw in captured]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="midi-fixture-evidence.json")
    parser.add_argument("--commit-sha", default=os.getenv("EVIDENCE_COMMIT_SHA", os.getenv("GITHUB_SHA", "")))
    parser.add_argument("--bootstrap", action="store_true",
                        help="emit digests before the expected hashes are committed")
    args = parser.parse_args()

    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest = json.loads(manifest_bytes)
    names = manifest["valid_cases"] + manifest["invalid_cases"]
    module = load_test_module()
    methods = {
        name: next(
            (candidate for candidate in dir(
                module.TestMIDIGoldenValidFixtures if name.startswith("G") else
                module.TestMIDIGoldenInvalidFixtures
            ) if candidate.startswith("test_" + name.split("_", 1)[0].lower() + "_")),
            None,
        )
        for name in names
    }
    missing = [name for name, method in methods.items() if method is None]
    if missing:
        raise RuntimeError("No matching test methods for manifest cases: " + ", ".join(missing))

    fixtures = {
        name: collect_case_bytes(module, method)
        for name, method in methods.items()
    }
    expected = manifest.get("fixture_sha256")
    if not args.bootstrap:
        if not isinstance(expected, dict):
            raise RuntimeError("Manifest fixture_sha256 mapping is missing")
        if expected != fixtures:
            mismatches = [
                name for name in fixtures
                if expected.get(name) != fixtures[name]
            ]
            raise RuntimeError("Fixture SHA-256 mismatch: " + ", ".join(mismatches))
        if set(expected) != set(fixtures):
            raise RuntimeError("Manifest fixture_sha256 keys do not match the case inventory")

    run_id = os.getenv("GITHUB_RUN_ID", "")
    server = os.getenv("GITHUB_SERVER_URL", "https://github.com")
    repository = os.getenv("GITHUB_REPOSITORY", "thuyainminnyo-hub/kmh-oia")
    evidence = {
        "schema": "kmh.midi-fixture-evidence.v1",
        "fixture_set": manifest["fixture_set"],
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "repository": repository,
        "commit_sha": args.commit_sha,
        "workflow_run_id": run_id,
        "workflow_run_url": f"{server}/{repository}/actions/runs/{run_id}" if run_id else "",
        "fixture_case_count": len(fixtures),
        "fixture_instance_count": sum(len(items) for items in fixtures.values()),
        "fixtures": [
            {"case_id": name, "fixture_count": len(digests), "sha256": digests}
            for name, digests in fixtures.items()
        ],
        "manifest_hash_verification": "BOOTSTRAP_PENDING" if args.bootstrap else "PASS",
    }
    output = pathlib.Path(args.output)
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    if args.bootstrap:
        print("BOOTSTRAP MODE: copy fixture SHA-256 arrays into the committed manifest, then remove --bootstrap.")
    else:
        print("MIDI FIXTURE SHA-256 MANIFEST VERIFICATION: PASS")


if __name__ == "__main__":
    main()
