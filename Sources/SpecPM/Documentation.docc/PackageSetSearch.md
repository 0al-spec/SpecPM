# Package Set Search

Discover aggregate and scoped package results without traversing a package tree.

## Overview

Package-set search is exact indexed lookup with explicit result scope.

The rule is:

```text
exact query -> direct indexed matches -> optional relation context
```

not:

```text
exact query -> root package -> traverse members -> infer leaf meaning
```

Package sets may appear beside scoped packages in exact search results when both
explicitly declare the searched capability or `intent.*`.

## Result Scope

Initial result scopes are:

- `package`: a concrete or scoped `SpecPackage`;
- `aggregate`: a package-set or collection entrypoint;
- `abstract_contract`: an abstract intent-level contract;
- `related`: relation context only, not a direct match.

Scope helps consumers display the result. It does not grant trust, lifecycle
state, acceptance, or selection authority.

## Example

Exact lookup for:

```text
intent.ui.node_based_editor
```

may return:

```text
xyflow.workspace scope=aggregate match=direct
xyflow.react     scope=package   match=direct
xyflow.svelte    scope=package   match=direct
```

Exact lookup for:

```text
intent.ui.flow_system_utilities
```

may return only:

```text
xyflow.system scope=package match=direct
```

The package set should not receive the narrower result unless it explicitly
declares that narrower intent as aggregate metadata.

## Boundary

Multiple direct matches are not an error. They are expected for shared intents.

SpecPM exposes exact metadata. Selection belongs to downstream consumers,
resolvers, SpecGraph, ContextBuilder, or human reviewers.

## References

- `specs/PACKAGE_SET_SEARCH.md`
- `specs/PACKAGE_SET_REGISTRY_METADATA.md`
- `specs/PACKAGE_SETS.md`
- `specs/PACKAGE_RELATIONS.md`
- <doc:PackageSetRegistryMetadata>
- <doc:PackageSets>
- <doc:PackageRelations>
- <doc:XyflowPackageSetReference>
- <doc:IdentifierModel>
