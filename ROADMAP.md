# SpecPM Roadmap

Status: Public alpha roadmap
Updated: 2026-05-23

SpecPM is the package substrate for SpecGraph. It packages, validates, indexes,
inspects, preserves, and exposes reusable specification intent. It does not own
graph reasoning, artifact generation, prompt execution, semantic intent
resolution, or package content execution.

## Current Alpha Baseline

SpecPM is ready for alpha exploitation as a read-only package and registry
substrate.

Implemented surfaces:

- local `SpecPackage` and `BoundarySpec` validation, inspection, deterministic
  packing, structural diff, strict spec-authoring warnings, and local registry
  operations;
- exact capability search and deterministic local add/lock behavior;
- exact `intent.*` lookup over explicit capability-to-intent mappings;
- observed intent catalog metadata for authoring and duplicate detection;
- SpecGraph inbox inspection for exported package candidates;
- read-only remote `/v0` metadata client commands;
- static public index generation for GitHub Pages;
- static registry viewer at `https://0al-spec.github.io/SpecPM/viewer/`;
- Docker-backed local public registry at `http://localhost:8081`;
- GitHub Pages public alpha registry at `https://0al-spec.github.io/SpecPM`;
- GitHub Issue intake for public package submissions, removals, and namespace
  claims;
- public alpha package set with `specpm.core`, `specnode.core`, and the example
  email tools package;
- first abstract intent-level interface contract for public repository metadata;
- GitHub Actions runtime-major maintenance policy for official `actions/*`
  workflow references;
- GitHub Actions permissions and secret-boundary policy for repository
  workflows, deploy credentials, and `pull_request_target` review;
- DocC documentation, landing page, Agent Skills, conformance fixtures, and
  self-spec coverage.

Operationally, registry-related changes should use:

```bash
make dev-reload
make dev-smoke
make pages-smoke
```

`make pages-smoke` validates the currently deployed GitHub Pages registry. Pull
request changes reach the deployed `/v0` surface only after merge and Pages
deployment.

## Roadmap Principles

- Keep SpecPM narrow: package substrate first, product reasoning elsewhere.
- Keep package content untrusted data.
- Keep package-owned capability IDs separate from package-neutral `intent.*`
  IDs.
- Keep public registry mutation out of request-time APIs.
- Prefer reviewed source changes, deterministic generation, and static hosting
  before introducing mutable services.
- Treat remote package acquisition, signing, enterprise auth, and intent
  resolution as explicit future tracks, not accidental MVP drift.

## Milestone 1: Alpha Stabilization

Goal: make the current alpha easier to understand, operate, and verify.

Tasks:

- keep `ROADMAP.md`, DocC Roadmap, and `specs/WORKPLAN.md` aligned;
- normalize completed phase numbering and current-status language in Workplan;
- keep DocC, README, and landing page consistent about the static registry
  pipeline and public alpha state;
- keep the self-spec aligned with public repository surfaces;
- keep abstract intent contracts clearly separate from concrete provider
  packages while allowing downstream governance to relate them;
- keep API versioning surfaces explicit before introducing multi-version
  runtime behavior;
- run local Docker and Pages smoke checks for registry-facing changes.

Success criteria:

- external users can identify what is live today;
- downstream consumers can query the public `/v0` registry without asking how it
  is hosted;
- maintainers can tell which future features are intentionally outside core.

## Milestone 2: Public Index Operator UX

Goal: make valid community submissions easier for maintainers to accept without
turning the public index into a mutable upload API.

Tasks:

- define maintainer labels for submission states such as `validated`,
  `needs-fix`, `accepted`, `rejected`, and `blocked`;
- add a maintainer checklist for accepting a valid package issue;
- explore a helper that reads a valid submission issue, pins the submitted Git
  revision, and prepares a pull request against
  `public-index/accepted-packages.yml`;
- keep acceptance human-reviewed and PR-based;
- keep package validation and publication separate from package execution.

Success criteria:

- a valid external submission can become a reviewed manifest PR with minimal
  manual copying;
- every acceptance remains auditable through GitHub Issues, PRs, and Actions;
- no `specpm publish`, upload endpoint, or unauthenticated mutation API exists.

## Milestone 3: Downstream Consumer Integration

Goal: make SpecGraph, ContextBuilder, and SpecNode consume the public registry
as a stable observation surface.

Tasks:

- document consumer examples for `/v0/status`, `/v0/packages`, package lookup,
  version lookup, observed intent catalog metadata, and exact capability search;
- define the SpecGraph public registry observation contract;
- expose registry availability, visible package counts, and drift in
  ContextBuilder;
- capture reusable observation reports for local Docker and GitHub Pages;
- document how SpecNode consumes typed-job and package-generation capabilities.

Success criteria:

- downstream tools can show whether a package is visible in the public registry;
- registry drift can be discussed with concrete JSON evidence;
- SpecPM remains the metadata substrate and does not take over graph reasoning.

