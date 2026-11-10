# Phase 02.77 — MIDI 2.0 / SMF2 Interoperability & Long-Term Preservation Research

**Status:** Research and architecture proposal only; no MIDI 2.0 or SMF2 implementation.
**Date:** 2026-11-09
**Branch:** phase-02-71/midi-golden-fixtures
**Depends on:** Phase 02.74 raw source preservation; Phase 02.75 canonical event contract; Phase 02.76 SMF conformance matrix.

## Executive decision

Keep MIDI 1.0 Standard MIDI File (SMF) as the first supported import target. Design the canonical event model so it can later represent MIDI 2.0 Universal MIDI Packet (UMP) and MIDI Clip File (SMF2) without pretending the two protocols have identical semantics.

Do not convert MIDI 2.0 data into MIDI 1.0 note events and discard higher-resolution or per-note attributes. Preserve the original container and protocol identity, then create a documented compatibility projection when needed.

## Primary-source findings

### MIDI 2.0 extends MIDI 1.0; it does not replace it
The MIDI Association states that MIDI 2.0 builds on MIDI 1.0 core principles and is not a stand-alone replacement. Developers need to understand MIDI 1.0 to implement MIDI 2.0:
- https://midi.org/midi-2-0

### MIDI-CI is capability negotiation
MIDI Capability Inquiry allows bidirectional devices to discover and negotiate extended capabilities while protecting backward compatibility. It covers Profile Configuration, Property Exchange, and protocol negotiation:
- https://midi.org/details-about-midi-2-0-midi-ci-profiles-and-property-exchange-updated-june-2023
- https://midi.org/midi-2-0

### Property Exchange carries structured device resources
MIDI-CI Property Exchange exchanges resources between devices using System Exclusive messages, including JSON data in defined header/property payloads. It is a live device capability/configuration mechanism, not a substitute for archiving a song's original performance data:
- https://midi.org/midi-2-0-property-exchange
- https://midi.org/core-property-exchange-2

### SMF2 / MIDI Clip File is a distinct file format
The MIDI Association's MIDI 2.0 core collection includes a MIDI Clip File specification, described as an SMF format for UMP. The collection also records updates to MIDI-CI and UMP specifications:
- https://midi.org/midi-2-0-core-specification-collection
- https://midi.org/midi-2-0-individual-collection-items

### SMF remains an interchange/archive format with its own boundaries
The MIDI Association describes SMF as a timestamped interchange format, not necessarily the native working format of every sequencer:
- https://midi.org/standard-midi-files

The Library of Congress describes SMF as a structured symbolic wrapper format used in creation, exchange, and preservation contexts. Its sustainability depends on preserving format identification and source bytes:
- https://www.loc.gov/preservation/digital/formats/fdd/fdd000119.shtml

## Architecture implications for Verified Music Notes Library

### 1. Protocol identity must be explicit
Add a container/protocol discriminator in the source manifest, for example:
- `smf1`
- `smf2_ump`
- `live_midi1_byte_stream`
- `live_midi2_ump_stream`
- `unknown_or_unclassified`

Do not infer the protocol solely from a filename extension.

### 2. Preserve native source before conversion
For every imported object, preserve:
- exact original bytes or immutable content-addressed object reference;
- SHA-256 and byte length;
- declared format/protocol and parser version;
- import provenance and timestamp;
- warnings and validation outcome.

Any conversion to a compatibility representation must create a separate derived object with its own hash, converter version, loss report, and links to the source object.

### 3. Canonical event model should be extensible, not MIDI-1-only
The event envelope should support:
- protocol and message-format version;
- group, channel, track/clip context where applicable;
- native timestamp representation and clock domain;
- raw packet/message bytes;
- decoded fields with explicit precision and units;
- per-note/controller attributes where supported;
- opaque preservation for unimplemented messages.

MIDI 2.0 UMP has packet structures and message types that do not map one-to-one to MIDI 1.0 byte-stream events. Do not flatten UMP to status/data bytes without a reversible encoding or explicit loss statement.

### 4. Separate file import from device negotiation
MIDI-CI and Property Exchange belong in a device-connection/capability layer:
- discover protocol and supported profiles;
- negotiate protocol only when both endpoints support it;
- query device resources only when useful and user-authorized;
- record device identity/capability evidence separately from the imported music file.

A device's current tuning or patch property does not prove the tuning used in an old recording unless the recording provenance links them.

### 5. Avoid premature SMF2 implementation
SMF2/UMP support should begin only after:
- MIDI 1.0 raw event preservation and SMF conformance gates pass;
- the canonical schema can preserve unknown/new UMP message types;
- official SMF2/UMP specification versions and test vectors are available to the implementation team;
- a separate SMF2 fixture corpus and independent oracle strategy are defined.

## Proposed gates

### Gate A — MIDI 1.0 archival baseline
- Finish byte-preserving SMF1 ingestion.
- Validate header/chunk/event offsets and source hash.
- Retain unknown chunks, Meta Events, and SysEx payloads.
- Keep parser policy and unsupported status explicit.

### Gate B — Canonical protocol envelope
- Add protocol discriminator and native timestamp/clock fields.
- Keep existing note projection backward-compatible.
- Require loss reports for conversions.

### Gate C — MIDI 2.0 research corpus
- Collect official versioned UMP and SMF2 specification references.
- Build synthetic UMP packet fixtures for supported message families.
- Add independent implementation comparisons only where semantics are documented.
- Include high-resolution values and per-note controller attributes in fixtures.

### Gate D — Device capability adapter
- Separate MIDI-CI negotiation and Property Exchange from file parsing.
- Test devices that support MIDI 1.0 only, MIDI 2.0, and no MIDI-CI.
- Do not assume a device supports MIDI-CI because it supports MIDI 2.0 transport.

## Acceptance criteria

- Original source bytes are retained and hash-verifiable.
- Protocol identity is explicit and validated.
- No MIDI 2.0 data is silently down-converted or stripped.
- Any compatibility conversion is separately hashed and accompanied by a loss report.
- MIDI-CI device properties are not misrepresented as historical performance metadata.
- SMF2 remains out of production scope until its own conformance corpus passes.

## Non-claims

- No MIDI 2.0 UMP parser is implemented.
- No SMF2 import/export is implemented.
- No MIDI-CI device negotiation or Property Exchange is implemented.
- No MIDI 2.0 device compatibility is claimed.
- This document does not authorize merge, release, or deployment.

## Decision

Prioritize a trustworthy MIDI 1.0 evidence archive and extensible protocol envelope. Treat MIDI 2.0/SMF2 as a future compatibility lane, not a reason to delay the current verified SMF1 baseline.
