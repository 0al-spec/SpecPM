# SpecPM MVP Workplan

Status: Draft
Created: 2026-04-23
Updated: 2026-04-26
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
- Keep derived artifact generation, package-provided prompt execution, and
  artifact evaluation runtime outside SpecPM core.
- SpecPM may carry intent; SpecGraph decides meaning.
- Package content can describe desired outputs. Package content cannot command the host.

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
- [x] Update README with MVP commands.
- [x] Mark RFC 0001 implementation coverage in docs.

Acceptance:

- Full test suite passes from clean checkout.
- README has enough commands for a new user to validate and inspect a package.
- The MVP does not require network access.

## Phase 12. Local Registry Lifecycle

- [x] Add `specpm yank <package-id@version> --index <path> --reason <reason>`.
- [x] Add `specpm unyank <package-id@version> --index <path>`.
- [x] Preserve yanked packages in exact search results with `yanked: true`.
- [x] Keep `specpm add` rejection for yanked packages.
- [x] Make yank and unyank idempotent when the index is already in the requested
  state.
- [x] Emit stable JSON lifecycle reports.
- [x] Document lifecycle command exit codes and JSON contracts.

Acceptance:

- Yanking an indexed package sets `yanked: true` and stores a deterministic
  reason without removing the package from the local index.
- Unyanking clears local yanked metadata and allows `specpm add` to select the
  package again.
- Invalid package refs and missing index entries produce structured errors.
- The lifecycle commands work through Docker and local Python execution.

## Phase 13. Conformance Test Artifacts

- [x] Define the first local conformance suite format.
- [x] Add a portable JSON suite manifest.
- [x] Add fixture packages for valid, invalid, and warning-only validation
  outcomes.
- [x] Add a registry lifecycle conformance case for index, search, yank, add
  rejection, unyank, and add success.
- [x] Add tests that verify the conformance artifacts remain aligned with
  implementation behavior.
- [x] Document conformance artifact scope and non-goals.

Acceptance:

- The conformance suite is data-only and repository-relative.
- The conformance fixtures do not require package code execution.
- Tests fail if the documented conformance expected outcomes drift from current
  SpecPM behavior.
- The conformance artifacts do not introduce remote registry, signing, graph
  reasoning, artifact generation, or agent runtime behavior.

## Phase 14. Remote Registry API Contract

- [x] Define a read-only remote registry API v0 contract.
- [x] Document package metadata lookup.
- [x] Document package version lookup.
- [x] Document exact capability search.
- [x] Document yanked and deprecated version state.
- [x] Document stable registry error payloads.
- [x] Add static JSON fixtures for representative registry responses.
- [x] Add conformance cases that validate registry payload shape without
  starting a server or performing network requests.

Acceptance:

- The remote registry API contract is documented as post-MVP.
- The contract does not implement `specpm publish`.
- The contract does not implement a remote client, remote server, auth, signing,
  namespace governance, dependency solving, semantic search, or remote yanking
  mutation workflow.
- Static fixtures cover package metadata, package version, exact capability
  search, yanked version visibility, and not-found errors.
- Tests fail if documented remote registry payload fixtures drift from the
  expected contract shape.

## Phase 15. Read-Only Remote Registry Client

- [x] Add `specpm remote package <package-id> --registry <url>`.
- [x] Add `specpm remote version <package-id@version> --registry <url>`.
- [x] Add `specpm remote search <capability-id> --registry <url>`.
- [x] Fetch only explicit read-only registry metadata endpoints.
- [x] Validate remote registry payload shape before returning a successful
  report.
- [x] Return stable JSON client reports for `ok`, `not_found`, and `invalid`
  outcomes.
- [x] Reject invalid package IDs, package refs, capability IDs, registry URLs,
  and timeouts before network access.
- [x] Keep archive download, local install/cache, publish, auth, signing,
  namespace governance, remote yanking mutation, and semantic search out of
  scope.

Acceptance:

- Remote package, version, and exact capability search commands produce stable
  JSON reports.