## Milestone 4: Remote Package Acquisition Design

Goal: decide whether and how SpecPM should fetch or cache remote package
archives.

Tasks:

- write a design note before implementing any remote install/fetch behavior;
- separate metadata lookup from archive acquisition;
- define digest verification, cache layout, lockfile changes, and failure modes;
- decide whether remote acquisition belongs in SpecPM core or a separate
  downstream tool;
- preserve the rule that package content is never executed during acquisition.

Success criteria:

- `specpm remote` remains read-only metadata until the trust model is explicit;
- any future fetch/add behavior has deterministic cache and lock semantics;
- archive download does not imply package execution or host authority.

## Milestone 5: Trust, Provenance, and Governance

Goal: strengthen the registry trust model beyond pinned revisions and archive
digests.

Tasks:

- design package signing and verification policy;
- define revocation and yanked/deprecated version behavior for public and
  enterprise registries;
- refine namespace claim policy without implying automatic ownership;
- explore transparency log or append-only audit records;
- define stronger provenance receipts for accepted public sources.

Success criteria:

- consumers can distinguish metadata visibility from trust;
- yanking, removal, and namespace claims have explicit audit semantics;
- public and enterprise trust requirements stay separate where necessary.

## Milestone 6: Enterprise Registry Track

Goal: support private deployments without forcing enterprise requirements into
the public static index.

Tasks:

- define an authenticated read-only registry profile compatible with `/v0`;
- specify private package visibility, access control, and audit behavior;
- define backup, restore, retention, and staged promotion requirements;
- keep enterprise mutation APIs separate from the public static index model;
- add conformance fixtures only after the profile is explicit.

Success criteria:

- enterprise deployments can implement compatible read-only metadata surfaces;
- public static hosting remains simple and low-risk;
- auth, private storage, and audit are designed as enterprise concerns.

## Milestone 7: Intent Resolver Track

Goal: keep the valuable intent-to-spec direction while preserving SpecPM's
package-manager boundary.

Tasks:

- maintain the identifier model that separates package IDs, capability IDs, and
  canonical `intent.*` IDs;
- expose exact intent lookup only for explicitly declared `intentIds`;
- define the resolver as ContextBuilder, SpecGraph, or downstream service work;
- use embeddings, vector search, RAG, or LLM reranking outside SpecPM core;
- return reviewable candidate `intent.*`, `SpecPackage`, `BoundarySpec`, and
  capability IDs;
- make candidate selection explicit and auditable;
- keep exact package verification in SpecPM.

Success criteria:

- plain-text needs can become reviewable package candidates;
- SpecPM verifies exact intent IDs, capability IDs, package IDs, and package
  shape;
- semantic resolution does not become normative package-manager behavior.

## Explicit Non-Goals For SpecPM Core

SpecPM core does not own:

- PRD, brief, issue breakdown, or test-plan generation;
- prompt execution or agent runtime behavior;
- artifact evaluation runtime;
- graph reasoning or canonical SpecGraph refinement;
- package-provided host instructions;
- public request-time mutation APIs;
- online intent-to-spec runtime.

Package content can describe desired outputs. Package content cannot command the host.

## Recent Progress

The Public Index Operator UX baseline is complete. SpecPM now has maintainer
review labels, a package-submission triage workflow, an accepted-manifest
candidate snippet helper, an accepted-manifest pull request helper, and
downstream read-only registry consumer examples.

The SpecGraph public registry observation contract is also documented. It
defines which `/v0` payloads SpecGraph can cite for package visibility,
missing versions, lifecycle state, observed intents, and drift without giving
SpecPM graph authority.

Reusable registry observation reports are now documented and exposed through
Make targets for local Docker and GitHub Pages. They write review-oriented JSON
artifacts under `.specpm/registry-observations/` and include package, version,
capability, and exact observed intent checks.

GitHub Actions runtime maintenance is now documented. The policy records the
official `actions/*` major-version guard, update triggers, validation commands,
and the `pull_request_target` post-merge verification boundary.

GitHub Actions workflow permissions and secret boundaries are now documented.
The policy records the allowed `GITHUB_TOKEN` scopes, FTP secret usage,
`pull_request_target` review rules, and SFTP/Pages deploy evidence boundary.

The remote package acquisition boundary is now documented before implementation.
The policy keeps registry metadata lookup separate from archive download,
requires digest verification before cache or lock writes, and keeps package
content untrusted during acquisition, validation, caching, and lockfile
generation.

This baseline still preserves the public static index boundary: automation may
prepare labels, comments, and candidate snippets, but accepted package changes
remain maintainer-reviewed pull requests against
`public-index/accepted-packages.yml`.

## Next Planned Sequence

1. `design: intent taxonomy governance`
   - define how canonical `intent.*` domains are proposed, reviewed, and mapped
     to package capabilities.
