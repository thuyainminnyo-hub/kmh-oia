"""Format-agnostic, evidence-preserving BagIt intake prototype (Gate A).

This worker treats the source as opaque bytes. It never invokes the MIDI parser.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import bagit

SCHEMA = "kmh.preservation-intake-receipt.v1"
OBJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
CHUNK_SIZE = 1024 * 1024


class IntakeError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    length = 0
    with path.open("rb") as stream:
        while True:
            block = stream.read(CHUNK_SIZE)
            if not block:
                break
            digest.update(block)
            length += len(block)
    return digest.hexdigest(), length


def _capture_source(source: Path, destination: Path) -> tuple[str, int]:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(source, flags)
    except OSError as exc:
        raise IntakeError("SOURCE_OPEN_FAILED", str(exc)) from exc

    digest = hashlib.sha256()
    length = 0
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise IntakeError("SOURCE_NOT_REGULAR_FILE", "Source must be a regular file")
        with os.fdopen(fd, "rb", closefd=False) as reader, destination.open("xb") as writer:
            while True:
                block = reader.read(CHUNK_SIZE)
                if not block:
                    break
                writer.write(block)
                digest.update(block)
                length += len(block)
            writer.flush()
            os.fsync(writer.fileno())
        after = os.fstat(fd)
        identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if identity_before != identity_after or length != after.st_size:
            raise IntakeError("SOURCE_CHANGED_DURING_CAPTURE", "Source metadata changed during capture")
    finally:
        os.close(fd)
    return digest.hexdigest(), length


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def ingest(source: str | Path, object_id: str, workspace: str | Path) -> dict:
    if not OBJECT_ID_RE.fullmatch(object_id):
        raise IntakeError("INVALID_OBJECT_ID", "Object ID must be 1-64 safe ASCII letters, digits, '_' or '-'")
    source_path = Path(source)
    workspace_path = Path(workspace).resolve()
    if source_path.is_symlink():
        raise IntakeError("SOURCE_SYMLINK", "Symlink sources are not accepted")
    if not source_path.exists():
        raise IntakeError("SOURCE_NOT_FOUND", "Source file does not exist")
    if not workspace_path.is_dir():
        raise IntakeError("WORKSPACE_NOT_FOUND", "Workspace must already exist")

    accepted_root = workspace_path / "accepted"
    quarantine_root = workspace_path / "quarantine"
    reports_root = workspace_path / "reports"
    accepted_root.mkdir(exist_ok=True)
    quarantine_root.mkdir(exist_ok=True)
    reports_root.mkdir(exist_ok=True)
    final_path = accepted_root / object_id
    if final_path.exists():
        raise IntakeError("DUPLICATE_OBJECT_ID", "Object ID already exists; no overwrite performed")

    run_id = str(uuid.uuid4())
    started = datetime.now(timezone.utc).isoformat()
    staging_root = workspace_path / "staging"
    staging_root.mkdir(exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix=f"{object_id}-{run_id}-", dir=staging_root))
    receipt = {
        "schema": SCHEMA,
        "run_id": run_id,
        "object_id": object_id,
        "source_name": source_path.name,
        "started_at_utc": started,
        "worker_version": "0.1.0",
        "source_commit": os.getenv("EVIDENCE_COMMIT_SHA", os.getenv("GITHUB_SHA", "")),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "rights_status": "unknown",
        "result": "rejected",
    }
    try:
        source_sha, source_length = _capture_source(source_path, run_dir / "source" / "original.mid")
        staged_sha, staged_length = sha256_file(run_dir / "source" / "original.mid")
        receipt.update({
            "source_byte_length": source_length,
            "source_sha256": source_sha,
            "staged_byte_length": staged_length,
            "staged_sha256": staged_sha,
        })
        if (source_sha, source_length) != (staged_sha, staged_length):
            raise IntakeError("STAGED_COPY_MISMATCH", "Staged bytes differ from captured source stream")

        bag = bagit.make_bag(
            str(run_dir),
            bag_info={"External-Identifier": object_id, "Source-File-Name": source_path.name},
            checksums=["sha256"],
        )
        bag.validate()
        payload = run_dir / "data" / "source" / "original.mid"
        payload_sha, payload_length = sha256_file(payload)
        if (payload_sha, payload_length) != (source_sha, source_length):
            raise IntakeError("BAG_PAYLOAD_MISMATCH", "BagIt payload differs from captured source")

        receipt.update({
            "bagit_version": "1.0",
            "manifest_algorithms": ["sha256"],
            "validation_tool": "bagit-python",
            "validation_tool_version": getattr(bagit, "VERSION", "unknown"),
            "validation_status": "valid",
            "result": "accepted",
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        _write_json(run_dir / "intake-receipt.json", receipt)
        if final_path.exists():
            raise IntakeError("DUPLICATE_OBJECT_ID", "Object ID appeared during ingest; no overwrite performed")
        os.replace(run_dir, final_path)
        receipt["accepted_path"] = str(final_path.relative_to(workspace_path))
        _write_json(reports_root / f"{object_id}-{run_id}.json", receipt)
        return receipt
    except Exception as exc:
        if isinstance(exc, IntakeError):
            code = exc.code
        elif isinstance(exc, bagit.BagValidationError):
            code = "BAGIT_VALIDATION_FAILED"
        else:
            code = "INGEST_FAILED"
        receipt.update({
            "result": "quarantined",
            "error_code": code,
            "diagnostics": str(exc),
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        if run_dir.exists():
            quarantine_path = quarantine_root / f"{object_id}-{run_id}"
            os.replace(run_dir, quarantine_path)
            receipt["quarantine_path"] = str(quarantine_path.relative_to(workspace_path))
        _write_json(reports_root / f"{object_id}-{run_id}.json", receipt)
        raise IntakeError(code, str(exc)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--object-id", required=True)
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args()
    try:
        result = ingest(args.source, args.object_id, args.workspace)
    except IntakeError as exc:
        print(json.dumps({"result": "quarantined", "error_code": exc.code, "message": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
