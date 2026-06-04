# Registry Acceptance Decisions

Status: Draft
Scope: Machine-readable SpecPM maintainer decisions for public-index acceptance

## Purpose

`SpecPMRegistryAcceptanceDecision` records the maintainer decision that accepts,
rejects, withdraws, or overrides a producer-backed public-index proposal.

The record links a decision to proposal evidence. It does not make producer
receipts, producer preflight, validation reports, diagnostics, static previews,
or SpecHarvester output authoritative.

## Authority Boundary

Authority remains with SpecPM maintainer review.

Producer evidence can support a decision:

```text
producer evidence -> SpecPM maintainer review -> registry acceptance decision
```

Producer evidence must not replace a decision:

```text
producer receipt -> automatic registry acceptance
```

## Record Shape

```json
{
  "apiVersion": "specpm.decisions/v0",
  "kind": "SpecPMRegistryAcceptanceDecision",
  "schemaVersion": 1,
  "decisionId": "specpm-decision-2026-06-04-example-package-0.1.0",
  "status": "approved",
  "requiredFor": ["public_index_acceptance"],
  "subject": {
    "packageId": "example.package",
    "version": "0.1.0",
    "proposal": {
      "kind": "pull_request",
      "url": "https://github.com/0al-spec/SpecPM/pull/0"
    },
    "acceptedSourcePath": "public-index/accepted-packages.yml"
  },
  "maintainerReview": {
    "decisionBy": "SpecPM maintainer",
    "decidedAt": "2026-06-04T00:00:00Z",
    "reviewLocation": "https://github.com/0al-spec/SpecPM/pull/0",
    "summary": "Accepted after SpecPM validation and evidence review."
  },
  "producerEvidence": {
    "producerReceiptAuthority": "evidence_only",
    "producerReceiptPath": "public-index/generated/example.package/0.1.0/producer-receipt.json",
    "validationReportPath": "public-index/generated/example.package/0.1.0/validation-report.json",
    "diagnosticsPath": "public-index/generated/example.package/0.1.0/diagnostics.json",
    "proposalEvidenceLinks": "pull_request_body"
  },
  "outcome": {
    "acceptedManifestChanged": true,
    "publishOnMerge": true
  }
}
```

## Required Fields

- `apiVersion`: `specpm.decisions/v0`.
- `kind`: `SpecPMRegistryAcceptanceDecision`.
- `schemaVersion`: integer `1`.
- `decisionId`: stable decision identifier.
- `status`: one of `approved`, `rejected`, `override`, `withdrawn`, or
  `pending`.
- `requiredFor`: must include `public_index_acceptance`.
- `subject.packageId` and `subject.version`.
- `subject.proposal`.
- `maintainerReview.reviewLocation`.
- `producerEvidence.producerReceiptAuthority`: must be `evidence_only`.

## Status Semantics

- `pending`: maintainer decision is not complete.
- `approved`: maintainer accepted the package for public-index inclusion.
- `rejected`: maintainer rejected the proposal.
- `override`: maintainer accepted despite failed or missing producer evidence
  and recorded the reason in `maintainerReview.summary`.
- `withdrawn`: proposal was closed or superseded without acceptance.

Producer automation should start with
`registryAcceptanceDecision.status: external_required` in the proposal body.
The external record uses the statuses above after maintainer review.

## Storage

The first implementation may store decision records as pull request body
sections, review comments, workflow artifacts, or repository-local JSON files.
If records become repository-local files, they should live outside producer
receipts and generated candidate bundles.

## Non-Goals

This record does not:

- execute package content;
- run SpecHarvester;
- prove package trust by itself;
- replace SpecPM validation;
- replace accepted-source review;
- make `producer-receipt.json` an authority document.
