# Generated Candidate Refresh Decision Policy

Status: Draft
Updated: 2026-06-12
Scope: SpecPM public index refresh decisions for producer-generated candidates
and maintainer-curated accepted artifacts

## Purpose

This document defines how maintainers decide whether a fresh producer run
requires a registry update.

The short rule is:

```text
fresh generated candidate -> comparison evidence
refresh decision -> update/no-update record
curated accepted artifact -> registry source
```

A new SpecHarvester run is useful even when it does not change accepted
registry metadata. The run may prove that current curated artifacts are still
good enough, that the generated candidate is byte-equivalent to the existing
producer evidence, or that only producer receipts and advisory reports changed.

That outcome should be recorded as an explicit no-op decision instead of being
treated as unfinished work.

## Decision Record Shape

The review outcome should be captured as a machine-readable
`SpecPMGeneratedCandidateRefreshDecision` when a fresh generated candidate is
compared with current registry sources.

The record reuses the shared SpecPM decision envelope
`apiVersion: specpm.decisions/v0`. It uses a distinct
`kind: SpecPMGeneratedCandidateRefreshDecision` so tooling can recognize the
refresh/no-update decision without introducing a separate decision API family.

Minimum shape:

```json
{
  "apiVersion": "specpm.decisions/v0",
  "kind": "SpecPMGeneratedCandidateRefreshDecision",
  "schemaVersion": 1,
  "subject": {
    "packageId": "xyflow.workspace",
    "version": "0.1.0",
    "acceptedArtifact": "public-index/curated/xyflow.workspace/0.1.0",
    "currentGeneratedArtifact": "public-index/generated/xyflow.workspace/0.1.0",
    "freshGeneratedArtifact": ".smoke/xyflow-registry-update-eval/package-set/xyflow.workspace"
  },
  "decision": {
    "status": "no_update_required",
    "updateNeeded": false,
    "reason": "no_contract_delta",
    "supportingReasons": [
      "same_source_revision",
      "generated_contract_bytes_unchanged",
      "curated_artifact_remains_stronger",
      "producer_receipt_only_delta",
      "immutable_generated_candidate"
    ]
  },
  "comparison": {
    "sourceRevisionChanged": false,
    "acceptedContractChanged": false,
    "generatedContractChanged": false,
    "capabilitiesChanged": false,
    "relationsChanged": false,
    "evidenceChanged": false,
    "receiptOnlyChanged": true
  },
  "authority": {
    "producerEvidenceAuthority": "evidence_only",
    "registryAuthority": "maintainer_review_required"
  }
}
```

The decision record is review evidence. It is not registry authority by itself
and does not mutate `public-index/accepted-packages.yml`,
`public-index/generated`, or `public-index/curated`.

## Status Values

`decision.status` must use one of these values:

- `no_update_required`: the fresh run does not justify a registry update.
- `curated_update_required`: accepted curated metadata should change through a
  reviewed curated artifact diff.
- `new_generated_candidate_required`: the producer output should be added as a
  new immutable evidence artifact before review can proceed.
- `new_package_version_required`: the package contract changed enough that the
  package version should advance instead of silently replacing the current
  accepted version.
- `manual_review_required`: the comparison found ambiguity that cannot be
  classified mechanically.

`decision.updateNeeded` must match `decision.status`. It is `false` only for
`no_update_required`.

## No-Update Reasons

For `status: no_update_required`, `decision.reason` should be
`no_contract_delta`.

Maintainers should add one or more `supportingReasons`:

- `same_source_revision`: the fresh run used the same upstream source revision
  as the current accepted review.
- `generated_contract_bytes_unchanged`: contract-bearing generated files are
  byte-equivalent to the current generated evidence.
- `curated_artifact_remains_stronger`: the maintainer-curated accepted artifact
  is still more precise, safer, or better reviewed than the fresh generated
  candidate.
- `producer_receipt_only_delta`: only producer receipts, run IDs, timestamps,
  diagnostics envelopes, or advisory quality reports changed.
