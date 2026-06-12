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
  "apiVersion": "specpm.registry-update-decision/v0",
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

## References

- `specs/GENERATED_CANDIDATE_REFRESH_DECISION_POLICY.md`
- <doc:CuratedAcceptedArtifactLifecycle>
- <doc:MultiPackageProducerIntake>
- <doc:XyflowPackageSetReference>
