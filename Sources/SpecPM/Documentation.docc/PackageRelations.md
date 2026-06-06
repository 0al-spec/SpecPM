# Package Relations

Navigate between package sets, scoped packages, abstract contracts, and
replacement packages without adding inheritance.

## Overview

Package relations are directed metadata claims between package subjects:

```text
source package --relation type--> target package
```

They help users understand why packages are grouped or connected after
discovery. Relations do not grant capabilities, trust, lifecycle state,
namespace ownership, or acceptance status to either side.

## Vocabulary

The initial vocabulary is:

- `contains`: a package set or aggregate entrypoint includes a member package;
- `composes`: a package combines another package or contract into a larger
  reviewable contract;
- `refines`: a package is a more specific contract than another package;
- `satisfies`: a concrete package claims to satisfy an abstract or required
  contract through evidence;
- `supersedes`: a package replaces an older package subject for future
  discovery or maintenance;
- `related`: a weaker useful relationship when no stronger relation applies.

## Evidence

A relation should identify:

- source package;
- target package;
- relation type;
- affected version scope;
- evidence path or decision record;
- whether the claim is producer-observed, maintainer-reviewed, or accepted
  registry metadata.

Producer-observed relations are evidence only. Maintainer review is still
required before a relation becomes accepted registry metadata.

## Search Boundary

Relations explain context after discovery. Exact search should not require
walking relation paths.

For example, exact lookup for `intent.ui.node_based_editor` may return both:

```text
xyflow.workspace scope=aggregate
xyflow.react scope=package
```

The `contains` relation explains why those results are connected. It should not
be required to find the first useful result.

## References

- `specs/PACKAGE_RELATIONS.md`
- `specs/PACKAGE_SETS.md`
- `specs/PACKAGE_SET_SEARCH.md`
- <doc:PackageSets>
- <doc:PackageSetSearch>
- <doc:PackageModel>
- <doc:ProducerBundleProposalPolicy>
