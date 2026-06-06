# Package Sets

Represent related packages without forcing discovery through a tree.

## Overview

A package set is a collection entrypoint for multiple related `SpecPackage`
records. It is useful for repositories, workspaces, ecosystems, and product
families where users need both:

- broad product-level discovery; and
- precise scoped package contracts.

For example, an `xyflow` package family may need:

```text
xyflow.workspace
  contains xyflow.system
  contains xyflow.react
  contains xyflow.svelte
```

The workspace entrypoint preserves broad product intent. The scoped member
packages preserve evidence discipline, package ownership, and precise
capability boundaries.

## Boundary

Package sets are metadata. They do not add inheritance, dependency solving,
natural-language search, package execution, or automatic package selection.

A package set may group related packages, but members do not inherit:

- capabilities;
- constraints;
- lifecycle state;
- acceptance status;
- namespace ownership;
- trust.

Every member package remains a separate reviewed subject.

## Discovery Model

Package-set discovery should be index-based, not tree-traversal-based.

An exact `intent.*` lookup may return both aggregate and scoped results:

```json
{
  "intent": "intent.ui.node_based_editor",
  "results": [
    {
      "package": "xyflow.workspace",
      "scope": "aggregate"
    },
    {
      "package": "xyflow.react",
      "scope": "package"
    }
  ]
}
```

Relations explain why results are connected after discovery. Consumers should
not need to walk from root to leaf to find the first useful result.

## Producer Boundary

Producer tools such as SpecHarvester may discover a monorepo and propose:

- a package-set candidate;
- scoped member package candidates;
- relation evidence;
- receipts, validation reports, diagnostics, and preview evidence.

SpecPM still owns validation, public-index review, generated registry metadata,
and maintainer acceptance decisions. Producer output is evidence, not registry
authority.

## References

- `specs/PACKAGE_SETS.md`
- `specs/PACKAGE_RELATIONS.md`
- `specs/PACKAGE_SET_SEARCH.md`
- `specs/PACKAGE_SET_REGISTRY_METADATA.md`
- `specs/WORKPLAN.md`
- <doc:PackageRelations>
- <doc:PackageSetSearch>
- <doc:PackageSetRegistryMetadata>
- <doc:PackageModel>
- <doc:ProducerBundleProposalPolicy>
- <doc:SpecQualityModel>
