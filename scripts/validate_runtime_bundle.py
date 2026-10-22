"""Fail-closed validator for deterministic KMH OIA source release bundles."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import PurePosixPath
import re
import tarfile
from pathlib import Path

ROOT_NAME = 'kmh-oia-runtime-source'

def validate_runtime_bundle(path: str | Path, *, expected_source_sha: str) -> dict:
    expected = expected_source_sha.strip().lower() if isinstance(expected_source_sha, str) else ''
    if not re.fullmatch(r'[0-9a-f]{40}', expected):
        raise ValueError('expected source SHA must be a full lowercase 40-character Git SHA')
    try:
        content = Path(path).read_bytes()
        if not content:
            raise ValueError('runtime bundle must not be empty')
        with tarfile.open(fileobj=io.BytesIO(content), mode='r:gz') as archive:
            members = archive.getmembers()
            if not members or any(not item.isfile() for item in members):
                raise ValueError('runtime bundle may contain regular files only')
            names = [item.name for item in members]
            if len(names) != len(set(names)):
                raise ValueError('duplicate archive paths are forbidden')
            payloads = {}
            for member in members:
                item_path = PurePosixPath(member.name)
                if item_path.is_absolute() or '..' in item_path.parts or not item_path.parts or item_path.parts[0] != ROOT_NAME:
                    raise ValueError('unsafe or unexpected archive path')
                rel = item_path.relative_to(ROOT_NAME).as_posix()
                if not rel or rel == '.':
                    raise ValueError('archive must not include a root directory entry')
                handle = archive.extractfile(member)
                if handle is None:
                    raise ValueError('archive member could not be read')
                payloads[rel] = handle.read()
    except (OSError, tarfile.TarError, EOFError) as exc:
        raise ValueError('runtime bundle is missing, unreadable, or invalid gzip/tar') from exc
    if 'SOURCE_REVISION' not in payloads or 'MANIFEST.json' not in payloads or 'requirements.txt' not in payloads:
        raise ValueError('runtime bundle must contain SOURCE_REVISION, MANIFEST.json, and requirements.txt')
    revision = payloads['SOURCE_REVISION'].decode('ascii', errors='strict').strip()
    if revision != expected:
        raise ValueError('bundle SOURCE_REVISION does not match expected source SHA')
    if not any(k.startswith('src/') and k.endswith('.py') for k in payloads):
        raise ValueError('runtime bundle must include at least one src/*.py module')
    try:
        manifest = json.loads(payloads['MANIFEST.json'].decode('utf-8'))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('runtime bundle manifest must be valid UTF-8 JSON') from exc
    if not isinstance(manifest, dict) or set(manifest) != {'schema_version', 'source_revision', 'files'}:
        raise ValueError('runtime bundle manifest must contain exactly schema_version, source_revision and files')
    if isinstance(manifest.get('schema_version'), bool) or manifest['schema_version'] != 1 or manifest.get('source_revision') != expected:
        raise ValueError('runtime bundle manifest schema/source revision mismatch')
    listed = manifest.get('files')
    if not isinstance(listed, list) or not listed:
        raise ValueError('runtime bundle manifest files must be a non-empty list')
    actual_files = {k: v for k, v in payloads.items() if k not in {'SOURCE_REVISION', 'MANIFEST.json'}}
    manifest_files = {}
    for entry in listed:
        if not isinstance(entry, dict) or set(entry) != {'path', 'sha256'}:
            raise ValueError('manifest file entries must contain exactly path and sha256')
        rel, digest = entry['path'], entry['sha256']
        if not isinstance(rel, str) or not rel or rel in manifest_files or not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('manifest path or digest is malformed/duplicated')
        if PurePosixPath(rel).is_absolute() or '..' in PurePosixPath(rel).parts:
            raise ValueError('manifest contains an unsafe path')
        manifest_files[rel] = digest
    if set(manifest_files) != set(actual_files):
        raise ValueError('manifest file list does not match actual bundle content')
    for rel, data in actual_files.items():
        if hashlib.sha256(data).hexdigest() != manifest_files[rel]:
            raise ValueError(f'manifest SHA-256 mismatch for {rel}')
    file_sha256 = {rel: hashlib.sha256(data).hexdigest() for rel, data in sorted(actual_files.items())}
    return {'source_revision': expected, 'bundle_sha256': hashlib.sha256(content).hexdigest(),
            'files_verified': len(actual_files), 'files_sha256': file_sha256}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path')
    parser.add_argument('--expected-source-sha', required=True)
    args = parser.parse_args(argv)
    result = validate_runtime_bundle(args.path, expected_source_sha=args.expected_source_sha)
    print('runtime source bundle validation: passed')
    print('bundle_sha256=' + result['bundle_sha256'])
    print('files_verified=' + str(result['files_verified']))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
