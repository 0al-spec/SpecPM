# Generated Candidate Refresh Decision Policy

SpecPM records refresh decisions when a fresh producer run is compared with
current registry sources.

```text
fresh generated candidate -> comparison evidence
refresh decision -> update/no-update record
curated accepted artifact -> registry source
```

The decision record is `SpecPMGeneratedCandidateRefreshDecision`:

```json
{
  "apiVersion": "specpm.decisions/v0",
  "kind": "SpecPMGeneratedCandidateRefreshDecision",
  "schemaVersion": 1,
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
  "authority": {
    "producerEvidenceAuthority": "evidence_only",
    "registryAuthority": "maintainer_review_required"
  }
}
```

The record reuses the shared SpecPM decision envelope
`apiVersion: specpm.decisions/v0`. The distinct
`kind: SpecPMGeneratedCandidateRefreshDecision` lets tooling recognize refresh
or no-update decisions without introducing another decision API family.

## No-Update Outcome

Use `status: no_update_required`, `updateNeeded: false`, and
`reason: no_contract_delta` when a fresh producer run does not change accepted
package claims, capabilities, evidence, relations, package-set membership, or
source revision.

Receipt churn, local run paths, new quality reports, and advisory producer
metadata are not accepted contract deltas by themselves.

## Update Outcomes

Use an update-required status when the comparison finds changed accepted
claims, capabilities, intent IDs, evidence, package boundaries, relation
endpoints, relation types, package-set membership, or source revision effects.

The supported statuses are:

- `no_update_required`
- `curated_update_required`
- `new_generated_candidate_required`
- `new_package_version_required`
- `manual_review_required`

## Immutability Boundary

`public-index/generated/<package_id>/<version>` remains producer evidence. Do
not edit generated candidates in place to reflect a fresh run.

When maintainers accept a contract change, update the curated artifact under
`public-index/curated/<package_id>/<version>` or create a new accepted package
version through review.

## Xyflow Example

A fresh `xyflow` package-set run at revision
`a58568f11bc0e1a1bdca1b3549e959e2e1ca0cdd` reproduced the same generated
contract bytes for `xyflow.workspace`, `xyflow.react`, `xyflow.svelte`, and
`xyflow.system`. The only meaningful difference was producer receipt churn plus
an additional advisory quality report.

The correct decision is `no_update_required` with
`reason: no_contract_delta`. This records the value of the refresh without
churning accepted registry metadata.

A complete example fixture is available at
`tests/fixtures/refresh_decisions/xyflow-no-update.example.json`. It uses
`apiVersion: specpm.decisions/v0`, covers the four `xyflow` package-set members,
and snapshots generated contract-file digests that support
`updateNeeded: false`.

## Prepare Helper

SpecPM can prepare a draft refresh decision by comparing fresh generated
candidate artifacts with the current registry evidence:

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
and runs the same consumer-side preflight rules against the prepared decision.

Matching contract files produce `status: no_update_required`,
`updateNeeded: false`, and `reason: no_contract_delta`. Contract, source
revision, or accepted-artifact drift produces `manual_review_required` with
`updateNeeded: true`. Both outcomes remain review evidence only.

## CI Artifact

The manual `.github/workflows/refresh-decision-prepare.yml` workflow runs the
same prepare helper through `workflow_dispatch` and uploads:

- `refresh-decision.json`
- `prepare-report.json`
- `preflight-report.json`

It defaults to the current `xyflow` package-set no-op comparison and exposes
inputs for package IDs, version, source repository, source revision, fresh
generated root, and run label. The workflow has `contents: read` permissions,
does not require write credentials, and does not mutate registry state.

## Consumer-Side Preflight

SpecPM can verify refresh decision records with:

```bash
specpm producer-bundle preflight-refresh-decision \
  --body tests/fixtures/refresh_decisions/xyflow-no-update.example.json \
  --root . \
  --json
```

The command emits `SpecPMGeneratedCandidateRefreshDecisionPreflightReport`. It
checks the shared decision envelope, status/update consistency,
`no_contract_delta` no-op semantics, authority flags, package IDs, safe artifact
paths, and generated contract-file SHA-256 digests when `--root` is provided.

Passing preflight means the decision is internally consistent review evidence.
It does not accept a package, update curated artifacts, mutate generated
candidates, accept relations, or publish registry metadata.

## References

- `specs/GENERATED_CANDIDATE_REFRESH_DECISION_POLICY.md`
- `tests/fixtures/refresh_decisions/xyflow-no-update.example.json`
- <doc:RegistryAcceptanceDecisions>
- <doc:CuratedAcceptedArtifactLifecycle>
- <doc:MultiPackageProducerIntake>
- <doc:XyflowPackageSetReference>
