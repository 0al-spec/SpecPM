# SpecPM Remote Package Acquisition Boundary

Status: Draft
Updated: 2026-05-24
Scope: future archive fetch, cache, lock, and remote add behavior

## Purpose

This note defines the boundary that must exist before SpecPM implements remote
package archive acquisition.

SpecPM already has read-only remote registry metadata commands and build-time
public index generation. Those surfaces are not package installation:

- `specpm remote ...` reads `/v0` metadata and does not download archives;
- `specpm public-index generate` may check out maintainer-reviewed pinned Git
  sources to build static registry metadata;
- generated `/v0` archive URLs and digests are metadata evidence, not host
  authority;
- package content remains untrusted data.

No future remote acquisition behavior may weaken those boundaries.

## Current Boundary

Current SpecPM core does not provide:

- remote archive download for user projects;
- remote package install;
- remote package cache management;
- remote add by package ID, capability ID, or intent ID;
- dependency solving;
- package execution after download;
- package signing or revocation enforcement.

The only current network reads are:

- explicit remote registry metadata requests through `specpm remote`;
- maintainer-reviewed public Git checkouts during public static index
  generation, pinned by exact commit revision.

## Trust Roots

Remote acquisition must not treat mutable labels as trust roots.

Trust for a future acquisition flow should be rooted in explicit immutable
inputs:

- registry base URL and registry API profile;
- package ID and version;
- archive format;
- archive digest algorithm and value;
- exact source revision where source checkout is involved;
- lockfile entry written by an explicit user action.

Readable labels such as branch names, tags, or release aliases can appear in
logs and user interfaces, but they are not sufficient for trust. If a label is
used for operator readability, the resolved immutable revision or digest must
still be verified.

## Future Acquisition Requirements

Before adding archive fetch, cache, or remote add behavior, the design must
define these steps:

1. Resolve metadata through the read-only registry API.
2. Select an exact package version.
3. Read the archive descriptor, including URL, format, size when available, and
   digest.
4. Download only from an allowed transport profile.
5. Verify the archive digest before indexing, caching, or locking it.
6. Validate package shape as data.
7. Write deterministic cache metadata and lockfile entries only after
   verification succeeds.
8. Never execute package content during acquisition, validation, caching, or
   lockfile generation.

The minimum future lock entry should record enough immutable data to reproduce
and audit the acquisition:

- package ID;
- version;
- registry base URL;
- archive URL;
- archive format;
- digest algorithm and digest value;
- resolved registry API version;
- acquisition timestamp or event metadata when the lock format defines it.

The cache layout must be deterministic and collision-resistant. A
content-addressed layout such as `sha256/<digest>.specpm.tgz` is acceptable in
principle, but the exact path is not normative until the lock/cache design is
accepted.

## Failure Modes

Remote acquisition must fail closed for:

- unsupported registry API version or registry profile;
- unsupported archive format;
- unsupported transport;
- missing digest;
- digest mismatch;
- cache collision;
- package validation failure;
- yanked package version unless an explicit policy allows it;
- deprecated package version when the command requires non-deprecated packages;
- lockfile mismatch between requested package metadata and resolved archive;
- mutable source reference without an exact revision where source checkout is
  involved.

Failures should be structured enough for downstream tools to display why the
package was not acquired without guessing from prose.

## Core vs Downstream

Remote acquisition can land in SpecPM core only if it stays within package
manager boundaries:

- exact metadata lookup;
- explicit package/version selection;
- digest verification;
- deterministic cache and lock updates;
- package validation as untrusted data.

Acquisition should remain downstream or enterprise-specific when it requires:

- private authentication policy;
- organization-specific allowlists;
- tenant authorization;
- signing or revocation infrastructure not yet specified by SpecPM;
- semantic package selection from natural language;
- graph reasoning or agent workflow execution.

## Non-Goals

This boundary does not add:

- `specpm publish`;
- public registry mutation APIs;
- package upload endpoints;
- dependency solving;
- signature verification policy;
- namespace ownership enforcement;
- semantic intent resolution;
- package execution;
- install scripts;
- prompt execution;
- agent runtime behavior.

Package content can describe desired outputs. Package content cannot command the
host.

## Source Contract

This document is policy evidence for future remote acquisition work. Runtime
implementation must not start before a concrete acquisition design references
this boundary and defines cache, lockfile, digest, and failure-mode behavior.
