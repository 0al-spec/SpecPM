# SpecPM MVP Workplan

Status: Draft
Created: 2026-04-23
Updated: 2026-04-28
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

## Phase 19. Local Public Index Service

- [x] Add a Docker Compose `public-index` service for local read-only registry
  testing.
- [x] Generate `.specpm/public-index` before serving the static `/v0` tree.
- [x] Serve the generated public index at `http://localhost:8081` by default.
- [x] Add Make targets for `public-index-generate`, `public-index-up`,
  `public-index-smoke`, and `public-index-down`.
- [x] Allow local endpoint overrides with `SPECPM_PUBLIC_INDEX_PORT` and
  `SPECPM_PUBLIC_INDEX_REGISTRY_URL`.
- [x] Allow the generator to use localhost HTTP development registry URLs while
  still rejecting non-local insecure HTTP URLs.
- [x] Add tests for the compose service contract and localhost generator
  behavior.
- [x] Document the local service as an integration point for SpecGraph,
  ContextBuilder, and manual ecosystem testing.

Acceptance:

- `make public-index-up` starts a local static registry service.
- `make public-index-smoke` can read the service through the existing
  read-only remote metadata client.
- The generated local service remains read-only and does not add publish, auth,
  signing, issue mutation, package installation, or package execution behavior.

## Phase 20. Public Index Observation Surface

- [x] Add a read-only `/v0/status` static registry payload for downstream
  availability and profile observation.
- [x] Add a read-only `/v0/packages` static package index payload for visible
  package/version discovery.
- [x] Add `specpm remote status --registry <url>` and
  `specpm remote packages --registry <url>` client commands.
- [x] Validate registry status and package index payload shapes through the
  same remote registry contract validator.
- [x] Extend conformance fixtures for registry status and package index
  payloads.
- [x] Extend `make public-index-smoke` so local SpecGraph and ContextBuilder
  integrations can verify discovery before exact capability lookup.
- [x] Document the observation surface without adding publish, auth, signing,
  artifact generation, graph reasoning, archive download/install, or package
  execution behavior.

Acceptance:

- `make public-index-up` exposes `/v0/status` and `/v0/packages` through the
  static local registry service.
- `specpm remote status --registry http://localhost:8081 --json` returns a
  `RemoteRegistryStatus` payload.
- `specpm remote packages --registry http://localhost:8081 --json` returns a
  `RemotePackageIndex` payload.
- SpecGraph and ContextBuilder can use the observation surface as metadata-only
  evidence of package visibility.

## Phase 21. GitHub Pages Public Index Deployment

- [x] Generate static `/v0` public index metadata into the GitHub Pages artifact
  alongside the DocC documentation site.
- [x] Use the existing read-only `specpm public-index generate` command instead
  of adding a registry server or mutation API.
- [x] Configure the Pages registry base URL as the repository Pages URL.
- [x] Trigger the Pages build when public index generator code, example package
  input, package metadata, docs, or workflow files change.
- [x] Keep the Pages artifact root compatible with both `/documentation/specpm/`
  and `/v0` paths.
- [x] Add workflow-shape tests so CI catches drift in the DocC plus public index
  deployment contract.
- [x] Document that Pages deployment is generated static metadata only, not
  `specpm publish`, remote registry service implementation, auth, package
  installation, or package execution behavior.

Acceptance:

- Pushes to `main` build a Pages artifact containing DocC documentation and the
  generated static `/v0` public index tree.
- Pull requests validate the Pages artifact generation shape without deploying.
- The workflow installs SpecPM, runs `specpm public-index generate`, and uploads
  `.docc-build` as the Pages artifact.
- GitHub Pages deployment remains read-only static hosting.

## Phase 22. Public Index Accepted Package Manifest

- [x] Add a maintainer-reviewed accepted package manifest at
  `public-index/accepted-packages.yml`.
- [x] Allow `specpm public-index generate` to read repository-relative package
  directories from the accepted manifest while preserving explicit package
  directory inputs.
