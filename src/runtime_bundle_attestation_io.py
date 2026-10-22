"""Strict JSON I/O for runtime-source bundle attestations."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from src.runtime_artifact_measurement import normalize_sha256
from src.runtime_bundle_attestation import RuntimeBundleAttestation

_FIELDS = frozenset({
    'bundle_sha256', 'issuer', 'subject', 'attestation_id', 'key_id', 'source_revision',
    'build_run_id', 'artifact_id', 'artifact_name', 'artifact_digest', 'issued_at',
    'signature', 'schema_version',
})

class RuntimeBundleAttestationIOError(ValueError):
    pass

def write_runtime_bundle_attestation(path: str | Path, attestation: RuntimeBundleAttestation) -> Path:
    if not isinstance(attestation, RuntimeBundleAttestation):
        raise RuntimeBundleAttestationIOError('a runtime bundle attestation object is required')
    destination = Path(path)
    if destination.suffix.lower() != '.json':
        raise RuntimeBundleAttestationIOError('attestation output path must end in .json')
    payload = json.dumps(asdict(attestation), sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'
    if len(payload.encode('utf-8')) > 65536:
        raise RuntimeBundleAttestationIOError('attestation JSON exceeds 64 KiB')
    try:
        with destination.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise RuntimeBundleAttestationIOError('attestation output already exists; refusing to overwrite evidence') from exc
    except OSError as exc:
        raise RuntimeBundleAttestationIOError('attestation output could not be written') from exc
    return destination

def load_runtime_bundle_attestation(path: str | Path) -> RuntimeBundleAttestation:
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeBundleAttestationIOError('attestation JSON is missing, unreadable, or invalid') from exc
    if not isinstance(data, dict) or set(data) != _FIELDS:
        raise RuntimeBundleAttestationIOError('attestation JSON must contain exactly the supported fields')
    if isinstance(data.get('schema_version'), bool) or data.get('schema_version') != 1:
        raise RuntimeBundleAttestationIOError('unsupported attestation schema version')
    if any(not isinstance(data.get(k), str) or not data[k].strip() for k in _FIELDS - {'schema_version'}):
        raise RuntimeBundleAttestationIOError('attestation fields must be non-empty strings')
    try:
        normalize_sha256(data['bundle_sha256'])
        normalize_sha256(data['artifact_digest'])
    except ValueError as exc:
        raise RuntimeBundleAttestationIOError('attestation contains invalid SHA-256 digest') from exc
    rev = data['source_revision'].lower()
    if len(rev) not in (40, 64) or any(c not in '0123456789abcdef' for c in rev):
        raise RuntimeBundleAttestationIOError('source_revision must be a full 40- or 64-character SHA')
    for key in ('build_run_id', 'artifact_id'):
        if not data[key].isdigit() or data[key].startswith('0'):
            raise RuntimeBundleAttestationIOError(f'{key} must be a canonical positive decimal ID')
    data['source_revision'] = rev
    return RuntimeBundleAttestation(**data)
