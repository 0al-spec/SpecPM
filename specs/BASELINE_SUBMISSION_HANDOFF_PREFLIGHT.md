# Baseline Submission Handoff Preflight

Status: Draft
Updated: 2026-06-13
Scope: SpecPM consumer-side validation for SpecHarvester first-submission and
seeded-baseline handoff evidence

## Purpose

`SpecHarvesterBaselineSubmissionHandoff` is producer evidence for repositories
that do not yet have current SpecPM generated artifacts. In that state SpecPM
cannot issue a normal generated-candidate refresh decision because there is no
baseline to compare against.

SpecPM therefore treats the handoff as an intake artifact:

```text
SpecHarvester fresh package-set output
  -> SpecPM prepare-refresh-decision reports missing generated baseline
  -> SpecHarvesterBaselineSubmissionHandoff
  -> SpecPM preflight-baseline-submission
  -> maintainer first-submission / seed-baseline / reject decision
```

The handoff is not registry authority.

## Command

```bash
specpm producer-bundle preflight-baseline-submission \
  --body <baseline-submission-handoff.json> \
  --root <handoff-artifact-root> \
  --json
```

`--body` may be a raw JSON file or Markdown containing a JSON block.

`--root` is optional. Without it, SpecPM can validate envelope shape and
authority fields, but it emits a warning because linked input digests cannot be
verified.

## Verified Contract

The preflight emits `SpecPMBaselineSubmissionHandoffPreflightReport` and checks:

- `apiVersion: spec-harvester.baseline-submission-handoff/v0`;
- `kind: SpecHarvesterBaselineSubmissionHandoff`;
- `schemaVersion: 1`;
- `status: first_submission_required` with
  `reason: missing_current_generated_baseline`, or
  `status: baseline_review_required` with
  `reason: specpm_prepare_report_not_provided`;
- `source.repository` and 40-character `source.revision`;
- `packageSet.id`, `candidateCount`, `memberPackageIds`, and
  `contractFileCount`;
- `specpmPrepareReport.diagnosticCode` equals
  `refresh_decision_prepare_current_contract_files_missing`;
- missing-baseline diagnostic counts for confirmed first-submission cases;
- `baselineWorkflow.blockedRefreshDecision: true`;
- maintainer actions `first_submission_review`, `seed_baseline`, and
  `reject_or_request_regeneration`;
- authority flags `producerEvidenceAuthority: evidence_only`,
  `registryAuthority: SpecPM maintainer review`, `noRegistryMutation: true`,
  and `notRefreshDecision: true`;
- non-goals covering acceptance, publication, baseline mutation, refresh
  decision emission, source repository execution, and package-manager execution.

When `--root` is provided, the preflight also reads linked inputs under that
root and verifies SHA-256 digests:

- `inputs.freshCandidateRefreshRun` must point to
  `SpecHarvesterFreshCandidateRefreshRun` with matching source, package-set id,
  member ids, candidate count, contract file count, and `schemaVersion: 1`;
- `inputs.specpmPrepareReport` must point to
  `SpecPMGeneratedCandidateRefreshDecisionPrepareReport` when the handoff
  claims `missing_baseline`, and the report's missing-baseline diagnostic count
  and decision summary must match the handoff.

Absolute input paths are accepted only when they resolve inside `--root`.

## Maintainer Decision Boundary

A passing preflight means the handoff is internally consistent review evidence.
It does not seed the baseline. It also does not:

- accept packages;
- accept relations;
- seed `public-index/generated`;
- update `public-index/curated`;
- emit `SpecPMGeneratedCandidateRefreshDecision`;
- publish public registry metadata;
- run SpecHarvester or source repository code.

Short form: it does not accept packages or mutate registry state.

Maintainers still choose one of:

- `first_submission_review`: review the generated package-set as a new
  submission;
- `seed_baseline`: create an explicit generated baseline only after review;
- `reject_or_request_regeneration`: reject or ask the producer to regenerate.

## Relationship To Refresh Decisions

`preflight-refresh-decision` validates an existing
`SpecPMGeneratedCandidateRefreshDecision`.

`preflight-baseline-submission` validates why such a decision cannot yet exist.
It is the bridge between fresh generated evidence and maintainer-controlled
baseline seeding.

## Non-Goals

This policy does not add automatic first-submission acceptance, automatic
baseline seeding, producer-owned registry updates, package-set materialization,
relation acceptance, package execution, or request-time registry mutation.
