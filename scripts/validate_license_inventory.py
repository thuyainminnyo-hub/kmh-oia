#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

def audit(sbom_path, inventory_path):
    sbom = json.loads(Path(sbom_path).read_text(encoding='utf-8'))
    inventory = json.loads(Path(inventory_path).read_text(encoding='utf-8'))
    entries = {(x['name'], x.get('version')): x for x in inventory['entries']}
    packages = {(x['name'], x.get('versionInfo')) for x in sbom['packages']}
    verified, missing, project = [], [], 'NOT_FOUND'
    for name, version in packages:
        entry = entries.get((name, version))
        if name == '.':
            project = entry.get('review_status', 'OWNER_DECISION_REQUIRED') if entry else 'NOT_FOUND'
        elif entry and entry.get('review_status') == 'VERIFIED' and entry.get('license') not in ('', 'NOASSERTION', 'UNDECLARED') and str(entry.get('evidence_url', '')).startswith('https://'):
            verified.append({'name': name, 'version': version, 'license': entry['license']})
        else:
            missing.append({'name': name, 'version': version})
    errors = []
    if missing: errors.append('external SPDX packages lack verified license evidence')
    if project == 'NOT_FOUND': errors.append('project license decision is missing')
    status = 'HOLD' if errors else ('REVIEW_REQUIRED' if project != 'VERIFIED' else 'PASS')
    return {'status': status, 'unique_spdx_packages': len(packages), 'external_packages_verified': len(verified), 'external_packages_unreviewed': missing, 'external_license_evidence': verified, 'project_license_status': project, 'errors': errors, 'limitations': ['Action repository licenses do not enumerate bundled transitive dependencies.', 'Source-tree SBOM does not fetch remote action source trees.', 'requirements.txt is not a resolved transitive Python lockfile.', 'Project license requires explicit owner decision.', 'This is not legal advice or a license compatibility determination.']}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--sbom',required=True); p.add_argument('--inventory',default='licenses/dependency-license-review.json'); p.add_argument('--output'); a=p.parse_args()
    try: result=audit(a.sbom,a.inventory)
    except (OSError,ValueError,KeyError,TypeError) as exc: result={'status':'HOLD','errors':[str(exc)]}
    rendered=json.dumps(result,indent=2)+'\n'
    if a.output: Path(a.output).write_text(rendered,encoding='utf-8')
    print(rendered,end='')
    return 1 if result['status']=='HOLD' else 0

if __name__ == '__main__': raise SystemExit(main())
