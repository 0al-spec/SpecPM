# SpecPM Roadmap

Status: Public alpha roadmap
Updated: 2026-06-06

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
- package signing and revocation policy for future verification, lifecycle, and
  provenance receipt work;
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

- maintain package signing and verification policy;
- define revocation and yanked/deprecated version behavior for public and
  enterprise registries;
- refine namespace claim policy without implying automatic ownership;
- explore transparency log or append-only audit records;
- define stronger machine-readable provenance receipts for accepted public
  sources.

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

## Milestone 8: Package Sets and Monorepo Decomposition

Goal: let SpecPM and producer tools represent multi-package repositories as
reviewable package sets plus scoped member packages without forcing discovery
through a package tree.

Tasks:

- define `SpecPackageSet` or an equivalent collection profile for repository,
  workspace, ecosystem, and product-family entrypoints;
- define package relations such as `contains`, `composes`, `refines`,
  `satisfies`, `supersedes`, and `related` without treating them as implicit
  inheritance;
- keep exact intent lookup index-based so a query can return aggregate package
  sets and concrete member packages without requiring root-to-leaf traversal;
- define how public registry metadata exposes member packages, relation
  evidence, aggregate intent summaries, and scoped capability ownership;
- align SpecHarvester monorepo discovery so workspace manifests can produce a
  package-set candidate plus scoped package candidates such as
  `xyflow.workspace`, `xyflow.system`, `xyflow.react`, and `xyflow.svelte`;
- recognize SpecHarvester package-set handoff artifacts such as
  `package-set-handoff-proposal.json` and `package-set-handoff-proposal.md` as
  dry-run review evidence, not write-capable registry authority;
- treat SpecHarvester package-set AI enrichment artifacts such as
  `package-set-ai-enrichment-proposal.json` as optional proposal-only review
  evidence, not canonical package truth or automatic capability/intent
  acceptance;
- define review and acceptance rules for multi-package producer bundles before
  adding registry authority or automatic publication behavior.

Success criteria:

- monorepos can preserve broad product intent and narrow package boundaries at
  the same time;
- downstream consumers can search by exact `intent.*` and see whether each
  result is aggregate, scoped, or related;
- SpecHarvester can hand SpecPM a reviewable multi-package candidate bundle
  without making SpecPM execute producer logic;
- package-set handoff evidence can be reviewed without exposing SpecPM write
  credentials or other registry write credentials to untrusted producer
  execution;
- SpecPM can run consumer-side package-set handoff preflight to verify member
  manifest IDs, evidence digests, bundle-set preflight counts, and `contains`
  relation endpoints before maintainer acceptance;
- a real SpecHarvester `xyflow` package-set dry run can pass through SpecPM
  consumer-side preflight without giving producer output registry authority;
- package relations improve navigation and evidence review without becoming a
  hidden semantic resolver.

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

The Downstream Registry Consumer Contract is documented for SpecGraph,
ContextBuilder, SpecNode, and lab deploy checks. It defines normative `/v0`
endpoint classes, minimum evidence fields, failure vocabulary, and read-only
consumer obligations without turning SpecPM into a resolver or runtime.

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

Remote package acquisition design invariants are now documented. The policy
defines explicit acquisition states, atomic cache and lock writes, retry and
partial-write behavior, trust/signature/receipt separation, and structured
failure categories before any remote fetch/install runtime exists.

Intent taxonomy governance is now documented. The intent taxonomy governance
policy separates observed
intent metadata from accepted canonical vocabulary, defines proposal and review
criteria, records lifecycle states such as accepted/deprecated/superseded/
rejected/reserved, and keeps semantic interpretation outside SpecPM core.

Package signing and revocation policy is now documented. The policy separates
digest verification from publisher authority, defines future signature subjects,
records revocation, yanked/deprecated semantics, and provenance receipt
expectations, and keeps runtime signature verification out of the current
implementation.

Provenance receipt schema and audit evidence profile are now documented. The
policy defines the draft `SpecPMProvenanceReceipt` envelope, public static index
profile, required source/archive/review/build/validation/trust/lifecycle/audit
sections, and fixture shape.

