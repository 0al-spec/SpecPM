# Multi-Package Producer Bundle Intake

Status: Draft
Updated: 2026-06-07
Scope: SpecPM review policy for producer-backed package-set and multi-package
candidate proposals

## Purpose

This document defines how SpecPM maintainers should review producer-backed
proposals that contain multiple related candidate packages.

Typical proposal:

```text
xyflow.workspace
xyflow.system
xyflow.react
xyflow.svelte
relations:
  xyflow.workspace contains xyflow.system
  xyflow.workspace contains xyflow.react
  xyflow.workspace contains xyflow.svelte
```

The proposal is evidence. It is not registry authority.

## Boundary

The multi-package intake flow extends the ordinary producer bundle proposal
policy. It does not replace:

- package validation;
- accepted-source review;
- maintainer decisions;
- namespace policy;
- registry provenance receipts;
- public-index generation after merge.

The review path is:

```text
producer bundle set -> per-package review -> relation review -> accepted-source PR
```

not:

```text
producer bundle set -> automatic package family acceptance
```

## Required Evidence

A multi-package proposal should include:

- workspace inventory report;
- package-set handoff proposal JSON;
- package-set handoff proposal Markdown summary;
- package-set candidate bundle;
- scoped member package candidate bundles;
- relation proposal report;
- producer receipt for each candidate package;
- validation report for each candidate package;
- diagnostics report for each candidate package;
- bundle-set preflight report;
- static preview evidence, when available;
- package-set AI draft proposal, when available;
- package-set AI enrichment proposal, when available;
- proposed accepted-source diff;
- maintainer acceptance decision records or review notes.

Each candidate package remains independently reviewable.

For SpecHarvester handoff, the expected top-level artifacts are
`package-set-handoff-proposal.json` and `package-set-handoff-proposal.md`.
They summarize the candidate set for review. They do not replace per-package
candidate files, receipts, validation reports, diagnostics reports, or the
accepted-source pull request.

Optional AI enrichment evidence may appear as
`package-set-ai-enrichment-proposal.json` with
`kind: SpecHarvesterPackageSetAIEnrichmentProposal`. This artifact can propose
refined summaries, capabilities, intents, and interfaces for reviewer
consideration. It does not replace the package-set handoff, per-package
candidate files, relation proposals, or accepted-source review.

Optional AI draft evidence may appear earlier as
`package-set-ai-draft-proposal.json` with
`kind: SpecHarvesterPackageSetAIDraftProposal`. This artifact can propose which
workspace inventory packages should become aggregate members, which packages
should be excluded, and which `contains` relations should be drafted. It does
not replace deterministic workspace inventory, package-set handoff, bundle-set
preflight, AI enrichment, relation acceptance, or accepted-source review.

## Package-Set Handoff Checklist

Before turning a producer handoff into an accepted-source pull request,
maintainers should verify:

- the handoff declares the producer, producer revision, source repository, and
  harvested source revision;
- the handoff uses a package-set subject such as `xyflow.workspace` for the
  aggregate entrypoint and scoped member subjects such as `xyflow.system`,
  `xyflow.react`, and `xyflow.svelte`;
- aggregate/package-set intent is separated from scoped member package intent;
- every selected member candidate has a path to its candidate bundle,
  `specpm.yaml`, `specs/*.spec.yaml`, receipt, validation report, and
  diagnostics report;
- `producerEvidenceLinks` cover the package-set handoff proposal, workspace
  inventory, package-set metadata, relation proposals, bundle-set preflight,
  static viewer evidence when available, and per-package candidate evidence;
- `registryAcceptanceDecision.status` is `external_required`, `pending`,
  or another non-approved review state until a maintainer records acceptance;
- `registryAcceptanceDecision.producerReceiptAuthority` is `evidence_only`;
- the handoff came from a trusted workflow boundary or dry-run artifact and did
  not require exposing SpecPM write credentials to untrusted producer code;
- any generated accepted-source diff is reviewed as a proposed registry input,
  not as producer authority.

## AI Enrichment Checklist

When a package-set proposal includes AI enrichment evidence, maintainers should
verify:

- `authority` is `proposal_only_not_registry_acceptance`;
- `privacy.rawPromptsPersisted`, `privacy.rawModelResponsesPersisted`,
  `privacy.chainOfThoughtPersisted`, and `privacy.secretsIncluded` are `false`;
- `trustBoundary` states that SpecPM remains the validation, acceptance,
  relation, and registry authority;
