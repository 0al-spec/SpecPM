# Remote Package Acquisition

SpecPM does not currently install or fetch remote package archives for user
projects. The current remote surface is metadata-only.

## Current Boundary

`specpm remote` reads `/v0` registry metadata and validates payload shape. It
does not download archives, mutate local project state, execute package content,
or select packages from natural language.

`specpm public-index generate` can check out maintainer-reviewed public Git
sources while building the static public registry, but those sources must be
pinned by exact revision. Mutable labels are not trust roots.

## Future Requirements

Any future remote acquisition design must define:

- exact package version selection;
- archive URL, format, size, and digest handling;
- digest verification before cache or lock writes;
- deterministic cache layout;
- lockfile fields for registry base URL, package ID, version, archive URL,
  archive format, digest, and registry API version;
- structured failure modes for unsupported profiles, missing digests, digest
  mismatches, cache collisions, validation failure, yanked versions, and mutable
  source refs without exact revisions.

Package content remains untrusted data. Acquisition, validation, caching, and
lockfile generation must not execute package content.

## Acquisition States

Future acquisition must move through explicit states:

- `observed_metadata`;
- `selected_version`;
- `downloaded_archive`;
- `verified_archive`;
- `validated_package`;
- `cached_package`;
- `locked_package`.

Each state requires the previous evidence. Downloaded bytes are not acquired
until their digest is verified, verified bytes are not publisher trust, and a
cache entry is not host execution authority.

## Cache, Lock, and Trust

Cache and lock writes must be atomic from the user's perspective:

- downloaded bytes are written to temporary storage first;
- digest verification happens before committed cache writes;
- lockfile entries are written only after archive verification and package
  validation succeed;
- failed acquisition leaves the previous valid state or removable temporary
  files;
- re-acquiring the same digest is idempotent;
- re-acquiring the same `package_id@version` with a different digest fails
  unless an explicit lifecycle or replacement policy has been accepted.

Digest verification proves bytes, not publisher authority. Signature
verification, revocation policy, and provenance receipt enforcement require
separate implemented policies before acquisition can claim stronger trust.

## Failure Categories

Future acquisition errors should be structured. At minimum they should
distinguish registry unavailability, unsupported registry API or profile,
ambiguous selection, unsupported archive format or transport, missing digest,
digest mismatch, cache collision, validation failure, lifecycle blocking,
lockfile mismatch, unmet trust policy, partial-write recovery, and mutable
source refs.

## Core vs Downstream

SpecPM core may eventually own exact metadata lookup, digest verification,
deterministic cache writes, lock updates, and package validation.

Authentication policy, tenant authorization, organization allowlists, semantic
package selection, graph reasoning, signing infrastructure, and agent workflow
execution need separate designs and may belong in downstream or enterprise
tools.

Package signing, verification, revocation, yanked/deprecated semantics, and
provenance receipt expectations are documented separately in
<doc:PackageSigningRevocation>.
Provenance receipt schema expectations are documented in
<doc:ProvenanceReceipts>.

## Source Contract

The detailed boundary is maintained in
`specs/REMOTE_PACKAGE_ACQUISITION.md`.
