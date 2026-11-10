"""Independent checkpoint witness for a transparency-log prototype.

This module pins signed tree heads in a separate SQLite trust domain. It does
not implement RFC 9162 Merkle proof algorithms; callers must supply a verifier
adapter for RFC 9162 consistency proofs before a checkpoint can advance.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from scripts.preservation_ingest import IntakeError, _parse_aware_time

CHECKPOINT_SCHEMA = "kmh.transparency-checkpoint.v1"
WITNESS_RECEIPT_SCHEMA = "kmh.audit-witness-receipt.v1"
GENESIS_HASH = "0" * 64


def _canonical(value: object) -> bytes:
    try:
        return rfc8785.dumps(value)
    except Exception as exc:
        raise IntakeError("INVALID_TRANSPARENCY_OBJECT", "Object cannot be canonicalized") from exc


def _raw_public_key(key: Ed25519PublicKey) -> bytes:
    return key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def create_signed_checkpoint(
    *, log_id: str, tree_size: int, root_hash: str, timestamp: str,
    log_signing_key_id: str, log_private_key: Ed25519PrivateKey,
) -> dict:
    if not isinstance(log_id, str) or not log_id.strip():
        raise IntakeError("INVALID_LOG_ID", "Log ID is required")
    if not isinstance(log_signing_key_id, str) or not log_signing_key_id.strip():
        raise IntakeError("INVALID_LOG_SIGNING_KEY_ID", "Log signing key ID is required")
    if not isinstance(tree_size, int) or isinstance(tree_size, bool) or tree_size < 0:
        raise IntakeError("INVALID_TREE_SIZE", "Tree size must be a non-negative integer")
    if not isinstance(root_hash, str) or len(root_hash) != 64:
        raise IntakeError("INVALID_TREE_ROOT", "Tree root must be a 32-byte SHA-256 hex digest")
    try:
        bytes.fromhex(root_hash)
    except ValueError as exc:
        raise IntakeError("INVALID_TREE_ROOT", "Tree root must be hexadecimal") from exc
    instant = _parse_aware_time(timestamp).astimezone(timezone.utc).isoformat()
    payload = {
        "schema": CHECKPOINT_SCHEMA,
        "log_id": log_id,
        "tree_size": tree_size,
        "root_hash": root_hash.lower(),
        "timestamp": instant,
        "log_signing_key_id": log_signing_key_id,
        "signature_algorithm": "Ed25519",
    }
    signature = log_private_key.sign(_canonical(payload))
    return {**payload, "signature_b64": base64.b64encode(signature).decode("ascii")}


def verify_signed_checkpoint(checkpoint: dict, log_public_key: Ed25519PublicKey) -> None:
    if not isinstance(checkpoint, dict) or checkpoint.get("schema") != CHECKPOINT_SCHEMA:
        raise IntakeError("INVALID_CHECKPOINT", "Unsupported transparency checkpoint")
    signature_b64 = checkpoint.get("signature_b64")
    payload = {key: value for key, value in checkpoint.items() if key != "signature_b64"}
    if payload.get("signature_algorithm") != "Ed25519":
        raise IntakeError("UNSUPPORTED_CHECKPOINT_SIGNATURE", "Checkpoint must use Ed25519")
    if not isinstance(payload.get("tree_size"), int) or isinstance(payload.get("tree_size"), bool) or payload["tree_size"] < 0:
        raise IntakeError("INVALID_TREE_SIZE", "Invalid checkpoint tree size")
    if not isinstance(payload.get("root_hash"), str) or len(payload["root_hash"]) != 64:
        raise IntakeError("INVALID_TREE_ROOT", "Invalid checkpoint root")
    try:
        bytes.fromhex(payload["root_hash"])
        signature = base64.b64decode(signature_b64, validate=True)
        _parse_aware_time(payload["timestamp"])
        log_public_key.verify(signature, _canonical(payload))
    except (ValueError, TypeError, KeyError, InvalidSignature) as exc:
        raise IntakeError("CHECKPOINT_SIGNATURE_INVALID", "Checkpoint signature or fields are invalid") from exc


class IndependentAuditWitness:
    """Pins signed checkpoints in a database operated separately from the log."""

    def __init__(
        self, database_path: str | Path, *,
        witness_id: str, witness_private_key: Ed25519PrivateKey,
    ):
        if not isinstance(witness_id, str) or not witness_id.strip():
            raise IntakeError("INVALID_WITNESS_ID", "Witness ID is required")
        self.database_path = str(database_path)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.witness_id = witness_id
        self.witness_private_key = witness_private_key
        self.witness_public_key_b64 = base64.b64encode(
            _raw_public_key(witness_private_key.public_key())
        ).decode("ascii")
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=5, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    def _initialize(self):
        connection = self._connect()
        try:
            if self.database_path != ":memory:":
                connection.execute("PRAGMA journal_mode=WAL")
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS witnessed_checkpoints (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_id TEXT NOT NULL,
                    tree_size INTEGER NOT NULL,
                    root_hash TEXT NOT NULL,
                    checkpoint_json TEXT NOT NULL,
                    checkpoint_hash TEXT NOT NULL,
                    witness_receipt_json TEXT NOT NULL,
                    UNIQUE(log_id, tree_size)
                );
                CREATE INDEX IF NOT EXISTS witnessed_checkpoints_latest
                    ON witnessed_checkpoints(log_id, sequence DESC);
                CREATE TRIGGER IF NOT EXISTS witnessed_checkpoint_no_update
                BEFORE UPDATE ON witnessed_checkpoints
                BEGIN SELECT RAISE(ABORT, 'witnessed checkpoints are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS witnessed_checkpoint_no_delete
                BEFORE DELETE ON witnessed_checkpoints
                BEGIN SELECT RAISE(ABORT, 'witnessed checkpoints are append-only'); END;
            """)
        finally:
            connection.close()

    def latest(self, log_id: str) -> dict | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT checkpoint_json,witness_receipt_json FROM witnessed_checkpoints "
                "WHERE log_id=? ORDER BY sequence DESC LIMIT 1", (log_id,)
            ).fetchone()
            if row is None:
                return None
            return {
                "checkpoint": json.loads(row["checkpoint_json"]),
                "witness_receipt": json.loads(row["witness_receipt_json"]),
            }
        finally:
            connection.close()

    def accept_checkpoint(
        self, checkpoint: dict, *, log_public_key: Ed25519PublicKey,
        consistency_proof: list[str] | None = None,
        consistency_verifier: Callable[[dict, dict, list[str]], bool] | None = None,
    ) -> dict:
        verify_signed_checkpoint(checkpoint, log_public_key)
        log_id = checkpoint["log_id"]
        previous = self.latest(log_id)
        if previous is not None:
            old = previous["checkpoint"]
            old_size = old["tree_size"]
            new_size = checkpoint["tree_size"]
            if new_size < old_size:
                raise IntakeError("CHECKPOINT_ROLLBACK", "Checkpoint tree size is older than the witnessed checkpoint")
            if new_size == old_size:
                if checkpoint["root_hash"] != old["root_hash"]:
                    raise IntakeError("CHECKPOINT_EQUIVOCATION", "Same tree size has a conflicting root hash")
                if checkpoint["timestamp"] < old["timestamp"]:
                    raise IntakeError("CHECKPOINT_TIME_ROLLBACK", "Checkpoint timestamp moved backwards")
                return previous
            if not consistency_proof or consistency_verifier is None:
                raise IntakeError("CONSISTENCY_PROOF_REQUIRED", "Tree growth requires an independently verified consistency proof")
            try:
                valid = consistency_verifier(old, checkpoint, consistency_proof)
            except Exception as exc:
                raise IntakeError("CONSISTENCY_PROOF_INVALID", "Consistency proof verifier failed") from exc
            if valid is not True:
                raise IntakeError("CONSISTENCY_PROOF_INVALID", "Checkpoint is not proven consistent with the prior witnessed tree")
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            latest_row = connection.execute(
                "SELECT checkpoint_json FROM witnessed_checkpoints WHERE log_id=? ORDER BY sequence DESC LIMIT 1",
                (log_id,),
            ).fetchone()
            if previous is None and latest_row is not None:
                raise IntakeError("WITNESS_CONCURRENT_UPDATE", "Another writer added a checkpoint; retry from the latest state")
            if previous is not None:
                current = json.loads(latest_row["checkpoint_json"]) if latest_row else None
                if current != previous["checkpoint"]:
                    raise IntakeError("WITNESS_CONCURRENT_UPDATE", "Witness checkpoint changed during verification")
            checkpoint_bytes = _canonical(checkpoint)
            checkpoint_hash = hashlib.sha256(checkpoint_bytes).hexdigest()
            receipt_payload = {
                "schema": WITNESS_RECEIPT_SCHEMA,
                "witness_id": self.witness_id,
                "witness_public_key_b64": self.witness_public_key_b64,
                "log_id": log_id,
                "tree_size": checkpoint["tree_size"],
                "checkpoint_hash": checkpoint_hash,
                "witnessed_at": datetime.now(timezone.utc).isoformat(),
                "signature_algorithm": "Ed25519",
            }
            receipt = {
                **receipt_payload,
                "signature_b64": base64.b64encode(
                    self.witness_private_key.sign(_canonical(receipt_payload))
                ).decode("ascii"),
            }
            connection.execute(
                """INSERT INTO witnessed_checkpoints(
                    log_id,tree_size,root_hash,checkpoint_json,checkpoint_hash,witness_receipt_json
                ) VALUES(?,?,?,?,?,?)""",
                (log_id, checkpoint["tree_size"], checkpoint["root_hash"],
                 checkpoint_bytes.decode("utf-8"), checkpoint_hash,
                 _canonical(receipt).decode("utf-8")),
            )
            connection.commit()
            return {"checkpoint": checkpoint, "witness_receipt": receipt}
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()


def verify_witness_receipt(receipt: dict, witness_public_key: Ed25519PublicKey) -> None:
    if not isinstance(receipt, dict) or receipt.get("schema") != WITNESS_RECEIPT_SCHEMA:
        raise IntakeError("INVALID_WITNESS_RECEIPT", "Unsupported witness receipt")
    payload = {key: value for key, value in receipt.items() if key != "signature_b64"}
    try:
        signature = base64.b64decode(receipt["signature_b64"], validate=True)
        witness_public_key.verify(signature, _canonical(payload))
    except (ValueError, TypeError, KeyError, InvalidSignature) as exc:
        raise IntakeError("WITNESS_SIGNATURE_INVALID", "Witness receipt signature is invalid") from exc
