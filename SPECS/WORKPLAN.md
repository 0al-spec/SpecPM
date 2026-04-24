# SpecPM MVP Workplan

Status: Draft
Created: 2026-04-23
Updated: 2026-04-24
Input: `PRD.md`, `RFC/SpecGraph-RFC-0001.md`, current SpecGraph SpecPM bridge

## Working Rules

- Keep the MVP local-first.
- Implement the package manager around `SpecPackage` and `BoundarySpec`, not
  around arbitrary Markdown.
- Treat every package file as untrusted data.
- Prefer deterministic machine-readable outputs over implicit CLI prose.
- Do not implement remote registry, signing, semantic search, or automatic
  SpecGraph canonical mutation in the MVP.
- Treat Docker as the default reproducible execution boundary for development,
  validation, CI parity, and cross-project handoff.

## Phase 0. Repository Baseline

- [x] Choose the implementation language and package layout: Python package
  under `src/specpm`.
- [x] Add a minimal CLI entry point named `specpm`.
- [x] Add test runner, linting, formatting, and CI.
- [x] Add Dockerfile and Compose service for reproducible local execution.
- [x] Add examples directory with a minimal valid package from RFC 0001.
- [x] Add JSON fixture for the current
  `.specgraph_exports/specgraph.core_repository_facade` bundle.
- [x] Decide where generated local state lives:
  `.specpm/`, `specpm.lock`, and `.specpm/index.json`.

Acceptance:

- `specpm --help` runs locally.
- Test suite runs from a clean checkout.
- The RFC example is present as a test fixture.
- Docker can run `specpm validate examples/email_tools --json`.

## Phase 1. Core Data Loading

- [x] Implement restricted YAML loading for JSON-compatible data.
- [x] Reject or report unsupported YAML constructs: anchors, aliases, custom
  tags, multiple documents, executable tags, and binary blobs.
- [x] Add package path discovery for directory packages.
- [x] Load `specpm.yaml` into an internal manifest object.
- [x] Resolve referenced spec paths relative to package root.
- [x] Load `BoundarySpec` documents into internal spec objects.
- [x] Preserve unknown `x-` extension fields.
- [x] Reject unknown non-extension top-level fields where the RFC requires it.

Acceptance:

- Valid fixtures load successfully.
- Malformed YAML produces structured errors.
- Path resolution cannot escape the package root.

## Phase 2. Validator

- [x] Implement manifest required-field checks.
- [x] Implement supported `apiVersion` and `kind` checks.
- [x] Implement package ID validation.
- [x] Implement SemVer validation for package and spec versions.
- [x] Implement BoundarySpec required-field checks.
- [x] Implement capability ID validation.
- [x] Ensure manifest-level provided capabilities are declared by referenced
  BoundarySpecs.
- [x] Add duplicate ID checks.
- [x] Add evidence, foreign artifact, and implementation binding path checks as
  warnings.
- [x] Add warning for manual-assertion-only evidence.
- [x] Emit JSON validation reports.

Acceptance:

- `specpm validate <package-dir>` exits non-zero for invalid packages.
- `specpm validate <package-dir> --json` emits stable `errors[]` and
  `warnings[]`.
- The current SpecGraph materialized draft bundle is valid or warning-only;
  any draft-specific gaps are explicit.

## Phase 3. Inspect

- [x] Implement human-readable `specpm inspect <package-dir>`.
- [x] Implement `specpm inspect <package-dir> --json`.
- [x] Summarize package identity, license, capabilities, requirements, and
  compatibility metadata.
- [x] Summarize BoundarySpec intent, bounded context, interfaces, constraints,
  evidence, and provenance in JSON.
- [x] Add full BoundarySpec scope, effects, foreign artifacts, and
  implementation bindings to inspect summaries.
- [x] Surface provenance confidence prominently in human-readable output.
- [x] Surface security-sensitive effects and capabilities as warnings.

Acceptance:

- Inspecting the RFC example gives a compact contract summary.
- Inspecting the SpecGraph bundle shows `specgraph.repository_facade`, draft
  boundary status, and evidence paths.
- SpecGraph `handoff.json` continuity is surfaced by `specpm inbox inspect`.

## Phase 4. Deterministic Pack

- [x] Define the MVP archive format and extension: `specpm-tar-gzip-v0`,
  emitted as `.specpm.tgz`.
- [x] Collect manifest, referenced specs, evidence, foreign artifacts, optional
  README-like files, and sidecar files.
- [x] Normalize file ordering and timestamps for deterministic output.
- [x] Reject symlink escapes and path traversal.
- [x] Run validation before packing.
- [x] Emit digest metadata.
- [x] Add `specpm pack <package-dir> -o <archive>`.

Acceptance:

- Packing the same package twice produces the same digest.
- Invalid packages are not packed unless an explicit future unsafe flag is
  introduced.
- Package code or scripts are never executed.

## Phase 5. Local Registry Index