- `immutable_generated_candidate`: changing the existing generated candidate in
  place would violate producer evidence immutability.

Receipt churn, local run paths, new quality reports, and other advisory
producer metadata are not accepted contract deltas by themselves.

## Comparison Rules

Maintainers should compare these surfaces before opening a registry update PR:

1. Source revision and package identity.
2. Accepted curated contract text: summaries, capabilities, intent IDs,
   constraints, evidence wording, package boundary wording, and
   `preview_only` posture.
3. Generated contract files: `specpm.yaml` and `specs/*.spec.yaml`.
4. Accepted package relations and package-set membership.
5. Evidence links and `foreignArtifacts`.
6. Producer receipts, diagnostics, validation reports, quality reports, and
   handoff reports.

Only items 1 through 5 can normally justify an accepted registry update. Item 6
is provenance or review evidence unless maintainers explicitly decide that it
changes accepted evidence requirements.

## Update Triggers

Open a targeted registry update PR when the comparison finds:

- a changed upstream source revision that affects accepted claims or evidence;
- changed accepted capabilities, intent IDs, constraints, summaries, or package
  boundaries;
- changed accepted relation endpoints, relation types, or package-set
  membership;
- stronger or weaker evidence that changes the accepted claim support;
- a needed version bump for the package contract;
- a maintainer decision to replace or supersede a previous curated artifact.

Do not open a registry update PR merely because:

- a producer receipt ID changed;
- a local output path changed;
- an advisory quality report is newly available;
- the fresh run reproduced the same generated contract bytes;
- the current curated artifact remains the accepted registry source.

## Generated Candidate Immutability

`public-index/generated/<package_id>/<version>` is producer evidence. Do not
edit existing generated candidates in place to reflect a fresh run.

If a fresh generated candidate is meaningfully different and worth retaining,
store it as new evidence or create a reviewed successor candidate path/version.
If the accepted package should change, update the maintainer-curated artifact
under `public-index/curated/<package_id>/<version>` or create a new accepted
package version.

## Xyflow No-Op Example

A fresh real `xyflow` package-set run against source revision
`a58568f11bc0e1a1bdca1b3549e959e2e1ca0cdd` produced the same four package
candidates and three `contains` relations as the current generated evidence:

```text
xyflow.workspace
xyflow.react
xyflow.svelte
xyflow.system
```

The fresh `specpm.yaml`, `specs/*.spec.yaml`, `harvest.json`,
`diagnostics.json`, and `validation-report.json` files were byte-equivalent to
the current `public-index/generated/xyflow.*` evidence. Only
`producer-receipt.json` changed, and the fresh run emitted an additional
`author-ready-draft-quality-report.json`.

The correct decision is:

```text
status: no_update_required
updateNeeded: false
reason: no_contract_delta
supportingReasons:
  - same_source_revision
  - generated_contract_bytes_unchanged
  - curated_artifact_remains_stronger
  - producer_receipt_only_delta
  - immutable_generated_candidate
```

That decision preserves the value of the new SpecHarvester quality machinery:
it proves the current registry state is stable and avoids churning accepted
metadata when there is no meaningful package contract delta.

A complete machine-readable example is stored in:

```text
tests/fixtures/refresh_decisions/xyflow-no-update.example.json
```

The fixture uses the shared `apiVersion: specpm.decisions/v0` decision envelope,
records all four `xyflow` package-set members, cites the current curated and
generated artifact paths, and snapshots the generated contract-file digests
used to justify `updateNeeded: false`.

## Prepare Helper

SpecPM can prepare a draft refresh decision by comparing a fresh generated
candidate tree with the current registry evidence:

```bash
specpm producer-bundle prepare-refresh-decision \
  --root . \
  --fresh-generated-root <fresh-public-index-generated-root> \
  --package xyflow.workspace \
  --package xyflow.react \
  --package xyflow.svelte \
  --package xyflow.system \
  --package-id xyflow.workspace \
  --version 0.1.0 \
  --source-repository https://github.com/xyflow/xyflow \
  --source-revision <40-char-source-sha> \
  --output refresh-decision.json \
  --json
```

