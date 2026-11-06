# GitHub Actions immutable pin inventory — Phase 2.2

This candidate replaces movable major-version tags with full commit SHAs for the workflow actions found in the repository's default-branch workflow inventory at the time of this review.

| Action | Version tag reviewed | Full commit SHA |
|---|---|---|
| actions/checkout | v4 | 11d5960a326750d5838078e36cf38b85af677262 |
| actions/checkout | v6 | d23441a48e516b6c34aea4fa41551a30e30af803 |
| actions/setup-python | v5 | a26af69be951a213d495a4c3e4e4022e16d87065 |
| actions/setup-python | v6 | ece7cb06caefa5fff74198d8649806c4678c61a1 |
| actions/setup-node | v7 | 949feb2413d6458794dcd2491c4babbbce0c15c1 |
| actions/configure-pages | v5 | 983d7736d9b0ae728b81ab479565c72886d7745b |
| actions/upload-pages-artifact | v4 | 7b1f4a764d45c48632c6b24a0339c27f5614fb0b |
| actions/deploy-pages | v4 | d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e |
| actions/upload-artifact | v4 | ea165f8d65b6e75b540449e92b4886f43607fa02 |

## Verification method
- Resolved each referenced version tag through the GitHub Git References API.
- Confirmed each returned Git object is a commit object and used its full 40-character SHA.
- Kept the human-readable version tag in a YAML comment beside each pin.
- This inventory does not claim to cover reusable workflows or third-party actions not found in the current workflow files. Re-run inventory whenever workflow files change.

## Governance
Sandbox candidate only. Pinning actions reduces risk from a movable tag but does not prove the action's code is benign. Review upstream source, permissions, transitive actions, and release provenance before production use.
