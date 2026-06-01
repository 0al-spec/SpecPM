# SpecPM Remote Package Acquisition Boundary

Status: Draft
Updated: 2026-06-01
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

## Acquisition State Machine

Future acquisition must keep state transitions explicit. A command may stop at
any earlier state, but it must not claim a later state until the required
checks for that state have succeeded.

| State | Meaning | Required before entering |
| --- | --- | --- |
| `observed_metadata` | Registry `/v0` metadata was read. | Registry status and subject payload are valid for the supported API family. |
| `selected_version` | One exact package version was chosen. | Selection is explicit or uniquely resolved by documented policy. |
| `downloaded_archive` | Archive bytes were fetched to a temporary location. | URL, format, size policy, transport policy, and digest descriptor are known. |
| `verified_archive` | Archive bytes match the declared digest. | Digest algorithm is supported and digest comparison succeeds. |
| `validated_package` | Archive content validates as SpecPM package data. | Archive unpacking is constrained and `specpm validate`-equivalent checks pass. |
| `cached_package` | Verified bytes and metadata are committed to cache. | Cache path is content-addressed or otherwise collision-resistant. |
| `locked_package` | Project state records the acquired package. | Cache commit succeeded and lock entry records immutable acquisition evidence. |

The state machine prevents silent coercion. For example, a downloaded archive is
not acquired, a verified digest is not publisher trust, and a cached package is
not executable host authority.

## Cache and Lock Invariants

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

Cache and lock writes must be atomic from the user's perspective:

- Downloaded bytes should first be written to a temporary file outside the
  committed cache location.
- Digest verification must happen before moving bytes into the committed cache.
- Cache metadata must not be written for unverified bytes.
- Lockfile entries must not be written until archive verification and package
  validation both succeed.
- A failed acquisition must leave either the previous valid state or removable
  temporary files, not a partially trusted cache entry.
- Re-acquiring the same digest should be idempotent.
- Re-acquiring the same `package_id@version` with a different digest must fail
  unless an explicit lifecycle or replacement policy has already been accepted.

## Trust, Signatures, and Receipts

Digest verification is required for acquisition, but it proves only byte
integrity against the registry metadata. It does not prove publisher authority,
namespace ownership, revocation status, or policy approval.

Future acquisition must compose with, but not silently invent, stronger trust
layers:

- If signature verification is required by policy, the acquisition runtime must
  fail closed until `specs/PACKAGE_SIGNING_REVOCATION.md` has an implemented
  verifier and trust policy.
- If provenance receipts are required by policy, the acquisition runtime must
  record and verify the expected receipt subject before lockfile mutation.
- If no signature or receipt policy is configured, acquisition may still verify
  digests and validate package shape, but it must not claim publisher trust.
- Revoked or yanked subjects must remain visible for audit, but acquisition
  eligibility must be an explicit policy decision.

## Retry and Partial Write Behavior

Retries are allowed only before trust-affecting state is committed.

- Retrying metadata reads or archive downloads is acceptable when the command
  records the final observed registry evidence.
- Retrying after a digest mismatch must fetch bytes again into a fresh
  temporary file; it must not reuse the mismatched archive.
- Retrying cache commits must verify that an existing cache entry has the same
  digest and format before treating it as success.
- Retrying lockfile writes must preserve deterministic ordering and must not
  duplicate package entries.
- Network timeouts, interrupted downloads, and process termination should leave
  temporary files that can be safely removed or resumed only after digest
  verification.

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

Minimum structured failure categories:

- `registry_unavailable`;
- `unsupported_registry_api`;
- `unsupported_registry_profile`;
- `ambiguous_selection`;
- `unsupported_archive_format`;
- `unsupported_transport`;
- `missing_digest`;
- `digest_mismatch`;
- `cache_collision`;
- `validation_failed`;
- `lifecycle_blocked`;
- `lockfile_mismatch`;
- `trust_policy_unmet`;
- `partial_write_recovered`;
- `mutable_source_ref`.

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
