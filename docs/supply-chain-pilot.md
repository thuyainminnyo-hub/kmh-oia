# KMH OIA Supply Chain CI Pilot

## Purpose

Phase 1010 pilot: generate an SPDX JSON Software Bill of Materials (SBOM) for the checked-out KMH OIA source tree, validate the document structure, record content hashes and GitHub run metadata, and create a signed SBOM attestation for pushes to the public `main` branch.

This is a narrowly scoped inventory and provenance pilot. It does not claim that the repository is secure, that every transitive dependency is discoverable, or that a successful SBOM generation is a vulnerability assessment.

## Workflow

Workflow: `.github/workflows/supply-chain-assurance.yml`

Dependency declaration: `requirements.txt` pins the known third-party validator dependency used by `scripts/validate_prompt_record.py`. It is a CI/tooling dependency declaration, not a claim that all KMH OIA runtime dependencies have been inventoried.

1. Pull requests and pushes to `main` generate an SPDX JSON SBOM using Anchore Syft.
2. The workflow checks required SPDX document fields, SPDX 2.x version, package-list shape, and package identifiers.
3. It inventories recognized dependency manifests and lockfiles, counts `NOASSERTION` license fields, and records a separate `REVIEW_REQUIRED` status when dependency coverage or license evidence is incomplete. This review status does not mislabel structural validation as a security pass.
4. It creates a source archive for the exact `GITHUB_SHA` and records SHA-256 digests for the SBOM and source archive in `supply-chain-evidence.json`.
5. The three evidence files are uploaded as a 14-day workflow artifact.
6. Only a push to `main` receives the attestation job. That job uses GitHub artifact attestations to bind the source archive to the SPDX SBOM.
7. Prompt Library Schema QA installs the validator from the pinned `requirements.txt` instead of resolving an unpinned latest version.

All third-party actions in this workflow are pinned to full commit SHAs. The attestation job has separate, least-privilege permissions and does not run for pull-request events.

## Evidence outputs

- `sbom.spdx.json`: Syft-generated SPDX JSON inventory.
- `kmh-oia-source.tar.gz`: source snapshot for the exact workflow commit.
- `supply-chain-evidence.json`: repository, commit, event, generation timestamp, package counts, dependency-manifest coverage, license `NOASSERTION` count, review findings, and SHA-256 digests.

## Gate semantics

- **STRUCTURE PASS**: SBOM is non-empty and its basic SPDX structure and package entries pass validation.
- **REVIEW REQUIRED**: no recognized dependency manifest/lockfile was found, or one or more package license fields are `NOASSERTION`. This is a coverage/compliance review signal, not a CI structural failure.
- **NOT RUN**: signed attestation is intentionally skipped for pull requests and non-main refs.
- **ATTESTATION GENERATED**: the main-branch attestation action completes successfully. Consumers must still cryptographically verify it before relying on it.

This pilot is not yet configured as a required branch-protection check and does not block releases. Promote it to a required gate only after reviewing the first real workflow run, inspecting the generated SBOM for coverage, and verifying the resulting attestation with GitHub CLI.

## Known limitations

- Syft can only inventory components it can discover from the checked-out source tree and supported catalogers. Directory scans use manifest/lockfile catalogers for declared dependencies; missing or incomplete manifests can leave runtime dependency coverage unverified.
- GitHub Actions workflow references may be cataloged even when application runtime dependencies are not declared. The package count must not be treated as proof of complete application dependency coverage.
- `NOASSERTION` means the SBOM does not assert a license conclusion for that entry; it must be reviewed using authoritative package metadata rather than guessed.
- A package count of zero is a review signal, not proof that the project has no dependencies.
- The SBOM is not a vulnerability scan, malware analysis, license-compliance decision, or independent security certification.
- The source archive is the repository source snapshot, not a compiled or deployed production artifact.
- GitHub documents artifact attestations as available for public repositories on current plans. Private/internal repository use requires GitHub Enterprise Cloud.
- The initial artifact review found 16 SPDX entries (9 unique name/version pairs), no recognized dependency manifest/lockfile, and `NOASSERTION` license fields across all 16 entries. A subsequent change adds the explicitly documented CI/tooling dependency `jsonschema==4.26.0` to `requirements.txt` and makes Schema QA install from that file. This improves declared CI dependency coverage but does not establish that all application/runtime dependencies are declared; transitive dependency completeness and license review remain open.

## References

- [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations)
- [GitHub: Using artifact attestations to establish provenance for builds](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [Anchore SBOM Action](https://github.com/anchore/sbom-action)