- [x] Reject missing manifests, invalid manifest shape, unknown package entry
  fields, absolute paths, and path escapes before package validation or
  packing.
- [x] Update the GitHub Pages documentation workflow to generate `/v0` metadata
  from the accepted manifest instead of hardcoded package arguments.
- [x] Update the local Docker Compose public-index service and Make targets to
  use the same accepted manifest by default.
- [x] Add tests for manifest path resolution, path escape rejection, CLI
  manifest generation, workflow shape, and compose service configuration.
- [x] Document that the accepted manifest is a reviewed static input source,
  not a remote mutation API, upload format, `specpm publish`, package
  installation, or package execution behavior.

Acceptance:

- Pull requests can review the accepted package source independently of
  generated Pages output.
- Pages and the local public-index service use the same default accepted package
  manifest.
- Accepted package entries are repository-relative local package directories.
- The manifest does not introduce remote publishing, issue mutation, auth,
  signing, archive install/cache behavior, or package execution.

## Phase 23. Public Index Pinned Remote Sources

- [x] Allow accepted package manifest entries to reference public HTTPS Git
  repositories with `repository`, `ref`, `revision`, and `path`.
- [x] Require a 40-character pinned commit revision for remote manifest
  entries.
- [x] Check out remote manifest entries without submodules or Git LFS smudging.
- [x] Verify that the checked out ref resolves to the pinned revision before
  package validation or packing.
- [x] Reject remote manifest URL credentials, query strings, fragments, unsafe
  refs, missing revisions, path escapes, and revision drift.
- [x] Keep accepted manifest generation static and read-only: no `publish`,
  auth, issue mutation, package installation, or package execution behavior.
- [x] Document the promotion path from validated submission issues to reviewed
  accepted manifest entries.

Acceptance:

- `specpm public-index generate --manifest public-index/accepted-packages.yml`
  still works for repository-local package paths.
- Remote manifest entries can be resolved into temporary checkouts for
  validation and static `/v0` generation.
- Generation fails if a reviewed ref no longer resolves to its pinned
  revision.
- Public index promotion remains a maintainer-reviewed manifest change, not a
  remote mutation API.

## Phase 24. Public Index Removal Request Intake

- [x] Add a GitHub Issue form for `Remove SpecPackage(s)` requests.
- [x] Collect package IDs or `package_id@version` references, requested removal
  scope, reason, rationale, and requester relationship.
- [x] Include acknowledgements that removal requests are maintainer-reviewed
  and do not automatically mutate the registry.
- [x] Document that removals happen through reviewed manifest or policy changes
  for future generated `/v0` snapshots.
- [x] Keep removal intake separate from `specpm publish`, remote mutation APIs,
  remote yanking workflows, package installation, credential intake, and
  package execution.
- [x] Add lightweight tests that keep the removal request form aligned with the
  public index boundary.

Acceptance:

- The issue template is valid YAML and uses GitHub Issue Forms structure.
- The form requires package references, removal scope, reason, rationale, and
  requester relationship.
- The form does not request credentials, tokens, private repository access,
  signing keys, or upload permissions.
- Documentation links removal requests to maintainer-reviewed static index
  changes without implying automatic deletion or registry mutation.

## Phase 25. Public Index Namespace Claim Intake

- [x] Add a GitHub Issue form for `Claim Namespace` requests.
- [x] Collect namespace or package ID prefix, claim scope, claimant identity,
  public evidence URLs, intended use, and public contact.
- [x] Include acknowledgements that namespace claims are maintainer-reviewed
  and do not automatically grant exclusive namespace ownership.
- [x] Document that namespace claims may inform package review, accepted-source
  context, or future public index policy.
- [x] Keep namespace claim intake separate from `specpm publish`, remote
  mutation APIs, authentication, authorization, enterprise namespace
  governance, package signing, package installation, credential intake, and
  package execution.
- [x] Add lightweight tests that keep the namespace claim form aligned with the
  public index boundary.

Acceptance:

