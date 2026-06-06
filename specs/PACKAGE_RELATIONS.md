# Package Relation Vocabulary

Status: Draft
Updated: 2026-06-06
Scope: package relation vocabulary, direction, evidence expectations, and
non-goals

## Purpose

This document defines the initial relation vocabulary for connecting
`SpecPackage` records and package sets.

Relations help users and downstream tools navigate from aggregate package sets
to scoped packages, from abstract contracts to concrete packages, and from old
package versions or subjects to newer replacements. Relations are reviewable
metadata. They do not create inheritance, trust, automatic selection, or
execution authority.

## Relation Model

A relation is a directed claim from one package subject to another package
subject.

Conceptually:

```yaml
relations:
  - type: contains
    target: xyflow.react
    summary: xyflow.workspace includes the React Flow package.
    evidence:
      - kind: source_file
        path: pnpm-workspace.yaml
```

The first implementation may encode relations through extension-safe package
metadata before a stable schema exists. A future registry profile may normalize
relation records into `/v0` metadata.

Every relation should be interpreted as:

```text
source package --relation type--> target package
```

The source is the package that declares or publishes the relation. The target is
the related package subject.

## Vocabulary

### `contains`

Meaning:

- The source package set or aggregate package includes the target as a member.

Typical source:

- repository package set;
- workspace package set;
- ecosystem package set;
- product-family package set.

Typical target:

- scoped package;
- abstract package;
- concrete package;
- another package set.

Evidence expectations:

- workspace manifest;
- package manifest;
- repository layout;
- accepted-source manifest;
- maintainer decision record.

Non-goals:

- does not make the target inherit source capabilities;
- does not imply dependency;
- does not imply the target is accepted when the source is accepted;
- does not imply the source is accepted when the target is accepted.

### `composes`

Meaning:

- The source package combines the target package with other packages or
  contracts to form a larger reviewable contract.

Typical source:

- aggregate contract;
- integration package;
- product profile;
- curated package family.

Typical target:

- package that contributes one part of the aggregate behavior.

Evidence expectations:

- explicit package documentation;
- integration contract;
- architecture note;
- maintainer-authored package evidence.

Non-goals:

- does not imply a runtime dependency graph;
- does not solve versions;
- does not select providers automatically;
- does not execute target package content.

### `refines`

Meaning:

- The source package is a more specific contract than the target package.

Typical source:

- provider-specific package;
- platform-specific package;
- stricter package profile;
- concrete package generated from an abstract or intent-level contract.

Typical target:

- abstract package;
- broader interface package;
- earlier or less specific contract.

Evidence expectations:

- shared capability or intent mapping;
- explicit constraints that narrow the target contract;
- documentation explaining the specialization boundary;
- maintainer review that the source does not contradict the target.

Non-goals:

- does not copy target constraints into the source;
- does not prove conformance by itself;
- does not make the source a valid substitute in every downstream context.

### `satisfies`

Meaning:

- The source package claims to satisfy the target contract through evidence.

Typical source:

- concrete implementation package;
- adapter package;
- generated candidate package with reviewed evidence.

Typical target:

- abstract package;
- intent-level contract;
- required interface package.

Evidence expectations:

- explicit implemented capability mapping;
- test, API, documentation, or interface evidence;
- review report or maintainer decision;
- clear unsupported target requirements, if any.

Non-goals:

- does not remove the need for maintainer review;
- does not imply full compatibility unless the target contract requires and the
  evidence proves it;
- does not create runtime trust or execution authority.

### `supersedes`

Meaning:

- The source package replaces the target package for future discovery or
  maintenance purposes.

Typical source:

- newer package subject;
- renamed package;
- replacement package family;
- successor contract.

Typical target:

- deprecated package;
- renamed package;
- obsolete package subject.

Evidence expectations:

- changelog;
- deprecation notice;
- maintainer decision;
- registry lifecycle metadata.

Non-goals:

- does not delete the target package;
- does not yank the target package automatically;
- does not rewrite old lockfiles;
- does not imply the source is compatible with every target use.

### `related`

Meaning:

- The source package is connected to the target in a useful but weaker way that
  does not fit the stronger relation types.

Typical source and target:

- any package or package set.

Evidence expectations:

- short reason;
- evidence link when the relationship affects review or discovery.

Non-goals:

- should not be used when `contains`, `composes`, `refines`, `satisfies`, or
  `supersedes` is more precise;
- does not imply membership, compatibility, dependency, or substitution.

## Evidence Rules

Relation evidence should answer:

- Who or what asserts the relationship?
- Which source and target package identities are involved?
- Which package versions or version ranges are affected?
- What file, manifest, decision, or documentation supports the relation?
- Is the relation producer-observed, maintainer-reviewed, or accepted registry
  metadata?

Producer-observed relations are evidence only. Maintainer-reviewed relations may
be accepted into registry metadata through the normal accepted-source flow.

## Acceptance Rules

Before accepting a relation into public registry metadata, maintainers should
verify:

- relation type is the most precise available vocabulary term;
- source and target package IDs are stable and reviewable;
- version scope is explicit or intentionally package-wide;
- evidence supports the selected relation type;
- relation text does not imply inherited capabilities, trust, lifecycle, or
  namespace ownership;
- producer receipts remain evidence only;
- acceptance is recorded outside producer output.

Maintainers may accept a package without accepting all proposed relations, and
may accept a relation after both package subjects already exist in the registry.

## Search Boundary

Relations may improve navigation after discovery, but exact search should not
depend on walking relation paths.

For example, a query for:

```text
intent.ui.node_based_editor
```

may return both:

```text
xyflow.workspace scope=aggregate
xyflow.react scope=package
```

The `contains` relation explains why those results are connected. It should not
be required for the user to discover `xyflow.react` in the first place.

## Future Work

Follow-up tasks should define:

- extension-safe relation storage shape;
- static `/v0` relation metadata;
- relation rendering in the static viewer;
- SpecHarvester relation proposal output;
- multi-package producer bundle intake checks.

Exact search result scope and relation-context search boundaries are defined in
`specs/PACKAGE_SET_SEARCH.md`.
