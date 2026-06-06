# Package Sets and Collection Boundaries

Status: Draft
Updated: 2026-06-06
Scope: package-set concept and boundary for monorepos, workspaces, ecosystems,
and product families

## Purpose

This document defines the initial package-set concept for SpecPM.

A package set is a reviewable collection entrypoint for multiple related
`SpecPackage` records. It helps users and downstream tools discover a repository,
workspace, ecosystem, or product family without forcing every useful intent,
capability, or claim into one package.

The package set is package metadata. It is not a resolver, dependency solver,
inheritance mechanism, or registry authority.

## Problem

Multi-package repositories often expose two kinds of public meaning:

- broad product or repository-level intent, such as "node-based editors and
  interactive flow charts";
- narrow package-level contracts, such as a shared system package, React binding,
  Svelte binding, CLI, runtime, or adapter.

When producer tooling turns such a repository into one `SpecPackage`, it tends
to choose one bad compromise:

- a broad package that overclaims implementation details it did not inspect; or
- a narrow package that is evidence-disciplined but loses the product-level
  meaning users search for.

For example, an `xyflow` repository-level package may be discoverable for
`intent.ui.node_based_editor`, while a scoped `packages/system` package should
only claim the shared system layer that powers React Flow and Svelte Flow.
Both views are useful, but they are different package subjects.

## Concept

A package set is an aggregate entrypoint that groups related package subjects.
It may represent:

- a repository;
- a monorepo workspace;
- an ecosystem;
- a product family;
- a curated package family;
- a migration or compatibility family.

Conceptually:

```text
xyflow.workspace
  contains xyflow.system
  contains xyflow.react
  contains xyflow.svelte
```

The package set can carry aggregate discovery metadata such as a summary,
declared intents, member list, and relation evidence. The member packages retain
their own scoped capabilities, constraints, evidence, versions, lifecycle state,
and acceptance decisions.

## Boundary

SpecPM owns:

- the package-set concept and registry metadata contract;
- validation of package-set records once a schema/profile exists;
- exact package, capability, and intent indexing;
- public-index accepted-source review;
- generated static registry metadata after merge;
- maintainer acceptance or rejection decisions.

SpecHarvester or another producer owns:

- workspace discovery;
- member package candidate proposal;
- package-set candidate proposal;
- producer receipts, validation reports, diagnostics, and previews;
- source evidence collection.

Downstream tools own:

- semantic interpretation;
- graph reasoning;
- package selection;
- product architecture decisions;
- execution or artifact generation.

The intended flow is:

```text
producer discovery -> package-set candidate evidence -> SpecPM review -> static registry metadata
```

not:

```text
producer discovery -> automatic package-set acceptance
```

and not:

```text
package set -> inherited member claims
```

## Non-Goals

This concept does not add:

- a dependency solver;
- automatic member selection;
- natural-language search;
- semantic resolver authority;
- package execution;
- inherited capabilities or constraints;
- inherited lifecycle or acceptance status;
- automatic namespace ownership;
- request-time public registry mutation;
- a new trust model for producer output.

Package sets improve discovery and navigation. They do not decide which package a
consumer should use.

## Relationship to SpecPackage

The first implementation should prefer an extension-safe profile over a new
runtime object model.

A package set may be represented as either:

- a normal `SpecPackage` with explicit collection metadata; or
- a future `SpecPackageSet` kind if schema evolution requires a separate kind.

The first profile should remain compatible with the existing boundary-first
model:

- `specpm.yaml` still declares package identity and indexable metadata;
- `specs/*.spec.yaml` still describes a reviewable boundary;
- relation data must be explicit;
- unknown extension fields must remain non-executable package data;
- package-set status must not grant authority to member packages.

The important distinction is semantic, not inheritance-based:

```text
SpecPackage: scoped package contract
Package set: aggregate discovery and navigation entrypoint
```

## Relationship to Abstract Packages

Abstract packages define desired capability contracts that concrete packages may
later satisfy through reviewable evidence and downstream graph relationships.

Package sets group related packages. They do not define a required interface
that every member must implement.

These concepts can be combined, but they remain separate:

- an abstract package can be a member of a package set;
- a package set can contain concrete and abstract packages;
- a package set can expose aggregate intent metadata;
- a package set does not make members conform to the aggregate intent.

## Discovery Semantics

Package discovery should remain index-based, not tree-traversal-based.

Exact `intent.*` lookup should be able to return both aggregate and scoped
results. A consumer should not need to know whether the useful result lives at
the repository root, a member package, or a related package.

Example result model:

```json
{
  "intent": "intent.ui.node_based_editor",
  "results": [
    {
      "package": "xyflow.workspace",
      "version": "0.1.0",
      "scope": "aggregate"
    },
    {
      "package": "xyflow.react",
      "version": "0.1.0",
      "scope": "package"
    }
  ]
}
```

The relation graph explains why results are connected after discovery. It should
not be required to find the first useful result.

## Xyflow Reference Shape

The intended `xyflow` reference scenario is:

```text
xyflow.workspace
  summary: xyflow workspace for node-based editors and interactive flow systems
  role: aggregate entrypoint

xyflow.system
  summary: shared system layer powering React Flow and Svelte Flow
  role: scoped package

xyflow.react
  summary: React package for building node-based editors and interactive flow charts
  role: scoped package

xyflow.svelte
  summary: Svelte package for building node-based editors and interactive flow charts
  role: scoped package
```

The aggregate package preserves the broad product meaning. The scoped packages
preserve evidence discipline and capability ownership.

## Acceptance Rules

Before a package-set proposal is accepted into the public index, maintainers
should verify:

- the package set and every proposed member package have separate package
  identities and versions;
- member relationships are explicit and reviewable;
- aggregate summaries do not imply member capabilities that are not declared by
  the member package;
- member packages do not inherit lifecycle, acceptance, trust, or namespace
  status from the package set;
- producer receipts and diagnostics remain evidence only;
- every accepted package/version is represented by an explicit maintainer
  decision or accepted-source diff.

Maintainers may accept a package set without accepting every proposed member, and
may accept a member package without accepting the aggregate set.

## Future Work

Follow-up tasks should define:

- public `/v0` registry metadata shape;
- SpecHarvester monorepo discovery handoff;
- multi-package producer bundle intake;
- an `xyflow` reference fixture.

Relation vocabulary and evidence expectations are defined in
`specs/PACKAGE_RELATIONS.md`.
Index and exact search result scope are defined in `specs/PACKAGE_SET_SEARCH.md`.