- The issue template is valid YAML and uses GitHub Issue Forms structure.
- The form requires namespace prefix, claim scope, claimant identity, public
  evidence URLs, intended use, public contact, and acknowledgements.
- The form does not request credentials, tokens, private repository access,
  signing keys, or upload permissions.
- Documentation links namespace claim requests to maintainer-reviewed public
  index policy without implying automatic ownership, authentication, or
  registry mutation.

## Phase 26. Public Index Namespace Claim Review Policy

- [x] Add a public index namespace claim review policy document.
- [x] Define recommended review labels for needs-info, under-review, accepted,
  rejected, contested, and superseded claim states.
- [x] Define maintainer review criteria based on public evidence, namespace
  shape, conflicts, validation status, confusion risk, and policy concerns.
- [x] Define accepted, rejected, and contested claim outcomes.
- [x] Document a public dispute process for competing namespace claims.
- [x] Keep the policy separate from namespace ownership enforcement,
  authentication, authorization, enterprise namespace governance, remote
  mutation APIs, package signing, package installation, and package execution.
- [x] Add lightweight tests that keep the policy boundary explicit.

Acceptance:

- The policy is documented in `specs/NAMESPACE_CLAIM_POLICY.md`.
- The policy explains that namespace claims are public-index review evidence,
  not a machine-enforced ownership contract.
- The policy records how claims may be cited from reviewed accepted-source pull
  requests without directly editing `public-index/accepted-packages.yml`.
- The policy has no runtime, schema, CLI, JSON contract, auth, or package
  execution changes.

## Phase 27. Public Index Namespace Claim Label Automation

- [x] Add a GitHub Actions workflow for issues labeled `namespace-claim`.
- [x] Ensure recommended namespace claim review labels exist.
- [x] Apply `namespace:under-review` when a namespace claim issue has no
  existing namespace review status label.
- [x] Post or update an idempotent policy note linking to
  `specs/NAMESPACE_CLAIM_POLICY.md`.
- [x] Keep automation separate from accepting or rejecting claims, editing
  `public-index/accepted-packages.yml`, generating registry metadata,
  publishing packages, installing packages, and executing package content.
- [x] Add workflow-shape tests that keep permissions, trigger labels, and
  non-goals explicit.

Acceptance:

- The workflow only runs for namespace claim issues.
- The workflow has repository read and issue write permissions only.
- The workflow does not run package validation, public index generation,
  publish, package installation, or package execution.
- The workflow is idempotent for comments and conservative for review status
  labels.

## Phase 28. Public Index Namespace Claim Decision Reports

- [x] Add a GitHub Actions workflow for namespace claim decision reports.
- [x] Report maintainer-applied decision labels for accepted, rejected,
  contested, and superseded namespace claims.
- [x] Skip creating new reports when no namespace claim decision label is
  present and no previous report exists.
- [x] Update existing reports when decision labels are removed.
- [x] Report ambiguity when multiple decision labels are present.
- [x] Post or update an idempotent decision report comment that links to
  `specs/NAMESPACE_CLAIM_POLICY.md`.
- [x] Keep decision report automation separate from applying terminal decision
  labels, editing `public-index/accepted-packages.yml`, generating registry
  metadata, publishing packages, installing packages, and executing package
  content.
- [x] Add workflow-shape tests that keep report-only behavior explicit.

Acceptance:

- The workflow only runs for namespace claim issues.
- The workflow has repository read and issue write permissions only.
- The workflow reports maintainer-applied labels and does not decide claims.
- The workflow is idempotent for comments and paginates marker lookup.
- The workflow does not leave stale decision reports after decision labels are
  removed.
- The workflow has no runtime, schema, CLI, JSON contract, auth, registry
  mutation, or package execution changes.

## Phase 29. Repository Agent Skills

- [x] Add repository-managed experimental Agent Skills for authoring and
  reviewing SpecPM package specs.
- [x] Keep skills under `skills/.experimental/` so they can be installed through
  `$skill-installer` from the GitHub repository.
