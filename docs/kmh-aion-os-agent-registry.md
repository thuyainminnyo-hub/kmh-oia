# KMH AION OS — Agent Registry Foundation

## Increment F1

The first registry increment adds a deterministic, in-memory catalogue for agent metadata and lifecycle status.

## Record contract

Each registered agent has:
- stable lowercase `agent_id`
- display name and role
- accountable owner
- version
- one or more unique capabilities
- lifecycle status: ACTIVE, SUSPENDED, DEPRECATED, or REVOKED
- optional description

The strict JSON Schema is maintained at `schemas/agent-record.schema.json`.

## Lifecycle

- ACTIVE → SUSPENDED, DEPRECATED, REVOKED
- SUSPENDED → ACTIVE, DEPRECATED, REVOKED
- DEPRECATED → REVOKED
- REVOKED → no further transitions

Revocation is terminal. Records are not silently deleted.

## Security boundary — critical

This module is only a metadata registry. It does not authenticate agents, issue credentials, authorize tool calls, or make an agent trusted. Declared capabilities are descriptive metadata, not permission grants. Every invocation must continue through the runtime security and autonomy policies.

The next increment must bind a verified execution identity to a task-scoped grant and enforce capability checks at the governed-tool boundary. Deny by default, check each request, log allow and deny decisions, and require human approval for consequential external actions.

## Current limitations

- In-memory only; restart persistence is not provided.
- No concurrent/distributed consistency guarantee.
- No credential issuance or cryptographic attestation.
- No runtime invocation integration in this increment.
- No claim of production readiness.

## Verification

Run:
```bash
python -m unittest discover -s tests -p 'test_agent_registry.py' -v
python -m unittest discover -s tests -v
```

Record actual results and CI evidence before promoting the increment beyond IMPLEMENTED.
