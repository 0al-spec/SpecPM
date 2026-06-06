# Multi-Package Producer Bundle Intake

Status: Draft
Updated: 2026-06-06
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
- package-set candidate bundle;
- scoped member package candidate bundles;
- relation proposal report;
- producer receipt for each candidate package;
- validation report for each candidate package;
- diagnostics report for each candidate package;
- bundle-set preflight report;
- static preview evidence, when available;
- proposed accepted-source diff;
- maintainer acceptance decision records or review notes.

Each candidate package remains independently reviewable.

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

Future CI preflight may check:

- required evidence roles are present for each candidate package;
- candidate package IDs are unique within the bundle set;
- receipts do not hash themselves;
- output digests match package files;
- relation proposal source and target package IDs exist in the bundle set or
  current registry metadata;
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

