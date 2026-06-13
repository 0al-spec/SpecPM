# Baseline Submission Handoff Preflight

Validate SpecHarvester first-submission and seeded-baseline handoff evidence
without turning it into registry authority.

## Overview

`SpecHarvesterBaselineSubmissionHandoff` is used when SpecHarvester produced a
fresh package-set candidate, but SpecPM cannot prepare a normal refresh
decision because the current generated baseline is missing.

Run the consumer-side preflight before using the handoff in maintainer review:

```bash
specpm producer-bundle preflight-baseline-submission \
  --body <baseline-submission-handoff.json> \
  --root <handoff-artifact-root> \
  --json
```

The command emits `SpecPMBaselineSubmissionHandoffPreflightReport`.

## What It Checks

The preflight verifies:

- `apiVersion`, `kind`, and `schemaVersion`;
- `first_submission_required` versus `baseline_review_required` status/reason
  consistency;
- source repository and 40-character source revision;
- package-set id, member ids, candidate count, and contract file count;
- missing-baseline diagnostic metadata;
- maintainer actions `first_submission_review`, `seed_baseline`, and
  `reject_or_request_regeneration`;
- authority flags `evidence_only`, `noRegistryMutation: true`, and
  `notRefreshDecision: true`;
- linked `SpecHarvesterFreshCandidateRefreshRun` and
  `SpecPMGeneratedCandidateRefreshDecisionPrepareReport` digests when `--root`
  is provided.

## Boundary

A passing report is review evidence only. It does not accept packages, accept
relations, seed `public-index/generated`, update curated artifacts, emit a
refresh decision, publish registry metadata, or execute producer tools.
In other words, it does not seed a baseline; it only gives maintainers a checked
handoff record for first-submission review.

See `specs/BASELINE_SUBMISSION_HANDOFF_PREFLIGHT.md` for the full policy.
