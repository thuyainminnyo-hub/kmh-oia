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

## Lifecycle

- ACTIVE → SUSPENDED, DEPRECATED, REVOKED
- SUSPENDED → ACTIVE, DEPRECATED, REVOKED
- DEPRECATED → REVOKED
- REVOKED → no further transitions

Revocation is terminal. Records are not silently deleted.

## Security boundary

This module is only a metadata registry. It does not authenticate agents, issue credentials, authorize tool calls, or make an agent trusted. Every invocation must continue through the existing runtime security and autonomy policies. Capability metadata must not be treated as an executable grant.

The next increment must bind registry identity to execution context and enforce capability checks at the governed-tool boundary, with negative tests for unknown, suspended, deprecated, and revoked agents.

## Current limitations

- In-memory only; restart persistence is not provided.
- No concurrent/distributed consistency guarantee.
- No credential issuance or cryptographic attestation.
- No runtime invocation integration in this increment.
- No claim of production readiness.

## Verification

Run:
```bash
python -m unittest tests.test_agent_registry -v
python -m unittest discover -s tests -v
```

Record actual results and CI evidence before promoting the increment beyond IMPLEMENTED.
