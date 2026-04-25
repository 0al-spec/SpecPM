# SpecPM MVP PRD

Status: Draft
Created: 2026-04-23
Updated: 2026-04-25
Owner: SpecPM
Primary source: `RFC/SpecGraph-RFC-0001.md`

## 1. Product Summary

SpecPM is a package manager for reusable software intent. The MVP manages
boundary-first specification packages, not implementation packages.
SpecPM is the package substrate for SpecGraph: it packages, validates, indexes,
and exposes reusable specification intent. It does not own graph reasoning,
artifact generation, prompt execution, or artifact evaluation runtime.

The first useful product loop is:

1. Author or receive a directory with `specpm.yaml` and at least one
   `BoundarySpec`.
2. Validate that package without executing any package content.
3. Inspect the package contract, evidence, capabilities, and provenance.
4. Pack the package deterministically.
5. Index packages by exact capability IDs.
6. Search and add packages into a consuming project through explicit,
   reviewable metadata.
7. Accept draft bundles produced by SpecGraph under `.specgraph_exports/`
   as reviewable package candidates.

SpecPM MVP should make specification reuse concrete before remote publishing,
marketplace governance, semantic search, or automatic graph mutation exist.

## 2. Problem

SpecGraph can refine and observe internal specification structure, but reusable
boundary contracts need a package-shaped exchange format. Without SpecPM, a
bounded specification region can be exported as files, but there is no dedicated
tool that can validate, inspect, pack, index, and import that package as a
first-class specification dependency.

The MVP must solve the practical local workflow first:

- package authors need a minimal format and validator;
- package consumers need exact capability lookup and inspection;
- SpecGraph needs a downstream package consumer that can receive
  `.specgraph_exports/<package_id>/` bundles without treating them as published
  or canonical automatically;
- reviewers need deterministic artifacts and clear failure messages.

## 3. Goals

- Implement the RFC 0001 minimal package model for `SpecPackage` and
  `BoundarySpec`.
- Provide a CLI that validates, inspects, packs, indexes, searches, and adds
  local packages.
- Provide a Docker-based development and execution baseline so the MVP can be
  run reproducibly from a clean checkout without relying on host-specific tool
  state.
- Keep package contents untrusted: no script execution, no automatic remote
  fetches, no implicit code execution from Markdown or foreign artifacts.
- Support exact capability ID search as the normative MVP resolution behavior.
- Preserve evidence, provenance, foreign artifacts, and implementation bindings
  as data.
- Support SpecGraph materialized bundles under `.specgraph_exports/` as local
  draft package candidates.
- Produce machine-readable outputs that a viewer can render.

## 4. Non-Goals

- Remote public registry hosting.
- Package signing and trust web.
- AI semantic search as normative resolution.
- Full dependency solving.
- Automatic code generation.
- Automatic import into SpecGraph canonical specs.
- Marketplace governance.
- Full semantic diffing.
- Running tests or package scripts during validation.
- PRD, brief, issue breakdown, test plan, or other derived artifact generation.
- Artifact evaluation runtime.
- Package-provided prompt or generation instruction execution.

These can be post-MVP tracks once the local package loop is stable.

## 5. Primary Users

- Package author: creates `specpm.yaml`, `BoundarySpec`, evidence, and foreign
  artifact references.
- Package consumer: searches by exact capability, inspects candidates, and adds
  selected package metadata into a local project.
- SpecGraph operator: materializes or reviews SpecGraph-originated
  `.specgraph_exports/<package_id>/` bundles in the SpecPM checkout.
- Viewer developer: needs compact JSON outputs for package status, validation
  errors, capability indexes, and imported package state.

## 6. MVP Package Contract

The canonical package layout is:

```text
my-package/
  specpm.yaml
  specs/
    main.spec.yaml
  evidence/
  foreign/
```

Required files:

- `specpm.yaml`
- at least one referenced `BoundarySpec` document

Required manifest fields:

- `apiVersion`
- `kind: SpecPackage`
- `metadata.id`
- `metadata.name`
- `metadata.version`
- `metadata.summary`
- `metadata.license`
- `specs`
- `index.provides.capabilities`

Required BoundarySpec fields:

- `apiVersion`
- `kind: BoundarySpec`
- `metadata.id`
- `metadata.title`
- `metadata.version`
- `intent.summary`
- `scope.boundedContext`
- `provides.capabilities`
- `interfaces`
- `evidence`

