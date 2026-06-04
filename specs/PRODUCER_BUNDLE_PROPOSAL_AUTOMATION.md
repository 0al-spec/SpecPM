# Producer Bundle Proposal Automation Contract

Status: Draft
Scope: SpecHarvester-to-SpecPM pull request body contract for producer-backed accepted-source proposals

## Purpose

This contract defines the machine-readable pull request body blocks that a
producer such as SpecHarvester should include when it opens or updates a
SpecPM accepted-source proposal.

The contract is consumer-side. It lets SpecPM CI and maintainers review
producer evidence without running SpecHarvester, executing package content, or
treating producer output as registry authority.

## Required Pull Request Blocks

A producer-backed proposal pull request should include two fenced JSON blocks:

1. `producerEvidenceLinks`
2. `registryAcceptanceDecision`

The blocks may be surrounded by human-readable Markdown, but the JSON payloads
must remain parseable by `specpm producer-bundle preflight`.

## `producerEvidenceLinks`

`producerEvidenceLinks` is an array of evidence link objects.

Required roles:

- `accepted_source_bundle`
- `manifest`
- `boundary_spec`
- `producer_receipt`
- `validation_report`
- `diagnostics`
- `accepted_source_diff`

Optional roles:

- `producer_preflight`
- `static_viewer`

Each entry must include:

- `role`: one of the evidence roles above.
- `path`: non-empty string. `pull_request` paths may be symbolic, but must
  still be present.
- `pathScope`: one of `repo_relative`, `candidate_bundle`,
  `workflow_artifact`, or `pull_request`.
- `required`: `true` for required roles and `false` for optional roles.
- `status`: `expected`, `present`, or `missing`.

Entries may include `digest` values using `sha256:<hex>` when the linked path
is a file available under the preflight root.

## `registryAcceptanceDecision`

`registryAcceptanceDecision` records that public index acceptance is still an
external maintainer decision.

For producer-opened proposals the initial status should be:

```json
{
  "registryAcceptanceDecision": {
    "status": "external_required",
    "requiredFor": ["public_index_acceptance"],
    "authority": "SpecPM maintainer review",
    "recordKind": "SpecPMRegistryAcceptanceDecision",
    "recordLocation": "SpecPM pull request or accepted-source review record",
    "producerReceiptAuthority": "evidence_only"
  }
}
```

Producers must not set this status to `approved`. Approval belongs to SpecPM
maintainer review or to a future explicit acceptance decision record.

## Minimal Proposal Shape

```json
{
  "producerEvidenceLinks": [
    {
      "role": "accepted_source_bundle",
      "path": "public-index/generated/example.package/0.1.0",
      "pathScope": "repo_relative",
      "required": true,
      "status": "expected"
    },
    {
      "role": "manifest",
      "path": "public-index/generated/example.package/0.1.0/specpm.yaml",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present",
      "digest": "sha256:<64-hex>"
    },
    {
      "role": "boundary_spec",
      "path": "public-index/generated/example.package/0.1.0/specs/example.spec.yaml",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present"
    },
    {
      "role": "producer_receipt",
      "path": "public-index/generated/example.package/0.1.0/producer-receipt.json",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present"
    },
    {
      "role": "validation_report",
      "path": "public-index/generated/example.package/0.1.0/validation-report.json",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present"
    },
    {
      "role": "diagnostics",
      "path": "public-index/generated/example.package/0.1.0/diagnostics.json",
      "pathScope": "repo_relative",
      "required": true,
      "status": "present"
    },
    {
      "role": "accepted_source_diff",
      "path": "pull-request-diff",
      "pathScope": "pull_request",
      "required": true,
      "status": "expected"
    }
  ],
  "registryAcceptanceDecision": {
    "status": "external_required",
    "requiredFor": ["public_index_acceptance"],
    "authority": "SpecPM maintainer review",
    "recordKind": "SpecPMRegistryAcceptanceDecision",
    "recordLocation": "SpecPM pull request or accepted-source review record",
    "producerReceiptAuthority": "evidence_only"
  }
}
```

## Automation Expectations

SpecHarvester proposal automation should:

- include or link producer receipt, validation report, diagnostics report,
  producer preflight report, static viewer evidence when available, and accepted
  source diff evidence;
- keep optional evidence as `status: missing` rather than omitting the role
  when it is expected but unavailable;
- keep `registryAcceptanceDecision.producerReceiptAuthority` set to
  `evidence_only`;
- leave acceptance, override, and rejection decisions to SpecPM maintainers;
- mention matching SpecPM/SpecHarvester fixture updates when drift-sensitive
  fields change.

SpecPM proposal preflight may fail malformed or incomplete required evidence,
but a passing preflight remains review evidence only.

## Non-Goals

This contract does not:

- make SpecHarvester a registry authority;
- let producer automation approve public index acceptance;
- require SpecPM to execute producer tools;
- require cross-repository mutable branch checkouts;
- replace SpecPM validation, accepted-source review, or maintainer decision.
