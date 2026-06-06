# SpecHarvester Monorepo Discovery

SpecPM-side handoff contract for generated package sets and scoped member
packages.

## Overview

SpecHarvester may inspect a multi-package repository and propose:

- a workspace inventory;
- a package-set candidate;
- scoped member package candidates;
- relation proposals;
- receipts, validation reports, diagnostics, preflight evidence, and previews.

SpecPM treats these artifacts as review evidence. They do not automatically
publish packages, accept relations, grant namespace ownership, or make
SpecHarvester a registry authority.

## Example

For `xyflow`, a producer may propose:

```text
xyflow.workspace
xyflow.system
xyflow.react
xyflow.svelte
```

The workspace candidate preserves aggregate discovery intent. The scoped member
packages preserve package-level evidence and capability boundaries.

## Handoff Evidence

A monorepo discovery handoff should include:

- repository URL and exact revision;
- workspace manifest paths;
- package manifest paths;
- proposed package IDs and roles;
- package-set and member candidate bundles;
- relation proposal report;
- producer receipts;
- validation and diagnostics reports;
- bundle-set preflight evidence.

## Boundary

SpecHarvester owns discovery and candidate generation. SpecPM owns validation,
accepted-source review, generated registry metadata after merge, and maintainer
acceptance decisions.

Maintainers may accept only part of a generated bundle set.

## References

- `specs/SPECHARVESTER_MONOREPO_DISCOVERY.md`
- `specs/MULTI_PACKAGE_PRODUCER_INTAKE.md`
- `specs/PACKAGE_SETS.md`
- `specs/PACKAGE_RELATIONS.md`
- `specs/PACKAGE_SET_REGISTRY_METADATA.md`
- <doc:PackageSets>
- <doc:PackageRelations>
- <doc:PackageSetRegistryMetadata>
- <doc:MultiPackageProducerIntake>
- <doc:ProducerBundleProposalPolicy>