- [x] Define a small file-backed index schema.
- [x] Add `specpm index <package-dir-or-archive> --index <path>`.
- [x] Store package ID, version, digest, manifest summary, capabilities,
  requirements, license, compatibility metadata, evidence summary, and yanked
  state.
- [x] Reject duplicate `metadata.id` + `metadata.version` entries unless
  digest matches and operation is idempotent.
- [x] Add index validation tests.

Acceptance:

- A local index can be rebuilt from fixtures.
- Duplicate version conflicts are explicit.
- The index can be consumed without loading every full package.

## Phase 6. Search

- [x] Add `specpm search <capability-id> --index <path>`.
- [x] Implement exact capability ID matching.
- [x] Return package ID, version, summary, capabilities, license,
  compatibility, and confidence summary.
- [x] Add `--json` output.
- [x] Keep keyword/fuzzy search out of normative MVP resolution.

Acceptance:

- Searching for a capability from the RFC fixture returns that package.
- Searching for `specgraph.repository_facade` returns the SpecGraph bundle once
  it has been indexed.
- Unknown capabilities return an empty result, not an error.

## Phase 7. Add and Lock

- [x] Define minimal `specpm.lock`.
- [x] Define local install/cache path under `.specpm/packages/`.
- [x] Add `specpm add <capability-id-or-package-ref> --index <path>`.
- [x] Resolve exact package refs directly.
- [x] Resolve capability IDs through exact search.
- [x] Select highest stable compatible version when unambiguous.
- [x] Return ambiguity as a structured review-required result.
- [x] Write deterministic lockfile entries.
- [x] Copy or reference package archive/source into local project state.

Acceptance:

- Adding a unique capability writes deterministic lock metadata.
- Ambiguous capability resolution does not choose silently.
- Re-running add is idempotent when the same package is selected.

## Phase 8. SpecGraph Inbox

- [x] Add `specpm inbox list --root .specgraph_exports --json`.
- [x] Add `specpm inbox inspect <package-id> --root .specgraph_exports --json`.
- [x] Detect bundles containing `specpm.yaml`, `specs/main.spec.yaml`, and
  optional `handoff.json`.
- [x] Validate discovered bundles through the same validator.
- [x] Surface handoff continuity fields when `handoff.json` exists.
- [x] Classify bundle status as `draft_visible`, `ready_for_review`,
  `invalid`, or `blocked`.
- [x] Ensure inbox commands never mutate SpecGraph canonical files.

Acceptance:

- The local `specgraph.core_repository_facade` bundle is listed.
- The bundle inspection JSON can drive a viewer card.
- Missing or malformed bundle files produce actionable gaps.

## Phase 9. Structural Diff

- [x] Add `specpm diff <old-package-dir> <new-package-dir> --json`.
- [x] Detect removed and added capabilities.
- [x] Detect removed interfaces.
- [x] Detect changed required capabilities.
- [x] Detect changed MUST constraints.
- [x] Detect changed package metadata and compatibility metadata.
- [x] Classify likely breaking changes conservatively.

Acceptance:

- Diff detects removal of a provided capability as breaking.
- Diff detects added optional capability as non-breaking or review-required.
- Diff output is stable enough for tests and viewer rendering.

## Phase 10. Viewer Contract Stabilization

- [x] Document JSON schemas for validation, inspect, search, add, inbox list,
  inbox inspect, pack result, and diff result.
- [x] Add golden JSON fixtures.
- [x] Keep status vocabularies stable.
- [x] Add examples for rendering package cards and capability search results.
- [x] Align field names with the SpecGraph lifecycle where useful, without
  importing SpecGraph-specific concepts into core package validation.

Acceptance:

- A viewer can render package validity, capabilities, evidence state, and
  inbox status without scraping CLI prose.
- JSON fixtures are covered by tests.

## Phase 11. Release Hardening

- [x] Add end-to-end tests for validate, inspect, pack, index, search, add,
  inbox, and diff.
- [x] Add corrupted package tests.
- [x] Add path traversal and symlink escape tests.
- [x] Add large evidence path smoke test.
- [x] Add CLI exit code contract.
- [ ] Update README with MVP commands.
- [ ] Mark RFC 0001 implementation coverage in docs.

Acceptance:

- Full test suite passes from clean checkout.
- README has enough commands for a new user to validate and inspect a package.
- The MVP does not require network access.

## Post-MVP Tracks

- Remote registry API.
- `specpm publish`.
- Package yanking semantics.
- Package signing and trust policies.
- Namespace governance.
- Natural-language or semantic capability search.
- Full dependency solving.
- Conformance test artifacts.
- Richer import adapters for CodeSpeak, OpenAPI, GraphQL, protobuf, AsyncAPI,
  README, ADR, package manifests, test metadata, and source-level public API
  summaries.
- Cross-repo PR workflow automation with SpecGraph.
- SpecGraph feedback promotion from observed downstream adoption into explicit
  proposal-lane candidates.
