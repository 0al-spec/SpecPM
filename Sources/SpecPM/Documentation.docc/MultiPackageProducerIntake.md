# Multi-Package Producer Intake

Review producer-backed package-set proposals without treating generated output
as registry authority.

## Overview

A multi-package proposal may include:

```text
xyflow.workspace
xyflow.system
xyflow.react
xyflow.svelte
```

plus relation proposals such as:

```text
xyflow.workspace contains xyflow.react
```

SpecPM treats this as review evidence. Maintainers still decide which packages,
versions, and relations are accepted.

## Required Evidence

A proposal should include:

- workspace inventory report;
- package-set handoff proposal JSON;
- package-set handoff proposal Markdown summary;
- package-set candidate bundle;
- scoped member package candidate bundles;
- relation proposal report;
- producer receipts;
- validation reports;
- diagnostics reports;
- bundle-set preflight evidence;
- package-set AI draft proposal, when available;
- package-set AI enrichment proposal, when available;
- proposed accepted-source diff;
- maintainer decision records or review notes.

For SpecHarvester handoff, the expected top-level artifacts are
`package-set-handoff-proposal.json` and `package-set-handoff-proposal.md`.
They summarize the candidate set for review, but they do not replace
per-package candidate files, receipts, validation reports, diagnostics reports,
or accepted-source review.

Optional AI enrichment evidence may appear as
`package-set-ai-enrichment-proposal.json` with
`kind: SpecHarvesterPackageSetAIEnrichmentProposal`. It can propose refined
summaries, capabilities, intents, interfaces, or evidence gaps for reviewer
consideration. It does not replace the package-set handoff, per-package
candidate files, relation proposals, or accepted-source review.

Optional AI draft evidence may appear earlier as
`package-set-ai-draft-proposal.json` with
`kind: SpecHarvesterPackageSetAIDraftProposal`. It can propose aggregate
members, exclusions, and `contains` relations from workspace inventory evidence.
It does not replace deterministic workspace inventory, package-set handoff,
bundle-set preflight, AI enrichment, relation acceptance, or accepted-source
review.

## Handoff Checklist

Before turning a package-set handoff into registry input, maintainers should
verify:

- the handoff records producer revision and harvested source revision;
- aggregate/package-set intent is separated from scoped member package intent;
- selected member candidates link their candidate bundles, manifests, specs,
  receipts, validation reports, and diagnostics reports;
- `producerEvidenceLinks` cover package-set handoff, workspace inventory,
  relation proposals, bundle-set preflight, static viewer evidence when
  available, and per-package candidate evidence;
- `registryAcceptanceDecision.status` remains non-approved until maintainer
  review records acceptance;
- `producerReceiptAuthority` remains `evidence_only`;
- dry-run handoff artifacts do not require exposing SpecPM write credentials to
  untrusted producer code.

Maintainers can run consumer-side package-set preflight against the handoff
artifact before accepted-source review:

```bash
specpm producer-bundle preflight \
  --body <package-set-handoff-proposal.json> \
  --root <package-set-bundle-root> \
  --json
```

This checks package-set handoff identity, linked evidence digests, member
manifest IDs, bundle-set preflight status/counts, and `contains` relation
endpoints. It remains review evidence only and does not accept packages or
relations.

After review, maintainers can materialize an explicit subset:

```bash
specpm producer-bundle materialize-package-set \
  --handoff <package-set-handoff-proposal.json> \
  --root <package-set-bundle-root> \
  --package <accepted-package-id> \
  --relation <accepted-relation-id> \
  --manifest-candidate-output accepted-manifest-candidate.yml \
  --pr-body-output package-set-accepted-source-pr.md
```

The helper prepares review artifacts only. It fails closed when selected
packages or relations are absent, package-set preflight failed, or a selected
relation does not connect selected package endpoints.

## AI Enrichment Checklist

When a package-set proposal includes AI enrichment evidence, maintainers should
verify `authority: proposal_only_not_registry_acceptance`, privacy flags for
raw prompts, raw responses, chain-of-thought, and secrets are false, the
`trustBoundary` keeps SpecPM as validation and registry authority, proposed
`packageId` values match reviewed handoff members, proposed capabilities and
interfaces cite allowlisted `evidencePaths`, unsupported evidence paths remain
diagnostics, `interfaces[].kind` is present for interface suggestions, and
provider receipts are provenance only.

AI enrichment remains proposal-only even when its status is `completed`. It
must not auto-accept capabilities, intents, interfaces, summaries, package
relations, package versions, or accepted-source entries.

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

## AI Draft Preflight Plan

SpecPM should add a consumer-side AI draft preflight before maintainers use
`SpecHarvesterPackageSetAIDraftProposal` as review evidence:

```bash
specpm producer-bundle preflight-ai-draft \
  --body <package-set-ai-draft-proposal.json> \
  --root <package-set-bundle-root> \
  --json
```

The planned preflight should verify artifact identity, proposal-only authority,
privacy flags, provider receipts, workspace inventory input, package ID
alignment, inventory-derived `sourceTargetPath` values, allowlisted evidence
paths, selected/excluded package consistency, and `contains` relation endpoints.
It should reject registry acceptance decision fields and remain review evidence
only. A passing report must not create a handoff, accept package members, accept
relations, mutate generated specs, materialize accepted sources, or publish
registry metadata.

## Partial Acceptance

Maintainers may accept only part of the bundle set:

- package set only;
- one or more member packages;
- selected relations;
- no generated packages.

Accepting a package set does not accept all members. Accepting a member does not
accept the package set. Accepting a relation does not grant trust or selection
authority.

Maintainers should copy only accepted packages and accepted relations into
registry input. Rejected or deferred members may remain in evidence without
becoming visible in the public index.

## Curated Accepted Artifacts

When maintainers improve generated package-set candidates, they should create a
separate maintainer-curated accepted artifact instead of editing producer output
in place. The curated artifact may reference the generated candidate,
`producer-receipt.json`, validation report, diagnostics report, handoff, and AI
enrichment proposal as evidence, but the curated manifest and BoundarySpec are
authored by SpecPM maintainer review.

This allows maintainers to remove `preview_only` from accepted registry
metadata without making the producer receipt an authority document. The receipt
continues to describe what the producer emitted; the curated artifact describes
what maintainers accepted.

The full lifecycle is covered by <doc:CuratedAcceptedArtifactLifecycle>. The
key boundaries are: generated candidates are immutable producer evidence; curated
artifacts own maintainer-authored accepted metadata; new harvests update
curated artifacts only through review diffs; curated artifacts preserve
`foreignArtifacts` evidence chains; removing `preview_only` is a maintainer
acceptance act; and package relation acceptance is recorded separately in
`public-index/accepted-packages.yml` `relations[]`.

## Boundary

This policy does not add automatic bundle-set acceptance, automatic relation
acceptance, SpecPM execution of producer tools, dependency solving, semantic
package selection, package execution, or trust propagation.

## References

- `specs/MULTI_PACKAGE_PRODUCER_INTAKE.md`
- `specs/PRODUCER_BUNDLE_PROPOSAL_POLICY.md`
- <doc:CuratedAcceptedArtifactLifecycle>
- `specs/SPECHARVESTER_MONOREPO_DISCOVERY.md`
- <doc:ProducerBundleProposalPolicy>
- <doc:SpecHarvesterMonorepoDiscovery>
- <doc:PackageSets>
