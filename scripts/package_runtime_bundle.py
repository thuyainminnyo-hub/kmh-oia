"""Create a deterministic, manifest-bound KMH OIA Python runtime source bundle."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

ROOT_NAME = 'kmh-oia-runtime-source'

def build_runtime_bundle(source_root: str | Path, source_revision: str, output: str | Path) -> Path:
    root = Path(source_root).resolve()
    revision = source_revision.strip().lower() if isinstance(source_revision, str) else ''
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('source_revision must be a full lowercase 40-character Git SHA')
    source_dir = root / 'src'
    requirements = root / 'requirements.txt'
    if not source_dir.is_dir() or not requirements.is_file():
        raise ValueError('runtime source root must contain src/ and requirements.txt')
    files: dict[str, bytes] = {}
    for path in sorted(source_dir.rglob('*')):
        rel_parts = path.relative_to(source_dir).parts
        if '__pycache__' in rel_parts or path.suffix in {'.pyc', '.pyo'}:
            continue
        if path.is_symlink():
            raise ValueError(f'symlinks are not allowed in runtime source bundle: {path.relative_to(root)}')
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f'non-regular runtime source item is not allowed: {path.relative_to(root)}')
        rel = path.relative_to(root).as_posix()
        if '..' in PurePosixPath(rel).parts or rel.startswith('/'):
            raise ValueError('unsafe runtime source path')
        files[rel] = path.read_bytes()
    files['requirements.txt'] = requirements.read_bytes()
    if not any(p.startswith('src/') and p.endswith('.py') for p in files):
        raise ValueError('runtime bundle must include at least one src/*.py module')
    manifest = {
        'schema_version': 1,
        'source_revision': revision,
        'files': [{'path': path, 'sha256': hashlib.sha256(files[path]).hexdigest()} for path in sorted(files)],
    }
    payloads = dict(files)
    payloads['SOURCE_REVISION'] = (revision + '\n').encode('ascii')
    payloads['MANIFEST.json'] = (json.dumps(manifest, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        raw = destination.open('xb')
    except FileExistsError:
        raise ValueError('output already exists; refusing to overwrite a runtime bundle') from None
    with raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for rel in sorted(payloads):
                data = payloads[rel]
                info = tarfile.TarInfo(f'{ROOT_NAME}/{rel}')
                info.size = len(data)
                info.mtime = 0
                info.uid = 0
                info.gid = 0
                info.uname = ''
                info.gname = ''
                info.mode = 0o644
                archive.addfile(info, io.BytesIO(data))
    return destination

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', default='.')
    parser.add_argument('--source-revision', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    path = build_runtime_bundle(args.source_root, args.source_revision, args.output)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    print(f'runtime source bundle created: {path}')
    print(f'bundle_sha256={digest}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
