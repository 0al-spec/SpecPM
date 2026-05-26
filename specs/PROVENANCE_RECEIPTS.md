# SpecPM Provenance Receipt Schema and Audit Evidence Profile

Status: Draft
Updated: 2026-05-26
Scope: machine-readable provenance receipt shape and audit evidence profile

## Purpose

This document defines the draft `SpecPMProvenanceReceipt` shape for future
registry, acquisition, and trust verification work.

Receipts are evidence, not authority. A receipt can record what source,
archive, review, build, validation, trust policy, lifecycle, and deployment
evidence was observed for an exact package version. It does not make package
content trusted, does not execute package content, and does not replace archive
digest verification, signature verification, or maintainer review.

## Current Boundary

Current SpecPM does not generate provenance receipts. Current public `/v0`
metadata includes package source descriptors, archive digests, lifecycle state,
implementation build metadata, and static registry payloads, but no dedicated
receipt artifact.

This policy defines a schema contract for future receipt artifacts only. It
does not add:

- receipt generation;
- registry payload mutation;
- signature verification;
- revocation feed handling;
- lockfile changes;
- cache writes;
- package execution.

## Receipt Envelope

A receipt artifact should be JSON-compatible data with this top-level shape:

```yaml
apiVersion: specpm.receipts/v0
kind: SpecPMProvenanceReceipt
schemaVersion: 1
receiptProfile: public_static_index_build_v0
receiptId: specpm.core@0.2.0:sha256:<digest-prefix>
issuedAt: "2026-05-26T00:00:00Z"
subject: {}
source: {}
archive: {}
review: {}
build: {}
validation: {}
trust: {}
lifecycle: {}
audit: {}
```

Required top-level fields:

- `apiVersion`: receipt API family. The initial value is
  `specpm.receipts/v0`.
- `kind`: receipt kind. The initial value is `SpecPMProvenanceReceipt`.
- `schemaVersion`: integer schema version within the API family.
- `receiptProfile`: named profile that defines required nested fields.
- `receiptId`: deterministic identifier for the receipt artifact.
- `issuedAt`: UTC timestamp string for the receipt event.
- `subject`: package version or registry snapshot being described.
- `source`: source location and immutable source identity.
- `archive`: deterministic package archive descriptor.
- `review`: maintainer review evidence.
- `build`: build or generation evidence.
- `validation`: package validation result summary.
- `trust`: signing, revocation, and verification policy state.
- `lifecycle`: visible, deprecated, yanked, revoked, or removed state.
- `audit`: external evidence references and retention hints.

## Public Static Index Profile

The initial public static profile is `public_static_index_build_v0`.

### `subject`

Required fields:

- `packageId`
- `version`
- `registryProfile`

The `registryProfile` value for the current public static index is
`public_static_index`.

### `source`

Required fields:

- `kind`: `local_path` or `git`.
- `path`: package path inside the source root.

Required when `kind` is `git`:

- `repository`
- `ref`
- `revision`

Mutable `ref` is operator-readable evidence only. Trust must come from exact
`revision` and archive digest.

### `archive`

Required fields:

- `format`
- `digest.algorithm`
- `digest.value`

Recommended fields:

- `size`
- `url`

The digest must describe the deterministic package archive bytes, not a source
tree, rendered web page, or registry UI view.

### `review`

Required fields:

- `kind`: `pull_request`, `issue`, `commit`, or `manual`.
- `decision`: `accepted`, `rejected`, `merged`, `superseded`, or `needs-info`.

Recommended fields:

- `url`
- `commit`
- `reviewedAt`
- `reviewer`

Review evidence records the acceptance path. It is not a signing identity by
itself.

### `build`

Required fields:

- `provider`
- `workflow`
- `revision`

Recommended fields:

- `runId`
- `runAttempt`
- `job`
- `builder`

Build evidence records where registry metadata or archives were generated. It
does not prove package authorship.

### `validation`

Required fields:

- `status`: `valid`, `warning`, or `invalid`.
- `warningCount`
- `errorCount`

Recommended fields:

- `reportDigest`
- `validatedAt`
- `validatorVersion`

Receipts for accepted public packages should not report `invalid` validation
status unless the receipt profile is explicitly documenting rejection evidence.

### `trust`

Required fields:

- `policy`
- `signatureRequired`
- `signatureStatus`
- `revocationStatus`

Recommended `signatureStatus` values:

- `not_applicable`
- `missing`
- `verified`
- `invalid`
- `expired`
- `revoked`

Recommended `revocationStatus` values:

- `not_checked`
- `not_revoked`
- `revoked`
- `unknown`

`signatureStatus: verified` is only valid when the profile defines a trust root
and verification policy.

### `lifecycle`

Required fields:

- `state`: `visible`, `deprecated`, `yanked`, `revoked`, or `removed`.
- `yanked`
- `deprecated`
- `revoked`

`state` is the summary state. Boolean fields preserve compatibility with
current registry lifecycle metadata.

### `audit`

Required fields:

- `evidence`: list of evidence references.

Recommended evidence reference fields:

- `kind`
- `url`
- `revision`
- `digest`
- `retention`

Audit evidence references should be stable enough for later reviewers to
explain why a package was accepted, generated, deployed, deprecated, yanked, or
revoked.

## Extension Rules

Profiles may add fields under `x-` extension keys. Consumers should preserve
unknown `x-` fields when copying receipts, but they must not treat unknown
extensions as verified trust.

Enterprise profiles may require private audit references, internal identity
provider references, or tenant-specific retention rules. Those requirements
must not be required by the public static profile unless the public profile is
explicitly revised.

## Failure Interpretation

Absence of a receipt means no receipt evidence is available. It does not prove
that the package is invalid.

If a policy requires receipts, future acquisition or verification runtime must
fail closed when:

- the receipt is missing;
- the receipt `apiVersion`, `kind`, or `schemaVersion` is unsupported;
- subject package ID or version differs from selected package metadata;
- archive digest differs from the downloaded archive descriptor;
- source revision differs from accepted source metadata;
- lifecycle state is `revoked` or `removed`;
- trust policy requires a verified signature and the receipt does not show one.

## Example Fixture

The non-normative example fixture is
`tests/fixtures/provenance_receipts/public-static-receipt.example.json`.

The fixture demonstrates the shape only. It is not a generated public registry
receipt and must not be used as trust evidence.

## Source Contract

This document is policy evidence for future provenance receipt work. Runtime
receipt generation, receipt publication, receipt verification, or registry
payload changes must reference this boundary and define implementation-specific
failure behavior before landing.
