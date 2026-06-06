# SpecHarvester Monorepo Discovery Contract

Status: Draft
Updated: 2026-06-06
Scope: SpecHarvester-to-SpecPM contract for monorepo package-set discovery

## Purpose

This document defines the SpecPM-side contract for producer tools, especially
SpecHarvester, when they discover a multi-package repository and propose a
package-set candidate plus scoped member package candidates.

The contract describes review evidence. It does not make SpecHarvester a
registry authority, does not require SpecPM to run SpecHarvester, and does not
accept generated packages automatically.

## Boundary

SpecHarvester owns:

- repository and workspace discovery;
- package manifest inspection;
- source and documentation harvesting;
- stable package ID proposal;
- package-set candidate generation;
- scoped member package candidate generation;
- relation proposal output;
- producer receipts, validation reports, diagnostics, and previews.

SpecPM owns:

- package validation;
- public-index accepted-source review;
- package-set and relation contract definitions;
- registry metadata generation after merge;
- maintainer acceptance decisions.

The handoff is:

```text
monorepo discovery evidence -> producer candidate bundle set -> SpecPM review
```

not:

```text
monorepo discovery evidence -> automatic public-index acceptance
```

## Discovery Inputs

A monorepo discovery run should record:

- repository URL;
- exact source revision;
- target root path;
- workspace manifest paths, such as `pnpm-workspace.yaml`,
  `package.json#workspaces`, `turbo.json`, or equivalent;
- package manifest paths;
- package README or documentation paths;
- public interface index paths, when generated;
- generation configuration digest;
- producer identity and version;
- privacy and redaction policy.

Inputs should be recorded in `producer-receipt.json` or an associated discovery
report so reviewers can determine what influenced the candidate output.

## Workspace Inventory

The producer should emit a machine-readable workspace inventory before drafting
packages.

Example shape:

```json
{
  "apiVersion": "specpm.producer/v0",
  "kind": "SpecHarvesterMonorepoDiscovery",
  "repository": {
    "url": "https://github.com/xyflow/xyflow",
    "revision": "<40-char-sha>"
  },
  "workspace": {
    "root": ".",
    "manifests": [
      "pnpm-workspace.yaml",
      "package.json"
    ]
  },
  "packages": [
    {
      "path": "packages/system",
      "ecosystem": "npm",
      "name": "@xyflow/system",
      "proposedPackageId": "xyflow.system",
      "role": "core_runtime"
    },
    {
      "path": "packages/react",
      "ecosystem": "npm",
      "name": "@xyflow/react",
      "proposedPackageId": "xyflow.react",
      "role": "react_binding"
    }
  ]
}
```

The inventory is producer evidence. It is not accepted registry metadata until a
maintainer reviews and accepts the relevant package sources.

## Package ID Proposal Rules

Producer-proposed package IDs should be:

- stable across repeated runs at the same repository layout;
- readable by maintainers;
- scoped to the package subject, not the producer;
- free of local machine names, branch names, temporary directories, or prompt
  artifacts;
- distinct for aggregate and member packages.

For monorepos, preferred ID shape is:

```text
<repository-or-product>.<member>
```

Example:

```text
xyflow.workspace
xyflow.system
xyflow.react
xyflow.svelte
```

The producer may propose IDs. SpecPM maintainers still own public-index
acceptance and namespace policy.

## Candidate Bundle Set

A producer-backed monorepo proposal should provide a bundle set:

```text
candidate/
  xyflow.workspace/
    specpm.yaml
    specs/workspace.spec.yaml
    producer-receipt.json
    validation-report.json
    diagnostics.json
  xyflow.system/
    specpm.yaml
    specs/system.spec.yaml
    producer-receipt.json
    validation-report.json
    diagnostics.json
  xyflow.react/
    specpm.yaml
    specs/react.spec.yaml
    producer-receipt.json
    validation-report.json
    diagnostics.json
```

Each package candidate should remain independently reviewable. The aggregate
package-set candidate should not replace member package candidates.

## Relation Proposal Output

The producer should emit proposed relations separately from accepted registry
metadata.

Example:

```json
{
  "relations": [
    {
      "type": "contains",
      "source": "xyflow.workspace",
      "target": "xyflow.system",
      "evidence": [
        {
          "kind": "source_file",
          "path": "pnpm-workspace.yaml"
        }
      ],
      "reviewStatus": "producer_observed"
    }
  ]
}
```

`reviewStatus: producer_observed` means the relation is evidence only. It does
not become public registry metadata until maintainer review accepts it.

## Evidence Discipline

The producer should keep evidence scoped:

- repository-level README and docs may support the package-set summary;
- package-level manifests and docs should support scoped member summaries;
- source-unit evidence should support member capabilities and interfaces;
- broad repository claims should not be copied into every member package;
- member-only capabilities should not be re-exported by the package set unless a
  future explicit re-export profile defines that behavior.

This prevents the two common monorepo errors:

- overclaiming the whole repository from one scoped package; and
- losing repository-level discovery intent when only one package directory is
  harvested.

## Review Reports

For each candidate package, the producer should provide:

- `producer-receipt.json`;
- `validation-report.json`;
- `diagnostics.json`;
- source/evidence digest references;
- privacy status;
- human review requirement for `public_index_acceptance`.

For the bundle set, the producer should also provide:

- workspace inventory report;
- relation proposal report;
- preflight report covering all candidate packages;
- static preview evidence, when available.

## Acceptance Rules

Before accepting a monorepo producer proposal, maintainers should verify:

- package-set and member package candidates are independently valid;
- proposed IDs are stable and reviewable;
- aggregate claims are supported by repository-level evidence;
- member claims are supported by scoped package evidence;
- proposed relations use the documented relation vocabulary;
- relation evidence supports the relation type;
- producer receipts and diagnostics remain evidence only;
- every accepted package/version and accepted relation has an explicit
  maintainer decision or accepted-source diff.

Maintainers may accept only part of a generated bundle set.

## Non-Goals

This contract does not add:

- SpecPM execution of SpecHarvester;
- automatic package-set generation in SpecPM;
- automatic public-index acceptance;
- namespace ownership grants;
- dependency solving;
- semantic package selection;
- package execution;
- trust in producer output.

## Future Work

SpecHarvester implementation follow-up should add:

- workspace inventory output;
- package-set candidate generation;
- scoped member package generation;
- relation proposal output;
- bundle-set preflight;
- static viewer support for package-set previews.

SpecPM follow-up should add:

- package-set registry metadata generation;
- conformance fixtures;
- `xyflow` reference scenario.

Multi-package producer bundle intake policy is defined in
`specs/MULTI_PACKAGE_PRODUCER_INTAKE.md`.