- proposed `packageId` values match package-set handoff members or separately
  reviewed accepted package subjects;
- proposed capabilities and interfaces cite allowlisted `evidencePaths`;
- unsupported evidence paths are diagnostics and are not treated as accepted
  facts;
- `interfaces[].kind` is present when interface suggestions are reviewed;
- `providerReceipt` records provider receipts as provenance only and does not
  make model output authoritative.

AI enrichment remains proposal-only even when its status is `completed`. It
must not auto-accept capabilities, intents, interfaces, summaries, package
relations, package versions, or accepted-source entries. Maintainers may use it
as a review aid, then edit or reject each generated claim under ordinary
package evidence review.

SpecPM can run a consumer-side AI enrichment preflight before using the
artifact during review:

```bash
specpm producer-bundle preflight-ai-enrichment \
  --body <package-set-ai-enrichment-proposal.json> \
  --root <package-set-bundle-root> \
  --handoff <package-set-handoff-proposal.json> \
  --json
```

This checks the machine-readable proposal boundary. It does not accept model
suggestions or alter package-set materialization.

## AI Draft Preflight Checklist

When a package-set proposal includes AI draft evidence, maintainers can run a
consumer-side preflight that checks the machine-readable drafting boundary before
using it to guide producer-side package-set generation:

```bash
specpm producer-bundle preflight-ai-draft \
  --body <package-set-ai-draft-proposal.json> \
  --root <package-set-bundle-root> \
  --json
```

This emits `SpecPMPackageSetAIDraftPreflightReport` and verifies artifact
identity, proposal-only authority, privacy flags, provider receipts, workspace
inventory input, package ID alignment,
inventory-derived `sourceTargetPath` values, allowlisted evidence paths,
selected/excluded package consistency, and `contains` relation endpoints. It
rejects registry acceptance decision fields and remains review evidence only. A
passing report must not create a handoff, accept package members, accept
relations, mutate generated specs, materialize accepted sources, or publish
registry metadata.

SpecPM package-set intake preflight can check the handoff artifact before
maintainer review:

```bash
specpm producer-bundle preflight \
  --body <package-set-handoff-proposal.json> \
  --root <package-set-bundle-root> \
  --json
```

The preflight verifies package-set handoff identity, linked evidence digests,
member manifest IDs, bundle-set preflight status/counts, and `contains`
relation endpoints. It is evidence for review only and does not accept packages,
accept relations, or write registry input.

After review, maintainers can generate a proposed accepted-source diff from an
explicit subset:

```bash
specpm producer-bundle materialize-package-set \
  --handoff <package-set-handoff-proposal.json> \
  --root <package-set-bundle-root> \
  --package <accepted-package-id> \
  --relation <accepted-relation-id> \
  --manifest-candidate-output accepted-manifest-candidate.yml \
  --pr-body-output package-set-accepted-source-pr.md
```

The materialization helper fails closed when selected package or relation IDs
are absent, when package-set preflight failed, or when a selected relation does
not connect selected package endpoints.

Maintainers should copy only the accepted packages and accepted relations into
the registry input. A rejected or deferred member can remain in the handoff
evidence without becoming visible in the public index.

## Maintainer-Curated Accepted Artifacts

Producer materialization can copy generated candidates into a review branch,
but maintainers should not polish those generated files in place and still
pretend the producer receipt describes them. When accepted registry metadata
needs human wording, tighter capabilities, or non-preview acceptance posture,
create a separate maintainer-curated package directory.

The curated artifact may reference producer output as evidence:

- generated `specpm.yaml`;
- `producer-receipt.json`;
- `validation-report.json`;
- `diagnostics.json`;
- package-set handoff and AI enrichment proposal, when relevant.

Those references should be evidence or `foreignArtifacts`, not a replacement
authority chain. The producer receipt describes what the producer emitted. The
curated artifact describes what maintainers accepted.

For the `xyflow` package-set, the accepted registry source is the curated
directory under `public-index/curated/xyflow.*`, while the generated
SpecHarvester output remains under `public-index/generated/xyflow.*` as
evidence. This lets maintainers remove `preview_only` from the curated entry
without changing producer receipt hashes or making producer output
authoritative.

The full curated artifact lifecycle is documented in
`specs/CURATED_ACCEPTED_ARTIFACT_LIFECYCLE.md`. In short:

