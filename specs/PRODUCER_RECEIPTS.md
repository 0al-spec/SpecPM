# Spec Producer Provenance Receipt Contract

Status: Draft
Updated: 2026-05-26
Scope: producer-side provenance receipts for generated SpecPackage candidates

## Purpose

This document defines the draft `SpecPMProducerReceipt` shape for tools that
generate or assist `SpecPackage` and `BoundarySpec` content.

Producer receipts are evidence, not authority. A producer receipt records which
tool, inputs, configuration, validation result, output files, diagnostics, and
review handoff produced a package candidate. It does not make generated package
content trusted, does not prove runtime behavior, does not replace maintainer
review, and does not require SpecPM to run the producer.

The first expected downstream producer is SpecHarvester, but the contract is
tool-neutral. Any generator may emit the same profile when it produces
reviewable SpecPM package candidates.

## Relationship to Registry Receipts

Producer receipts describe package creation:

```text
source repo / docs / analyzer output / generator config
        -> producer
        -> specpm.yaml + specs/*.spec.yaml + evidence
```

Registry provenance receipts describe package publication:

```text
SpecPackage
        -> SpecPM validate / pack / public index generation
        -> static registry artifacts
```

The two receipts may form an audit chain, but they have different authority.
SpecPM can publish a package that has no producer receipt, and a producer
receipt does not force SpecPM to accept a generated package.

## Current Boundary

Current SpecPM does not generate, validate, require, or index producer
receipts. This policy defines a schema contract for external producer tools and
future optional SpecPM validation only.

This document does not add:

- producer execution;
- LLM prompt execution;
- analyzer execution;
- automatic package acceptance;
- registry publication;
- signature verification;
- package trust decisions;
- remote input fetching;
- cache, lockfile, or registry payload mutation.

## Receipt Envelope

A producer receipt artifact should be JSON-compatible data with this top-level
shape:

```yaml
apiVersion: specpm.receipts/v0
kind: SpecPMProducerReceipt
schemaVersion: 1
receiptProfile: generated_spec_package_v0
receiptId: example.generated_spec@0.1.0:producer:sha256:<digest-prefix>
issuedAt: "2026-05-26T00:00:00Z"
subject: {}
producer: {}
inputs: []
configuration: {}
outputs: []
validation: {}
diagnostics: []
review: {}
privacy: {}
audit: {}
```

Required top-level fields:

- `apiVersion`: receipt API family. The initial value is
  `specpm.receipts/v0`.
- `kind`: receipt kind. The initial value is `SpecPMProducerReceipt`.
- `schemaVersion`: integer schema version within the API family.
- `receiptProfile`: named profile that defines required nested fields.
- `receiptId`: deterministic identifier for the receipt artifact.
- `issuedAt`: UTC timestamp string for the generation event.
- `subject`: generated package candidate being described.
- `producer`: generator identity, version, and source revision.
- `inputs`: source material observed by the generator.
- `configuration`: generation mode, analyzers, templates, and model metadata.
- `outputs`: generated files and their digests.
- `validation`: validation performed by the producer or handoff workflow.
- `diagnostics`: warnings, skipped inputs, or generation limitations.
- `review`: maintainer or reviewer handoff evidence.
- `privacy`: redaction and secret-handling claims.
- `audit`: external evidence references and retention hints.

## Generated Spec Package Profile

The initial producer profile is `generated_spec_package_v0`.

### `subject`

Required fields:

- `packageId`
- `packageVersion`
- `packageApiVersion`
- `packageRoot`

Recommended fields:

- `boundarySpecs`
- `candidateStatus`

`candidateStatus` should be one of `draft`, `review-ready`, `accepted`, or
`rejected`. It is handoff status only and must not be treated as registry
acceptance.

### `producer`

Required fields:

- `name`
- `version`

Recommended fields:

- `repository`
- `revision`
- `workflow`
- `runId`

When the producer is built from Git, `revision` should be an exact
40-character commit SHA. Mutable branch or tag names may be recorded for
operator readability, but trust must come from exact revisions and output
digests.

### `inputs`

Each input reference should include:

- `kind`
- `path` or `url`
- `digest.algorithm`
- `digest.value`
- `redaction`

Recommended `kind` values:

- `source_tree`
- `source_file`
- `documentation`
- `package_manifest`
- `public_interface_index`
- `manual_note`
- `generator_prompt`
- `template`
- `config`
- `previous_spec`

Input receipts must not store raw secrets, private keys, access tokens,
credentials, recovery codes, or confidential source text that should not be
redistributed. When an input cannot be disclosed, the producer should record a
digest, redaction reason, and retention pointer instead of embedding the raw
content.