Public static provenance receipt artifact generation is now implemented for
public index package versions. Task label:
`implementation: public static provenance receipt artifacts`. The generated
receipts are non-authoritative audit evidence and do not add signature
verification, lockfile enforcement, remote acquisition, mutable registry
publication, or package execution.

Producer receipt requirements for generated package candidates are now
documented. The policy defines a tool-neutral `SpecPMProducerReceipt` envelope
and `generated_spec_package_v0` profile that SpecHarvester or another producer
can emit without giving SpecPM generator runtime authority.

Producer candidate bundle contract alignment is now documented. The policy
defines the `candidate/` layout, `producer-receipt.json` handoff contract,
input and configuration digests, output roles and hashes, validation and
diagnostics artifacts, human review status for `public_index_acceptance`, and
the rule that receipts do not hash themselves.

SpecPM-side producer bundle proposal policy is now documented. Producer
candidate bundles from SpecHarvester or another tool are proposal evidence, not
registry authority; maintainers still own package validation, accepted-source
review, override records, and acceptance decisions.

Producer-backed public-index intake is now documented in the operator guide and
submission flow. Accepted-manifest pull requests that rely on SpecHarvester or
other producer bundles should link the receipt, validation report, diagnostics
report, preflight evidence, static viewer evidence when available, and proposed
accepted-source diff before maintainer acceptance.

This baseline still preserves the public static index boundary: automation may
prepare labels, comments, and candidate snippets, but accepted package changes
remain maintainer-reviewed pull requests against
`public-index/accepted-packages.yml`.

Public index operator flow hardening is now documented. The operator guide
defines label transition policy, terminal label ownership, dry-run helper
review posture, accepted-manifest pull request checklist, and audit links from
submission issues to generated static registry evidence.

## Next Planned Sequence

The SpecHarvester producer loop now has receipt, validation report,
diagnostics report, preflight, viewer, handoff documentation, and end-to-end
smoke coverage. The next seam work belongs at the SpecPM intake boundary:
proposal automation evidence links, optional SpecPM CI preflight, shared
cross-repository fixtures, and an external acceptance decision record that
keeps producer receipts separate from registry authority.

Shared SpecPM/SpecHarvester fixture policy is now documented: SpecPM owns
consumer contract examples, SpecHarvester owns generated output examples, and
cross-repository checks must avoid mutable `main` as a fixture trust root.

SpecHarvester-to-SpecPM proposal automation contract is now documented. Producer
pull requests should include machine-readable `producerEvidenceLinks` and
`registryAcceptanceDecision` blocks that SpecPM can preflight without executing
producer tools.

External registry acceptance decision records are now documented. They connect
producer evidence to maintainer review and accepted-source effects while keeping
producer receipts as `evidence_only` support material.

Package-set concept and boundaries are now documented. Package sets are
collection entrypoints for repositories, workspaces, ecosystems, and product
families; they preserve aggregate discovery without making member packages
inherit capabilities, trust, lifecycle state, or acceptance status.
Package relation vocabulary is now documented for `contains`, `composes`,
`refines`, `satisfies`, `supersedes`, and `related` metadata claims, including
evidence expectations and non-goals.
Package-set search semantics are now documented. Exact lookup remains
index-based and may return aggregate, scoped package, abstract-contract, and
relation-context results without requiring root-to-leaf traversal.
Package-set registry metadata shape is now drafted for additive `/v0` fields
covering package-set subject metadata, members, accepted relations, result
scope, relation context, and feature signaling.
SpecHarvester monorepo discovery handoff is now documented for workspace
inventory, stable package ID proposals, package-set and scoped member
candidates, relation proposal output, and bundle-set review evidence.
SpecHarvester-to-SpecPM package-set dry-run validation has been exercised on a
real `xyflow` checkout. The run produced `xyflow.workspace`, `xyflow.react`,
`xyflow.svelte`, and `xyflow.system` candidates with three `contains` relation
proposals; SpecPM consumer-side preflight accepted the handoff with zero errors
and zero warnings.
SpecHarvester-to-SpecPM package-set AI enrichment has been exercised on the
same real `xyflow` checkout with a local OpenAI-compatible provider. The run
produced four proposal-only enrichment records, while SpecPM materialization
still used only the ordinary package-set handoff and explicit maintainer
package/relation selection.