- [x] Include per-skill `SKILL.md`, OpenAI interface metadata, reference
  checklists, and MIT license files.
- [x] Document installation commands and the skill boundary in `README.md` and
  DocC.
- [x] Update the self-spec so Agent Skills are part of the repository's
  declared package surface.
- [x] Add tests that verify skill shape, install prompts, licensing, README
  links, and self-spec coverage.
- [x] Keep Agent Skills separate from SpecPM runtime, schema validation,
  registry behavior, JSON contracts, and package execution policy.

Acceptance:

- Skills validate with the Agent Skill quick validator.
- `PYTHONPATH=src python3 -m specpm.cli validate . --json` remains valid.
- CI checks catch missing skill files, license drift, or self-spec drift.
- No runtime, schema, CLI, JSON contract, registry mutation, or package
  execution behavior changes.

## Phase 30. Public Index Namespace Claim Decision Summary

- [x] Add a read-only GitHub Actions workflow for namespace claim decision
  summary aggregation.
- [x] Run the summary manually and on a weekly schedule.
- [x] Query namespace claim issues by current maintainer-applied decision
  labels.
- [x] Count accepted, rejected, contested, and superseded namespace claim
  issues without double-counting ambiguous issues in per-label counts.
- [x] Detect ambiguous namespace claim issues with multiple decision labels.
- [x] Preserve inclusive per-label search hit counts separately from
  unambiguous issue counts.
- [x] Bound GitHub Search API pagination to the first 1,000 accessible results
  per decision label and report truncation or incomplete-result warnings.
- [x] Emit workflow summary output and JSON/Markdown artifacts.
- [x] Keep aggregation separate from applying labels, commenting on issues,
  editing `public-index/accepted-packages.yml`, generating registry metadata,
  publishing packages, installing packages, and executing package content.
- [x] Add workflow-shape tests that keep read-only behavior explicit.

Acceptance:

- The workflow has repository read and issue read permissions only.
- The workflow does not write labels, comments, accepted package sources,
  registry metadata, packages, or package content.
- The workflow output is a review aid, not a decision authority or namespace
  ownership contract.
- The workflow surfaces truncation warnings when GitHub Search API result caps
  may make summary counts incomplete.
- The workflow has no runtime, schema, CLI, JSON contract, auth, registry
  mutation, or package execution changes.

## Phase 31. Public and Enterprise Registry Conformance

- [x] Add conformance cases for generated public static `/v0` registry
  endpoints.
- [x] Validate generated registry status, package index, package metadata,
  package version, and exact capability search payloads.
- [x] Verify static-host `index.html` payload mirrors for generated endpoints.
- [x] Verify generated archive digest and size metadata against the actual
  deterministic archive.
- [x] Assert missing package and missing capability paths are not fabricated as
  package data in the static index.
- [x] Add remote registry payload conformance fixtures for deprecated versions
  and invalid package index counts.
- [x] Add enterprise registry status fixture coverage using the same read-only
  metadata contract.
- [x] Document that enterprise registry conformance does not add auth, publish,
  remote mutation, package installation, package signing, or package execution
  to SpecPM core.

Acceptance:

- The portable conformance suite includes public static index endpoint cases.
- The portable conformance suite includes enterprise registry compatibility
  payload cases.
- Generated `/v0` JSON and adjacent `index.html` static-host payloads validate
  against the remote registry API contract.
- Negative payload-shape fixtures produce expected validator error codes.
- No runtime server, publish flow, auth flow, remote mutation API, archive
  client, package signing, package installation, or package execution behavior
  is added.

## Phase 32. Deploy-First Development Workflow

- [x] Add deploy-first Make aliases for the live local registry loop:
  `dev-up`, `dev-reload`, `dev-smoke`, and `dev-down`.
- [x] Add `public-index-reload` so registry-related changes can force-recreate
  the Docker Compose `public-index` service before smoke checks.
- [x] Add `pages-smoke` for validating the deployed GitHub Pages `/v0`
  registry through the read-only `specpm remote` client.