- Remote error payloads remain machine-readable and produce non-zero CLI exits.
- Client tests use fixture-backed HTTP fetch stubs and do not require a live
  registry service.
- The client never executes package content and never downloads package
  archives as a side effect of reading metadata.

## Phase 16. Public Index Submission Template

- [x] Add a GitHub Issue form for `Add SpecPackage(s)` submissions.
- [x] Collect one public Git repository URL per line.
- [x] Allow an optional package path for repositories where `specpm.yaml` is
  not at the repository root.
- [x] Include submission acknowledgements for public visibility, SpecPM package
  files, no package execution during validation, and policy compliance.
- [x] Document that the issue form is public index intake, not `specpm publish`,
  remote mutation, enterprise auth, archive download/install, or package
  execution behavior.
- [x] Add lightweight tests that keep the issue form aligned with the documented
  public index submission contract.

Acceptance:

- The issue template is valid YAML and uses GitHub Issue Forms structure.
- The form requires repository URLs and submission acknowledgements.
- The form does not ask for credentials, tokens, private repository access,
  signing keys, or upload permissions.
- Documentation links the issue template to the public index flow while keeping
  enterprise registry deployment separate.

## Phase 17. Public Index Submission Validation Workflow

- [x] Add a GitHub Actions workflow for issues labeled `package-submission`.
- [x] Parse the `Add SpecPackage(s)` issue form body into repository URLs,
  package path, and notes.
- [x] Reject missing URLs, non-HTTPS URLs, credential-bearing URLs, URL
  fragments, absolute package paths, and package path traversal before cloning.
- [x] Shallow-clone submitted public repositories without submodules.
- [x] Run `specpm validate` against the submitted package path.
- [x] Post a markdown validation report back to the submission issue.
- [x] Fail the workflow for invalid submissions while still leaving a
  machine-readable and human-readable report.
- [x] Add tests for issue parsing, URL/path guards, workflow shape, report
  rendering, and validation through `specpm validate`.

Acceptance:

- The workflow only runs for the `package-submission` label.
- The workflow permissions are limited to repository read and issue comments.
- Submitted package content is validated as data and is not executed.
- The workflow does not publish packages, generate registry JSON, mutate remote
  registry state, download package archives, or install submitted packages.
- Invalid submissions produce an issue comment and a failing validation check.

## Phase 18. Public Static Index Generator

- [x] Add a `specpm public-index generate` command for static public registry
  metadata generation.
- [x] Accept one or more already-local package directories as generator inputs.
- [x] Validate and deterministically pack each package before publication into
  static output.
- [x] Emit remote registry API compatible package metadata, package version,
  and exact capability search payloads under `/v0`.
- [x] Emit JSON-body `index.html` copies so static hosts can serve
  extensionless registry endpoints.
- [x] Validate generated payloads against the remote registry contract before
  returning success.
- [x] Reject duplicate `package_id@version` inputs when archive digests differ.
- [x] Add tests for generated payload shape, archive digest/size/URL,
  duplicate conflict handling, and CLI JSON output.
- [x] Document that the generator is static metadata output, not `publish`,
  issue mutation, archive install/cache, or package execution behavior.

Acceptance:

- Generated `/v0` package, version, and capability payloads validate against
  the existing remote registry API contract.
- Output file order is deterministic and reviewable.
- Deterministic `.specpm.tgz` archives are generated only as static hosted
  source artifacts for metadata payloads.
- The command does not contact a remote registry, change GitHub issues, publish
  through a mutation API, install packages, or execute package content.

## Post-MVP Tracks

- Remote registry service implementation.
- Public SpecPM Index submission flow through GitHub Issues, Actions, and
  GitHub Pages.
- Enterprise remote registry deployment with private access control, audit, and
  policy enforcement.
- `specpm publish`.
- Remote package yanking governance.
- Package signing and trust policies.
- Namespace governance.
- Natural-language or semantic capability search.
- Full dependency solving.
- Expanded conformance suites for additional post-MVP tracks.
- Richer import adapters for CodeSpeak, OpenAPI, GraphQL, protobuf, AsyncAPI,
  README, ADR, package manifests, test metadata, and source-level public API
  summaries.
