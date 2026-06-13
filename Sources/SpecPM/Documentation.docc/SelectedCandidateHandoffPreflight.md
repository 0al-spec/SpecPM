# Selected Candidate Handoff Preflight

Validate SpecHarvester selected candidate handoff evidence before maintainer
intake review.

## Command

```bash
specpm producer-bundle preflight-selected-candidate-handoff \
  --body <selected-candidate-handoff.json> \
  --root <handoff-artifact-root> \
  --json
```

The command accepts raw JSON or Markdown with a JSON block. It emits
`SpecPMSelectedCandidateHandoffPreflightReport` with `apiVersion:
specpm.selected-candidate-handoff-preflight/v0`.

## Accepted Inputs

The preflight accepts:

- `SpecHarvesterSelectedCandidateHandoffProposal`;
- `SpecHarvesterRefreshedCandidateLayerSelectedHandoff`.

It verifies handoff identity, `schemaVersion`, producer authority, selected and
deferred candidate counts, unique candidate IDs, preview-only posture,
producer-preflight status, static viewer status, external registry acceptance
requirements, evidence roles, SHA-256 digests, and non-authority flags.

For refreshed P32 evidence, it also verifies source fixture digests when
`--root` is provided and keeps `cupertino.core` deferred on
`refined_summary_missing`.

## Boundary

Passing preflight means the handoff is internally consistent review evidence.
It does not accept packages, accept relations, seed baselines, remove
`preview_only`, publish registry metadata, or create a SpecPM pull request.

See `specs/SELECTED_CANDIDATE_HANDOFF_PREFLIGHT.md` for the canonical policy.

## See Also

- <doc:MultiPackageProducerIntake>
- <doc:ProducerBundleProposalPolicy>
- <doc:BaselineSubmissionHandoffPreflight>