### `configuration`

Required fields:

- `mode`

Recommended fields:

- `analyzers`
- `templates`
- `model`
- `deterministic`
- `parametersDigest`

`deterministic: false` is valid for LLM-assisted generation. In that case, the
receipt records an observation of the run, not a reproducibility guarantee.

### `outputs`

Each output reference should include:

- `path`
- `kind`
- `digest.algorithm`
- `digest.value`

Expected output kinds include:

- `specpm_manifest`
- `boundary_spec`
- `evidence`
- `foreign_artifact`
- `producer_receipt`

The output digest must describe the generated file bytes after redaction and
normalization performed by the producer.

### `validation`

Required fields:

- `status`: `not_run`, `valid`, `warning`, or `invalid`.
- `warningCount`
- `errorCount`

Recommended fields:

- `validator`
- `validatorVersion`
- `validatedAt`
- `reportDigest`

If the producer ran `specpm validate`, the receipt should record the validator
version and validation report digest. It should not embed long validation logs
unless the profile is explicitly extended for that purpose.

### `diagnostics`

Diagnostics should be compact, reviewable entries with:

- `severity`
- `code`
- `message`

Recommended severity values are `info`, `warning`, and `error`.

### `review`

Required fields:

- `handoff`: `none`, `pull_request`, `issue`, `commit`, or `manual`.
- `required`

Recommended fields:

- `url`
- `reviewer`
- `reviewedAt`

Generated packages should normally set `required: true`. A producer receipt is
not a substitute for maintainer review.

### `privacy`

Required fields:

- `secretsIncluded`
- `redactions`

`secretsIncluded` must be `false` for receipts intended for public SpecPM
review or public registry submission.

### `audit`

Required fields:

- `evidence`: list of evidence references.

Recommended evidence reference fields:

- `kind`
- `path`
- `url`
- `digest`
- `retention`

Audit evidence references should be stable enough for a later reviewer to
explain why a generated candidate changed between producer runs.

## Carrying Receipts with Generated Packages

A producer may place the receipt inside the generated package, for example:

```text
evidence/generated-spec-receipt.json
```

Until SpecPM accepts a dedicated evidence kind or foreign artifact role for
producer receipts, generated packages may reference the receipt as ordinary
package data through an existing package-local path. For example:

```yaml
foreignArtifacts:
  - id: generated_spec_receipt
    role: documentation
    path: evidence/generated-spec-receipt.json
```

This preserves the receipt in package archives without requiring SpecPM to
interpret or trust it.

## SpecHarvester Requirements

A SpecHarvester implementation of this profile should:

- emit `apiVersion: specpm.receipts/v0`;
- emit `kind: SpecPMProducerReceipt`;
- emit `receiptProfile: generated_spec_package_v0`;
- record the generated package ID, version, API version, and root path;
- record SpecHarvester version and exact source revision when available;
- record source, analyzer, template, prompt, and configuration inputs by digest;
- record generated `specpm.yaml`, `specs/*.spec.yaml`, and evidence file
  digests;
- record validation status when `specpm validate` was run;
- record diagnostics for skipped files, unsupported languages, model
  uncertainty, or lossy summaries;
- set `privacy.secretsIncluded` to `false` for public handoff receipts;
- avoid embedding private prompts, private source text, tokens, credentials, or
  local machine paths that should not leave the producer environment.

## Extension Rules

Profiles may add fields under `x-` extension keys. Consumers should preserve
unknown `x-` fields when copying receipts, but they must not treat unknown
extensions as verified trust.

Producer-specific fields should stay under namespaced extension keys such as
`x-specharvester` unless they are promoted into the common profile.

## Failure Interpretation

Absence of a producer receipt means no producer evidence is available. It does
not prove that a package is invalid.

If a future policy requires producer receipts, validation or acquisition runtime
must fail closed when:

- the receipt is missing;
- the receipt `apiVersion`, `kind`, or `schemaVersion` is unsupported;
- subject package ID, version, or API version differs from selected package
  metadata;
- an output digest differs from the package file bytes;
- a required input digest is missing or malformed;
- `privacy.secretsIncluded` is `true` for a public handoff;
- validation status is `invalid` and the policy requires accepted candidates
  only.

## Example Fixture

The non-normative example fixture is
`tests/fixtures/provenance_receipts/generated-spec-package-receipt.example.json`.

The fixture demonstrates the shape only. It is not a generated SpecHarvester
receipt and must not be used as trust evidence.

## Source Contract

This document is policy evidence for future producer receipt work. Runtime
producer receipt generation, validation, publication, or registry behavior must
reference this boundary and define implementation-specific failure behavior
before landing.
