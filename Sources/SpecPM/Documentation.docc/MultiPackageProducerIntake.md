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
- proposed accepted-source diff;
- maintainer decision records or review notes.

For SpecHarvester handoff, the expected top-level artifacts are
`package-set-handoff-proposal.json` and `package-set-handoff-proposal.md`.
They summarize the candidate set for review, but they do not replace
per-package candidate files, receipts, validation reports, diagnostics reports,
or accepted-source review.

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

## Boundary

This policy does not add automatic bundle-set acceptance, automatic relation
acceptance, SpecPM execution of producer tools, dependency solving, semantic
package selection, package execution, or trust propagation.

## References

- `specs/MULTI_PACKAGE_PRODUCER_INTAKE.md`
- `specs/PRODUCER_BUNDLE_PROPOSAL_POLICY.md`
- `specs/SPECHARVESTER_MONOREPO_DISCOVERY.md`
- <doc:ProducerBundleProposalPolicy>
- <doc:SpecHarvesterMonorepoDiscovery>
- <doc:PackageSets>
