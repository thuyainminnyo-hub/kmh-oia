# Security and Governance

## Default-deny integration policy

- No third-party skill/plugin is installed by this pilot.
- Do not index secrets, `.env` files, credentials, private keys, personal data, generated user media, or unrestricted Library exports.
- Graphify indexing must use an explicit allowlist of public/project documentation paths and must exclude secret/config directories before it is run.
- Review external skill code, scripts, package manifests, hooks, network calls, shell commands, and license before adoption.
- Pin package/plugin versions or commits after approval; do not follow floating `main` automatically in production.
- Use project-scoped installation, not global installation, for initial experiments.
- Keep network access and tool permissions disabled unless the task requires them and an operator approves.
- Do not let design agents change auth, payments, child-data handling, security controls, or deployment settings.

## Human approval gates

| Gate | Required reviewer | Evidence |
|---|---|---|
| Third-party tool intake | Technical owner | Source, version, license, dependency and permission review |
| Project context indexing | Data owner | Approved path allowlist and exclusion report |
| Design direction | Product/design owner | Alternatives, rationale and selected direction |
| Cultural/character review | MLCW owner | Source references and protected-identity inspection |
| Accessibility review | QA reviewer | Contrast, keyboard, focus, responsive and reduced-motion results |
| Release | Authorized release owner | Complete QA evidence and rollback plan |

## Child/privacy safeguards for MLCW

The pilot must not collect or expose children's full names, precise location, school, contact details, face photographs, or unrelated identifiers. Do not add advertising, analytics, telemetry, or third-party asset uploads before a dedicated privacy assessment. Store only the minimum learning state necessary, with retention and deletion rules defined before any learner-facing trial.

## External service boundary

Graphify semantic processing of PDFs/images may involve a configured model/API; do not assume every extraction is fully local. Review the selected provider and data flow before ingesting private material. Anthropic credentials, subscription sign-in, and API usage must follow Anthropic's published terms; this project must not broker or collect user credentials.

## Incident response

If a plugin or agent attempts an unapproved network request, reads an excluded path, or changes protected files: stop execution, preserve logs, revert the unapproved change, rotate any exposed credentials, and record an incident before resuming.
