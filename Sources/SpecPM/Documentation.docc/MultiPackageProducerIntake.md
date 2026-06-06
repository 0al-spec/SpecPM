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
- package-set candidate bundle;
- scoped member package candidate bundles;
- relation proposal report;
- producer receipts;
- validation reports;
- diagnostics reports;
- bundle-set preflight evidence;
- proposed accepted-source diff;
- maintainer decision records or review notes.

## Partial Acceptance

Maintainers may accept only part of the bundle set:

- package set only;
- one or more member packages;
- selected relations;
- no generated packages.

Accepting a package set does not accept all members. Accepting a member does not
accept the package set. Accepting a relation does not grant trust or selection
authority.

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

