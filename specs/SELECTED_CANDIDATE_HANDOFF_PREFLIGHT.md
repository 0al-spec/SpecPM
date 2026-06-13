# Selected Candidate Handoff Preflight

Status: Draft
Updated: 2026-06-13
Scope: SpecPM consumer-side validation for SpecHarvester selected candidate
handoff evidence

## Purpose

SpecHarvester can produce selected preview candidates for a bounded repository
corpus. Those artifacts are useful review evidence, but they are not SpecPM
registry authority.

`specpm producer-bundle preflight-selected-candidate-handoff` checks that a
selected handoff artifact is internally consistent before maintainers use it
for intake review:

```text
SpecHarvester selected preview evidence
  -> SpecPM selected candidate handoff preflight
  -> maintainer review
  -> optional accepted-source or regeneration decision
```

The command currently accepts:

- `SpecHarvesterSelectedCandidateHandoffProposal`
  (`spec-harvester.selected-candidate-handoff-proposal/v0`);
- `SpecHarvesterRefreshedCandidateLayerSelectedHandoff`
  (`spec-harvester.refreshed-candidate-layer-selected-handoff/v0`).

## Command

```bash
specpm producer-bundle preflight-selected-candidate-handoff \
  --body <selected-candidate-handoff.json> \
  --root <handoff-artifact-root> \
  --json
```

`--body` may be a raw JSON file or Markdown containing a JSON block.

`--root` is optional. Without it, SpecPM validates envelope shape, selected and
deferred candidate consistency, and authority fields, but emits a warning
because linked source fixture digests cannot be verified.

## Verified Contract

The preflight emits `SpecPMSelectedCandidateHandoffPreflightReport` with
`apiVersion: specpm.selected-candidate-handoff-preflight/v0` and checks:

- supported `apiVersion` and `kind`;
- `schemaVersion: 1`;
- `authority: producer_preview_evidence_only`;
- `summary.selectedCandidateCount` and `summary.deferredCandidateCount`;
- no SpecPM pull request creation and no registry mutation;
- unique selected and deferred candidate IDs;
- no candidate appears in both selected and deferred sets;
- every selected candidate remains `previewOnly: true`;
- every selected candidate has `producerPreflight.status: passed`,
  `warningCount: 0`, and `errorCount: 0`;
- every selected candidate has static viewer status `ok`;
- every selected candidate has `registryAcceptanceDecision.status:
  external_required`, `producerAuthority: evidence_only`, and
  `requiredFor: public_index_acceptance`;
- required evidence roles and SHA-256 digests;
- non-authority statements or flags covering package acceptance, relation
  acceptance, baseline seeding, `preview_only` removal, public registry
  publication, and SpecPM pull request creation.

For refreshed P32 handoff evidence, the gate also checks:

- candidate-layer selected counts;
- producer preflight and viewer counts;
- `expectedConsumerGate` points to
  `SpecPMSelectedCandidateHandoffPreflightReport`;
- `sources[]` paths and digests when `--root` is provided;
- `cupertino.core` remains deferred with `refined_summary_missing`.

## Meaning Of A Pass

A passing report means the handoff is reviewable producer evidence. It does
not:

- accept packages;
- accept relations;
- seed baselines;
- remove `preview_only`;
- update `public-index/generated`;
- update `public-index/curated`;
- publish public registry metadata;
- create or merge a SpecPM pull request;
- prove generated claims are semantically complete.

Maintainers still decide whether to accept, reject, request regeneration, seed
a baseline, or prepare a separate accepted-source diff.

Short form: passing selected handoff preflight does not accept packages and
does not accept relations.

## Failure Signals

The command fails closed for unsupported handoff identity, unsupported schema
version, producer authority drift, selected/deferred count drift, duplicate
candidate IDs, selected candidates that are not preview-only, producer
preflight warnings or errors, static viewer failures, missing evidence roles,
invalid digests, source fixture digest mismatch, unexpected registry mutation,
or producer claims of package acceptance.

Historical absolute `local_path` evidence from older SpecHarvester fixtures is
treated as provenance. Stable source fixtures and refreshed handoff source
records are the digest-backed inputs that SpecPM verifies under `--root`.
