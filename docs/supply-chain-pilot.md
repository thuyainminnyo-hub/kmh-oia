# KMH OIA Supply Chain CI Pilot

## Purpose

Phase 1010 pilot: generate an SPDX JSON Software Bill of Materials (SBOM) for the checked-out KMH OIA source tree, validate the document structure, record content hashes and GitHub run metadata, and create a signed SBOM attestation for pushes to the public `main` branch.

This is a narrowly scoped inventory and provenance pilot. It does not claim that the repository is secure, that every transitive dependency is discoverable, or that a successful SBOM generation is a vulnerability assessment.

## Workflow

Workflow: `.github/workflows/supply-chain-assurance.yml`

1. Pull requests and pushes to `main` generate an SPDX JSON SBOM using Anchore Syft.
2. The workflow checks required SPDX document fields, SPDX 2.x version, package-list shape, and package identifiers.
3. It creates a source archive for the exact `GITHUB_SHA` and records SHA-256 digests for the SBOM and source archive in `supply-chain-evidence.json`.
4. The three evidence files are uploaded as a 14-day workflow artifact.
5. Only a push to `main` receives the attestation job. That job uses GitHub artifact attestations to bind the source archive to the SPDX SBOM.

All third-party actions in this workflow are pinned to full commit SHAs. The attestation job has separate, least-privilege permissions and does not run for pull-request events.

## Evidence outputs

- `sbom.spdx.json`: Syft-generated SPDX JSON inventory.
- `kmh-oia-source.tar.gz`: source snapshot for the exact workflow commit.
- `supply-chain-evidence.json`: repository, commit, event, generation timestamp, package count, and SHA-256 digests.

## Gate semantics

- **PASS**: SBOM is non-empty and its basic SPDX structure and package entries pass validation.
- **NOT RUN**: signed attestation is intentionally skipped for pull requests and non-main refs.
- **ATTESTATION PASS**: the main-branch attestation action completes successfully. This confirms the attestation was generated; consumers must still verify it before relying on it.

This pilot is not yet configured as a required branch-protection check and does not block releases. Promote it to a required gate only after reviewing the first real workflow run, inspecting the generated SBOM for coverage, and verifying the resulting attestation with GitHub CLI.

## Known limitations

- Syft can only inventory components it can discover from the checked-out source tree and supported catalogers. Missing or incomplete manifests can produce incomplete inventory.
- A package count of zero is a review signal, not proof that the project has no dependencies.
- The SBOM is not a vulnerability scan, malware analysis, license-compliance decision, or independent security certification.
- The source archive is the repository source snapshot, not a compiled or deployed production artifact.
- GitHub documents artifact attestations as available for public repositories on current plans. Private/internal repository use requires GitHub Enterprise Cloud.
- The first run must be inspected before the pilot is considered operationally verified.

## References

- [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations)
- [GitHub: Using artifact attestations to establish provenance for builds](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [Anchore SBOM Action](https://github.com/anchore/sbom-action)