The accepted authoring format is restricted YAML using JSON-compatible maps,
arrays, strings, numbers, booleans, and null values. Anchors, aliases, custom
tags, multiple documents, executable tags, and implicit non-JSON scalar tricks
must be rejected or reported as unsupported.

## 7. MVP CLI

The MVP CLI should expose these commands:

```bash
specpm validate <package-dir>
specpm inspect <package-ref-or-dir> [--json]
specpm pack <package-dir> [-o <archive>]
specpm index <package-dir-or-archive> [--index <path>]
specpm search <capability-id> [--index <path>] [--json]
specpm add <capability-id-or-package-ref> [--index <path>] [--project <dir>]
specpm diff <old-package-dir> <new-package-dir> [--json]
specpm inbox list [--root .specgraph_exports] [--json]
specpm inbox inspect <package-id> [--root .specgraph_exports] [--json]
```

`publish` is RFC-defined but should stay post-MVP unless a local fake registry
needs it for tests. The MVP should not imply remote distribution before local
validation, packing, and indexing are reliable.

## 8. Validation Requirements

`specpm validate` must check:

- manifest exists;
- manifest parses successfully;
- `apiVersion` is supported;
- manifest `kind` is `SpecPackage`;
- required manifest fields exist;
- package ID matches the RFC pattern;
- package version is valid SemVer;
- referenced spec files exist;
- referenced spec files parse successfully;
- BoundarySpec `kind` is `BoundarySpec`;
- required BoundarySpec fields exist;
- manifest capabilities are declared by specs;
- capability IDs match the RFC pattern.

It should warn, not necessarily fail, on:

- missing evidence paths;
- missing foreign artifact paths;
- missing implementation binding paths;
- duplicate IDs;
- empty summaries;
- unresolved required capabilities;
- unknown interface kinds;
- unknown effect kinds;
- manual-assertion-only evidence.

Validation output must be available as JSON with:

- `status`
- `error_count`
- `warning_count`
- `errors[]`
- `warnings[]`
- `package_identity`
- `capabilities`
- `checked_files`

## 9. Packing Requirements

`specpm pack` must:

- run validation first;
- produce a deterministic archive;
- include `specpm.yaml`, referenced specs, local evidence files, local foreign
  artifacts, and optional README-like files;
- preserve extension fields beginning with `x-`;
- reject path traversal and symlink escapes;
- never execute package code or scripts;
- emit archive digest metadata.

The MVP archive format is `specpm-tar-gzip-v0`, emitted with the
`.specpm.tgz` extension. Archives use stable file order, normalized ownership,
and normalized timestamps.

## 10. Index, Search, and Add Requirements

The local MVP registry index should store:

- `schemaVersion`
- package ID;
- version;
- archive or source digest;
- manifest summary;
- provided capabilities;
- required capabilities;
- license;
- compatibility metadata;
- evidence summary;
- yanked flag, default false for local indexes.

`specpm search` must support exact capability ID matching. Keyword or fuzzy
search can exist only as advisory UX, not normative resolution.

`specpm add` should:

1. resolve exact package reference or exact capability ID;
2. reject invalid or yanked packages;
3. choose the highest stable compatible version when only one package remains;
4. ask for selection or return a machine-readable ambiguity error when multiple
   packages remain;
5. write deterministic project metadata.

The initial project metadata can be:

- `specpm.lock`
- `.specpm/index.json`
- `.specpm/packages/<package_id>/<version>/`

The lockfile format should stay small and deterministic.

## 11. Inspect and Diff Requirements

`specpm inspect` should display:

- intent summary;
- provided and required capabilities;
- interfaces;
- constraints;
- effects;
- evidence;
- foreign artifacts;
- compatibility metadata;
- version;
- license;
- provenance confidence.

The MVP may stage this surface: baseline package identity, capabilities,
interfaces, constraints, evidence, and provenance can ship before the fuller
effects, foreign artifact, implementation binding, and security-warning
summaries. SpecGraph handoff continuity belongs to `specpm inbox inspect`, not
plain package inspection.

The inspection JSON should expose advisory `contract_warnings[]` separately
from validation warnings. These warnings do not affect validation status; they
highlight contract facts that a reviewer or viewer should notice, including
security-sensitive effects and security-sensitive provided or required
capabilities.

