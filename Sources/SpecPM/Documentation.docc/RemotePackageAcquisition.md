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

## Core vs Downstream

SpecPM core may eventually own exact metadata lookup, digest verification,
deterministic cache writes, lock updates, and package validation.

Authentication policy, tenant authorization, organization allowlists, semantic
package selection, graph reasoning, signing infrastructure, and agent workflow
execution need separate designs and may belong in downstream or enterprise
tools.

## Source Contract

The detailed boundary is maintained in
`specs/REMOTE_PACKAGE_ACQUISITION.md`.