- generated candidates are immutable producer evidence;
- curated artifacts own maintainer-authored accepted metadata;
- new harvests update curated artifacts only through review diffs;
- curated artifacts preserve `foreignArtifacts` evidence chains;
- removing `preview_only` is a maintainer acceptance act;
- package relation acceptance is recorded separately in
  `public-index/accepted-packages.yml` `relations[]`.

## Bundle-Set Checklist

Before accepting any part of a multi-package proposal, maintainers should verify:

- every package candidate has stable `metadata.id` and `metadata.version`;
- the package set and member packages do not share the same package ID;
- package-level evidence does not rely on unrelated member directories;
- repository-level evidence is used for aggregate discovery claims only;
- member package capabilities are not silently re-exported by the package set;
- relation proposals use the documented relation vocabulary;
- relation evidence supports the selected relation type;
- diagnostics do not report failed producer-side checks;
- privacy reports do not indicate included secrets;
- each accepted package/version has an explicit accepted-source entry or
  accepted-source diff.

## Partial Acceptance

Maintainers may accept:

- the package set only;
- one or more member packages only;
- a subset of proposed relations;
- none of the producer proposal.

Partial acceptance must be explicit. A package-set acceptance does not imply
member package acceptance. A member package acceptance does not imply package-set
acceptance. A relation acceptance does not imply either package subject is
trusted or selected by consumers.

## Relation Acceptance

Accepted relations should record:

- relation type;
- source package ID and version scope;
- target package ID and version scope;
- evidence paths or review notes;
- maintainer decision location;
- whether the relation is accepted, rejected, or deferred.

Producer-observed relations should stay marked as evidence until maintainer
review accepts them.

## Accepted-Source Effects

Accepted-source changes should be reviewable as ordinary manifest diffs.

For a package-set proposal, maintainers should be able to see:

```text
added xyflow.workspace 0.1.0
added xyflow.system 0.1.0
added xyflow.react 0.1.0
deferred xyflow.svelte 0.1.0
accepted relation: xyflow.workspace contains xyflow.system
accepted relation: xyflow.workspace contains xyflow.react
```

The accepted-source diff is the registry input. Producer receipts remain
supporting evidence.

## CI Preflight Expectations

Current single-package producer preflight can inspect machine-readable
`producerEvidenceLinks` and `registryAcceptanceDecision` blocks in a proposal
body. For package-set proposals, CI should still be treated as evidence-only
unless a future bundle-set preflight explicitly makes a check required.

Future package-set CI preflight may check:

- required evidence roles are present for each candidate package;
- package-set handoff proposal JSON and Markdown summary are present;
- candidate package IDs are unique within the bundle set;
- receipts do not hash themselves;
- output digests match package files;
- relation proposal source and target package IDs exist in the bundle set or
  current registry metadata;
- package-set and member subject scopes do not collapse into a single package;
- dry-run handoff evidence does not require `SPECPM_PROPOSAL_TOKEN` or other
  write credentials;
- acceptance decision records do not treat producer receipts as authority.

Preflight should remain evidence until maintainers choose to make a specific
check required.

## Failure and Warning Signals

Reject or request regeneration when:

- package IDs are unstable or collide;
- aggregate claims are copied into every member package;
- member-only capabilities are copied into the package set without an explicit
  re-export profile;
- relation types are vague or unsupported;
- relation evidence does not support the relation;
- `package-set-handoff-proposal.json` disagrees with candidate bundles,
  relation proposals, or receipts;
- a dry-run handoff claims that it created, approved, or merged a SpecPM
  accepted-source pull request;
- output digests do not match;
- diagnostics status is `failed`;
- privacy status indicates secrets or confidential local paths;
- the proposal asks SpecPM to run producer tools or accept packages
  automatically.

Warnings may be acceptable when:

- some member packages are intentionally omitted;
- static preview is absent but machine-readable evidence is present;
- relation acceptance is deferred;
- a package is manually authored and has no producer evidence.

## Non-Goals

This intake policy does not add:

- automatic bundle-set acceptance;
- automatic relation acceptance;
- SpecPM execution of producer tools;
- package-set generator implementation;
- public registry mutation APIs;
- dependency solving;
- semantic package selection;
- package execution;
- trust propagation.

## Future Work

Future implementation may add:

- multi-package evidence blocks for proposal bodies;
- preflight checks for bundle-set integrity;
- acceptance decision records that cover relation decisions;
- static viewer support for package-set review;
- `xyflow` reference proposal fixtures.