- Cross-repo PR workflow automation with SpecGraph.
- SpecGraph feedback promotion from observed downstream adoption into explicit
  proposal-lane candidates.

### Post-MVP Track: Public SpecPM Index Submission Flow

Status: Deferred.

#### Goal

Define a public package-index workflow where anyone can submit public
SpecPackage repositories through a GitHub Issue form. The index validates
submitted repositories through GitHub Actions, records review history in GitHub,
and publishes generated read-only registry metadata through GitHub Pages.

#### Boundary

- The public index is a submission queue, validation gate, and generated
  read-only metadata registry.
- The public index may store package references and generated registry JSON
  before it stores package archives.
- The public index should use the remote registry API contract for generated
  `/v0` metadata.
- The public index does not require a custom backend for the first iteration.
- The public index does not define enterprise authentication, private package
  visibility, package signing, remote mutation APIs, or archive install/cache
  behavior.

#### Future Investigation Areas

Future work may explore:

- Maintainer labels for accepted, rejected, duplicate, blocked, and needs-info
  submissions.
- Package removal request workflow.
- Namespace claim workflow.
- GitHub Pages deployment automation for generated public index output.

### Post-MVP Track: Enterprise Remote Registry

Status: Deferred.

#### Goal

Preserve the remote registry path for enterprise deployments that need private
packages, access control, audit, policy enforcement, internal namespace
ownership, and integration with company infrastructure.

#### Boundary

- Enterprise registry deployments may implement the same read-only metadata
  contract as the public index.
- Enterprise registry deployments may add authentication, authorization,
  private blob storage, signing policy, audit logs, retention policy, and
  approval workflows.
- These enterprise features should not be required for the public index MVP.
- Enterprise registry work must not turn SpecPM core into a package content
  execution runtime.

### Post-MVP Track: Derived Artifact Profile

Status: Deferred.

#### Goal

Explore an optional post-MVP profile that allows packages to carry metadata
useful to downstream artifact generation tools without making SpecPM an
artifact generator, eval runner, or agent runtime.

Derived artifacts may include:

- product requirements documents.
- implementation briefs.
- design briefs.
- onboarding documents.
- issue breakdowns.
- test plans.
- review reports.
- other downstream product or engineering artifacts.

#### Boundary

- SpecPM is the package substrate for SpecGraph.
- SpecPM may store, validate, inspect, and expose package data.
- SpecPM does not generate derived artifacts in core.
- SpecPM does not execute package-provided prompts, generation instructions, or
  artifact workflows.
- SpecPM does not run artifact evals in core.
- SpecPM does not grant package content authority over host behavior.
- SpecPM may carry intent; SpecGraph decides meaning.
- Package content can describe desired outputs. Package content cannot command the host.
- ContextBuilder or downstream tools are responsible for derived artifact
  generation and artifact-level evaluation.
- SpecGraph is responsible for product meaning, graph reasoning, refinement,
  proposal lanes, and canonical relationships across specs.

#### Non-Goals

- This track does not change the MVP package layout.
- This track does not replace `specpm.yaml + specs/*.spec.yaml`.
- This track does not introduce a Markdown-first package model.
- This track does not introduce a new package term alongside `SpecPackage` and
  `BoundarySpec`.
- This track does not introduce stable JSON fields in the MVP.
- This track does not change `inspect --json`.
- This track does not define an agent runtime.
- This track does not allow package content to override host policy, system
  instructions, developer instructions, security policy, runtime policy, or
  access controls.

#### Future Investigation Areas

Future work may explore:

- artifact descriptors.
- generation preferences for downstream tools.
- artifact evaluation profiles.
- source ID coverage checks.
- required section checks.
- out-of-scope promotion checks.
- open question preservation checks.
- assumption and risk preservation checks.
- traceability checks for generated artifacts.

These investigation areas are not part of the MVP contract.