SpecPM now provides `specpm producer-bundle preflight-ai-enrichment` for the
machine-checkable AI enrichment review boundary: artifact identity,
proposal-only authority, privacy flags, package alignment, allowlisted evidence
paths, `interfaces[].kind`, and provider provenance.

The maintainer-selected accepted-source materialization path is now implemented
through `specpm producer-bundle materialize-package-set`. The helper reads a
package-set handoff plus explicit package and relation selections, prepares
review artifacts in dry-run mode, and can copy only selected package candidates
into `public-index/generated` with `--apply`. It does not auto-accept all producer
output, infer acceptance from a passing preflight, or publish registry metadata
without maintainer review.

The `xyflow` package-set acceptance policy is now documented as a transition
rule for the existing `xyflow.core@0.1.0` candidate. A future package-set PR
must decide explicitly whether `xyflow.core` remains unchanged, is superseded by
`xyflow.workspace` plus scoped members, is kept as compatibility metadata, or is
removed later. Removing `preview_only` from generated package-set candidates is
also an explicit maintainer acceptance decision, not a consequence of green
producer or SpecPM preflight checks.

The `xyflow` package-set accepted-source materialization is now proposed from a
fresh real checkout run using current SpecHarvester and SpecPM `main`. The
selected accepted-source inputs are `xyflow.workspace`, `xyflow.react`,
`xyflow.svelte`, and `xyflow.system`, with three selected `contains` relations
kept as maintainer-review evidence. `xyflow.core@0.1.0` remains unchanged as
previous single-package review evidence, generated package-set entries remain
`preview_only`, and AI enrichment remains proposal-only evidence rather than
registry truth.

Registry-visible package-set relations are now implemented as additive `/v0`
metadata. Maintainer-reviewed `relations[]` entries in
`public-index/accepted-packages.yml` generate `/v0/relations`, advertise
`package_relations` support in `/v0/status`, add `packageSet.members` to
aggregate package payloads, and add `relationContext` to member package and
exact search payloads. Producer-observed relations remain non-authoritative
until explicitly accepted in the manifest.

These are planned tracks. They do not add package upload, request-time registry
mutation, package execution, semantic resolution, graph authority, or remote
archive acquisition to SpecPM core.

## Explicit Non-Goals For SpecPM Core

SpecPM core does not own:

- PRD, brief, issue breakdown, or test-plan generation;
- prompt execution or agent runtime behavior;
- artifact evaluation runtime;
- graph reasoning or canonical SpecGraph refinement;
- package-provided host instructions;
- public request-time mutation APIs;
- online intent-to-spec runtime.

Package content can describe desired outputs. Package content cannot command the
host.

## References

- [Static registry pipeline](specs/STATIC_REGISTRY_PIPELINE.md)
- [Identifier model](specs/IDENTIFIER_MODEL.md)
- [Public alpha registry](specs/PUBLIC_ALPHA_REGISTRY.md)
- [Deployment](specs/DEPLOYMENT.md)
- [Registry operations](specs/REGISTRY_OPERATIONS.md)
- [SpecGraph integration](specs/SPECGRAPH_INTEGRATION.md)
- [Remote package acquisition](specs/REMOTE_PACKAGE_ACQUISITION.md)
- [Intent taxonomy governance](specs/INTENT_TAXONOMY_GOVERNANCE.md)
- [Package signing and revocation](specs/PACKAGE_SIGNING_REVOCATION.md)
- [Provenance receipts](specs/PROVENANCE_RECEIPTS.md)
- [Producer receipts](specs/PRODUCER_RECEIPTS.md)
- [Producer bundle proposal policy](specs/PRODUCER_BUNDLE_PROPOSAL_POLICY.md)
- [Package sets](specs/PACKAGE_SETS.md)
- [Package relations](specs/PACKAGE_RELATIONS.md)
- [Package set search](specs/PACKAGE_SET_SEARCH.md)
- [Package set registry metadata](specs/PACKAGE_SET_REGISTRY_METADATA.md)
- [SpecHarvester monorepo discovery](specs/SPECHARVESTER_MONOREPO_DISCOVERY.md)