- [x] Document the current live local deployment, production static Pages
  deployment, fresh-version deployment strategy, backup assumptions, and
  flood/DDoS boundary in `specs/DEPLOY_FIRST.md`.
- [x] Update repository agent instructions so registry/deploy changes use the
  live Docker service as the first deploy gate.
- [x] Update README and DocC so local operators and downstream SpecGraph or
  ContextBuilder developers can find the live registry workflow.
- [x] Update the self-spec so deploy-first operation is declared as part of the
  repository package surface.
- [x] Add tests that keep the deploy-first Make targets, docs, and self-spec
  coverage aligned.
- [x] Keep the workflow read-only: no `specpm publish`, remote mutation API,
  auth flow, archive download/install client, package execution, or online
  intent-to-spec runtime is added.

Acceptance:

- `make dev-reload` rebuilds/recreates the local Docker public-index service
  and runs live read-only smoke checks.
- `make pages-smoke` validates the deployed GitHub Pages `/v0` registry through
  the same read-only remote metadata client.
- Documentation makes clear that fresh deployment, backup, flood/DDoS
  protection, and future online intent-to-spec endpoints are operational
  follow-up tracks, not current SpecPM core behavior.
- The local service remains available for SpecGraph, ContextBuilder, and manual
  ecosystem integration testing at `http://localhost:8081` by default.

## Post-MVP Tracks

- Remote registry service implementation.
- Enterprise remote registry deployment with private access control, audit, and
  policy enforcement.
- Fresh-version deployment channels, staged rollout, rollback, and release
  promotion policy for non-static registries.
- Backup and restore policy for generated registry snapshots, accepted package
  manifests, package archives, private enterprise metadata, audit logs, and
  namespace decisions.
- Flood, abuse, and DDoS controls for future online registry and intent-to-spec
  endpoints.
- `specpm publish`.
- Remote package yanking governance.
- Package signing and trust policies.
- Namespace governance.
- Natural-language or semantic capability search.
- Plain-text intent discovery with LLM, embeddings, vector search, or RAG.
- Full dependency solving.
- Expanded conformance suites for additional post-MVP tracks beyond the
  read-only public and enterprise registry metadata contract.
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
- Additional conformance suites for authenticated enterprise registry behavior
  if a future enterprise profile defines auth, audit, or private storage
  contracts.

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

### Post-MVP Track: Intent Discovery and Capability Resolver

Status: Deferred.

#### Goal

Define a downstream resolver that can map plain-text user intent to candidate
capability IDs or package IDs without making SpecPM core a semantic authority.

Example user intent:

```text
I need a package that converts email messages into Markdown.
```

The resolver may propose:

```text
document_conversion.email_to_markdown
```

SpecPM then verifies the candidate through exact lookup, validation, inspection,
and package metadata contracts.

#### Boundary

- SpecPM remains the package and verification substrate.
- SpecPM exact search remains the normative package-manager resolution path.
- ContextBuilder, SpecGraph, or a downstream resolver owns plain-text intent
  interpretation.
- A resolver may use LLM extraction, embeddings, vector search, lexical search,
  reranking, ontology traversal, graph context, and human review.
- Resolver output must be candidate `capability_id` or `package_id` values, not
  trusted package selections.
- Ambiguous matches must remain review-required.

#### Non-Goals

- This track does not add embedding generation to SpecPM core.
- This track does not add vector index storage to SpecPM core.
- This track does not add RAG orchestration to SpecPM core.
- This track does not add semantic package selection authority to SpecPM core.
- This track does not allow package content to become trusted prompt
  instructions.
- This track does not change the exact capability search contract.

#### Future Investigation Areas

Future work may explore:

- metadata exports optimized for external embedding;
- candidate generation from package summaries, capabilities, constraints,
  evidence, and provenance;
- confidence and traceability reports for candidate mappings;
- policy gates before `specpm add`;
- feedback loops into SpecGraph proposal lanes.