The command emits `SpecPMGeneratedCandidateRefreshDecisionPrepareReport` and can
write the prepared `SpecPMGeneratedCandidateRefreshDecision` with `--output`.
It compares only contract-bearing generated files (`specpm.yaml` and
`specs/*.spec.yaml`), records current generated contract-file SHA-256 digests,
checks the prepared decision with the same consumer-side preflight rules, and
keeps the output read-only review evidence.

If fresh and current generated contract files match, the draft decision uses
`status: no_update_required`, `updateNeeded: false`, and
`reason: no_contract_delta`. If contract files, source revisions, or accepted
artifact assumptions differ, the draft uses `manual_review_required` and
`updateNeeded: true`; it still does not mutate curated artifacts, generated
artifacts, relations, or registry metadata.

## CI Artifact

The manual `.github/workflows/refresh-decision-prepare.yml` workflow runs the
same prepare helper through `workflow_dispatch` and uploads three review
artifacts:

- `refresh-decision.json`
- `prepare-report.json`
- `preflight-report.json`

The workflow defaults to the current `xyflow` package-set no-op comparison, but
maintainers can override package IDs, version, source repository, source
revision, fresh generated root, and run label. It has `contents: read`
permissions, does not require write credentials, and does not mutate accepted
packages, generated candidates, accepted relations, or registry metadata.

## Consumer-Side Preflight

SpecPM can verify a generated candidate refresh decision before maintainers use
it as review evidence:

```bash
specpm producer-bundle preflight-refresh-decision \
  --body tests/fixtures/refresh_decisions/xyflow-no-update.example.json \
  --root . \
  --json
```

The command emits `SpecPMGeneratedCandidateRefreshDecisionPreflightReport`. It
checks the shared `apiVersion: specpm.decisions/v0` envelope, refresh decision
status/update consistency, `no_contract_delta` no-op semantics, authority flags,
package IDs, safe artifact paths, and generated contract-file SHA-256 digests
when `--root` is provided.

Passing preflight means the refresh decision record is internally consistent
review evidence. It does not accept a package, update `public-index/curated`,
mutate `public-index/generated`, accept relations, or publish registry metadata.

## Missing Baseline Handoffs

When `prepare-refresh-decision` reports
`refresh_decision_prepare_current_contract_files_missing`, the correct output is
not a normal refresh decision. The fresh candidate has no current generated
baseline to compare against.

SpecHarvester can turn that state into
`SpecHarvesterBaselineSubmissionHandoff` evidence. SpecPM maintainers can check
it with:

```bash
specpm producer-bundle preflight-baseline-submission \
  --body <baseline-submission-handoff.json> \
  --root <handoff-artifact-root> \
  --json
```

This emits `SpecPMBaselineSubmissionHandoffPreflightReport`. Passing preflight
means the handoff is internally consistent first-submission or seeded-baseline
review evidence. It does not seed the baseline, emit a refresh decision, accept
packages, or publish registry metadata.

## Non-Goals

This policy does not add automatic registry updates, producer-owned
publication, request-time registry mutation, semantic package selection,
package signing trust enforcement, dependency solving, or runtime execution of
producer tools.

## References

- `specs/REGISTRY_ACCEPTANCE_DECISIONS.md`
- `specs/CURATED_ACCEPTED_ARTIFACT_LIFECYCLE.md`
- `specs/BASELINE_SUBMISSION_HANDOFF_PREFLIGHT.md`
- `specs/MULTI_PACKAGE_PRODUCER_INTAKE.md`
- `specs/PUBLIC_INDEX_OPERATOR_GUIDE.md`
- `specs/XYFLOW_PACKAGE_SET_REFERENCE.md`
- `tests/fixtures/refresh_decisions/xyflow-no-update.example.json`
- `public-index/curated/xyflow.workspace/0.1.0/specpm.yaml`
- `public-index/generated/xyflow.workspace/0.1.0/producer-receipt.json`