`specpm diff` should initially operate on package directories. Archive diff can
be added after archive inspection is promoted beyond indexing.

`specpm diff` should detect at least:

- removed capabilities;
- added capabilities;
- removed interfaces;
- changed required capabilities;
- changed MUST constraints;
- changed package metadata;
- changed compatibility metadata.

The diff is structural and conservative. Full semantic diffing is post-MVP.

## 12. SpecGraph Integration

SpecGraph already materializes draft bundles into the SpecPM checkout under:

```text
.specgraph_exports/<package_id>/
  specpm.yaml
  specs/main.spec.yaml
  evidence/source/
  handoff.json
```

SpecPM MVP should treat this path as a local inbox, not as a published registry.

Inbox commands must:

- list discovered bundles;
- validate `specpm.yaml`;
- validate `specs/main.spec.yaml`;
- preserve and display `handoff.json`;
- show whether a bundle is draft-only or reviewable;
- expose JSON suitable for viewer overlays;
- never mutate upstream SpecGraph canonical specs.

The initial known bundle is:

- package ID: `specgraph.core_repository_facade`
- capability: `specgraph.repository_facade`
- status: draft materialized preview

SpecGraph-side artifacts that shaped this contract:

- `specpm_export_preview`
- `specpm_handoff_packets`
- `specpm_materialization_report`
- `specpm_import_preview`
- `specpm_import_handoff_packets`
- `specpm_delivery_workflow`
- `specpm_feedback_index`

SpecPM should not reimplement SpecGraph governance. It should provide a stable
consumer-side package tool that can be observed by SpecGraph.

## 13. Derived Artifacts Boundary

SpecPM is the package substrate for SpecGraph. Its responsibility is to
package, validate, index, inspect, diff, and preserve reusable specification
intent.

SpecPM is not the runtime responsible for generating PRDs, implementation
briefs, design briefs, onboarding documents, issue breakdowns, test plans, or
other derived artifacts. Derived artifacts are downstream outputs produced from
`SpecPackage` and `BoundarySpec` data by SpecGraph, ContextBuilder, or other
downstream tools.

PRDs, briefs, issue breakdowns, and test plans are not canonical truth inside
SpecPM. The canonical material handled by SpecPM is the package data itself.
SpecPM may carry intent; SpecGraph decides meaning.

SpecPM core MUST NOT execute package-provided prompts, generation instructions,
or artifact workflows. SpecPM core MUST NOT treat package content as trusted
instructions to the host. Package content can describe desired outputs. Package
content cannot command the host.

Any future support for derived artifact metadata or artifact evaluation
profiles MUST be introduced as a post-MVP profile and MUST NOT change the MVP
package manager boundary.

## 14. Viewer-Facing JSON Surfaces

Every command that can drive a viewer should support `--json`.

Minimum JSON surfaces:

- validation report;
- package inspection report;
- local registry index;
- search result list;
- add/import result;
- inbox bundle list;
- inbox bundle inspection.

Status names should be explicit and stable enough for UI badges, for example:

- `valid`
- `invalid`
- `warning_only`
- `draft_visible`
- `ready_for_review`
- `blocked`

## 15. Success Metrics

The MVP is successful when:

- the RFC example package validates;
- the current `.specgraph_exports/specgraph.core_repository_facade` bundle can
  be listed, validated, and inspected;
- a valid package can be packed deterministically twice with the same digest;
- exact capability search finds a package from a local index;
- `specpm add` writes deterministic project metadata;
- invalid packages produce actionable JSON errors without crashing;
- no command executes package-provided code.

## 16. Release Boundary

The first MVP release should be local-first:

- CLI and library in one repository;
- Docker image and Compose service for local validation, tests, and scripted
  CLI execution;
- file-backed local registry index;
- deterministic archives;
- reviewable SpecGraph inbox;
- no remote service dependency.

The next release can consider remote publish/search, package signing, richer
dependency solving, formal registry APIs, and explicitly deferred derived
artifact profiles.

## 17. Implementation Environment

The MVP implementation should maintain two supported execution paths:

- local Python development with `python -m pip install -e ".[dev]"`;
- Docker execution with `docker compose run --rm specpm <command>`.

Docker is the preferred reproducibility boundary for task execution, CI parity,
and handoff between SpecPM, SpecGraph, and ContextBuilder workspaces. Runtime
commands must not require network access after the image has been built.
