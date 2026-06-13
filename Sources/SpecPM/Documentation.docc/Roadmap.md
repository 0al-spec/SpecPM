# Roadmap

SpecPM is in public alpha as a package and registry substrate for SpecGraph.

The canonical repository roadmap is `ROADMAP.md`. This DocC page summarizes the
same direction for public documentation readers.

## Maturity Snapshot

SpecPM is in public alpha / MVP+ status. It is usable today as a read-only
package and registry substrate with deployed `/v0` metadata, curated accepted
artifacts, package-set relations, and the `xyflow` package-set reference flow.

It is not yet a self-service package manager ecosystem. `specpm publish`,
mutable remote registry APIs, authentication, dependency solving, runtime
signature verification, and semantic package selection remain outside SpecPM
core.

## Current Alpha Baseline

SpecPM is usable today for:

- local `SpecPackage` and `BoundarySpec` validation, inspection, deterministic
  packing, structural diff, and local registry operations;
- exact capability search and deterministic local add/lock behavior;
- exact `intent.*` lookup over explicit capability-to-intent mappings;
- observed intent catalog metadata for authoring and duplicate detection;
- SpecGraph inbox inspection for exported package candidates;
- read-only remote `/v0` metadata lookup;
- static public index generation for GitHub Pages;
- static registry viewer at `https://0al-spec.github.io/SpecPM/viewer/`;
- local Docker registry integration at `http://localhost:8081`;
- public alpha registry metadata at `https://0al-spec.github.io/SpecPM`;
- GitHub Issue intake for package submissions, removals, and namespace claims;
- registry-visible package-set metadata through `/v0/relations`,
  `packageSet.members`, relation context, and package-set viewer panels;
- maintainer-curated `xyflow` accepted artifacts with generated SpecHarvester
  output preserved as producer evidence;
- SpecHarvester producer-bundle intake policy, handoff preflight, AI enrichment
  preflight, AI draft preflight, maintainer-selected materialization, and
  curated accepted artifact lifecycle policy;
- GitHub Actions runtime-major maintenance policy for official `actions/*`
  workflow references;
- GitHub Actions permissions and secret-boundary policy for repository
  workflows, deploy credentials, and `pull_request_target` review;
- package signing and revocation policy for future verification, lifecycle, and
  provenance receipt work;
- DocC documentation, conformance fixtures, Agent Skills, and self-spec
  coverage.

The public registry is metadata-only and static-hosted. See
<doc:StaticRegistryPipeline> for the build-time generation path.

## Milestones

### Alpha Stabilization

Keep roadmap, Workplan, README, DocC, landing page, and self-spec coverage
aligned with the current public alpha state.

### Public Index Operator UX

Make valid community submissions easier to accept through maintainer-reviewed
labels, checklists, and future helper tooling that prepares
`public-index/accepted-packages.yml` pull requests.

This does not add `specpm publish`, package upload, or request-time registry
mutation.

### Downstream Consumer Integration

Document and stabilize how SpecGraph, ContextBuilder, and SpecNode consume
`/v0/status`, `/v0/packages`, package lookup, version lookup, exact capability
search, observed intent catalog metadata, and observation reports.

### Remote Package Acquisition Design

Design remote fetch/cache/add behavior before implementing it. Metadata lookup,
archive acquisition, digest verification, lockfile changes, and cache layout
must be explicit.

### Trust, Provenance, and Governance

Design signing, provenance, revocation, yanked/deprecated version semantics,
namespace claim policy, and audit records without conflating public static index
needs with enterprise registry needs.

### Enterprise Registry Track

Define an authenticated read-only registry profile compatible with `/v0` for
private package visibility, access control, audit, retention, backup, restore,
and staged promotion.

### Intent Resolver Track

Keep natural-language intent resolution outside SpecPM core. ContextBuilder,
SpecGraph, or downstream resolver tooling may use embeddings, vector search,
RAG, or LLM reranking to propose reviewable candidate `intent.*`,
`SpecPackage`, `BoundarySpec`, and capability IDs. SpecPM verifies exact IDs and
package shape.

### Package Sets and Monorepo Decomposition

Represent multi-package repositories as package sets plus scoped member
packages. Package-set discovery should be index-based, not tree-traversal-based,
so exact `intent.*` lookup can return aggregate and scoped package results with
explicit scope and consumers do not have to guess whether the useful result
lives at a repository root or a member package.

This track defines collection entrypoints, relation vocabulary, registry
metadata, SpecHarvester monorepo discovery handoff, and multi-package producer
bundle intake without adding inheritance, package execution, dependency solving,
or resolver authority to SpecPM core.

The current public alpha reference flow is complete for `xyflow`: generated
producer evidence, SpecPM handoff preflight, explicit maintainer package and
relation selection, curated accepted artifacts, registry-visible relations, and
viewer support are all in place.

### Multi-Repository Quality Calibration

Run SpecHarvester and SpecPM intake checks across several real repositories
before expanding public intake automation. The goal is to measure summary,
capability, evidence, interface, package-boundary, relation, and diagnostics
quality across ecosystems while keeping automatic acceptance, semantic ranking,
and self-service upload outside SpecPM core.

## Next Planned Sequence

The Public Index Operator UX baseline is complete. Maintainer tooling can now
prepare accepted-manifest pull request drafts from valid submission reports. The
SpecGraph public registry observation contract is also documented so downstream
graph work can cite exact `/v0` evidence without giving SpecPM graph authority.
The Downstream registry consumer contract is documented for SpecGraph,
ContextBuilder, SpecNode, and lab deploy checks. It defines normative `/v0`
endpoint classes, minimum evidence fields, failure vocabulary, and read-only
consumer obligations without turning SpecPM into a resolver or runtime.
Reusable registry observation reports now write local Docker and GitHub Pages
JSON artifacts under `.specpm/registry-observations/` for downstream reviews.
GitHub Actions runtime maintenance is documented for official action majors,
update triggers, validation commands, and the `pull_request_target` post-merge
verification boundary.
GitHub Actions workflow permissions and secret boundaries are documented for
allowed `GITHUB_TOKEN` scopes, FTP secret usage, `pull_request_target` review
rules, and SFTP/Pages deploy evidence boundaries.
The remote package acquisition boundary is now documented before any archive
fetch/cache/add behavior: metadata lookup stays separate from download, digests
must be verified before cache or lock writes, and package content remains
untrusted data.
Remote package acquisition design invariants are now documented. The policy
defines explicit acquisition states, atomic cache and lock writes, retry and
partial-write behavior, trust/signature/receipt separation, and structured
failure categories before any remote fetch/install runtime exists.
Intent taxonomy governance is now documented for canonical `intent.*` proposal,
review, lifecycle, conflict handling, experimental/private namespace use, and
the boundary between observed metadata and accepted vocabulary. The intent
taxonomy governance policy keeps observed metadata separate from accepted
vocabulary.
The phrase "intent taxonomy governance" names the current policy boundary.
Package signing and revocation policy is now documented. It separates digest
verification from publisher authority, defines future signature subjects,
records revocation, yanked/deprecated semantics, and provenance receipt
expectations, and keeps runtime signature verification out of the current
implementation.
Provenance receipt schema and audit evidence profile are now documented. The
draft `SpecPMProvenanceReceipt` envelope defines source, archive, review,
build, validation, trust, lifecycle, and audit evidence sections without adding
trust authority.
The public static provenance receipt JSON artifacts are now generated for public
index package versions. Task label:
`implementation: public static provenance receipt artifacts`. The generated
receipts are non-authoritative audit evidence and do not add signature
verification, lockfile enforcement, remote acquisition, mutable registry
publication, or package execution.
Producer receipt requirements for generated package candidates are now
documented. The draft `SpecPMProducerReceipt` envelope defines generated
package subject, producer, inputs, configuration, outputs, validation,
diagnostics, review, privacy, and audit evidence sections through the
`generated_spec_package_v0` profile for SpecHarvester or another producer
without adding generator runtime authority to SpecPM.
Producer candidate bundle contract alignment is now documented. The policy
defines the `candidate/` layout, `producer-receipt.json` handoff contract,
input and configuration digests, output roles and hashes, validation and
diagnostics artifacts, human review status for `public_index_acceptance`, and
the rule that receipts do not hash themselves.
SpecPM-side producer bundle proposal policy is now documented. Producer
candidate bundles from SpecHarvester or another tool are proposal evidence, not
registry authority; maintainers still own package validation, accepted-source
review, override records, and acceptance decisions.
Producer-backed public-index intake is now documented in the operator guide
and submission flow. Accepted-manifest pull requests that rely on SpecHarvester
or other producer bundles should link the receipt, validation report,
diagnostics report, preflight evidence, static viewer evidence when available,
and proposed accepted-source diff before maintainer acceptance.
Public index operator flow hardening is now documented. The operator guide
defines label transition policy, terminal label ownership, dry-run helper
review posture, accepted-manifest pull request checklist, and audit links from
submission issues to generated static registry evidence.
The immediate planned sequence is:

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
Multi-package producer bundle intake is now documented so maintainers can
review package-set proposals, scoped member candidates, and relation proposals
with partial acceptance and explicit accepted-source effects.
SpecPM package-set intake now recognizes SpecHarvester
`package-set-handoff-proposal.json` and `package-set-handoff-proposal.md`
artifacts as dry-run review evidence while keeping accepted-source pull
requests, relation acceptance, and maintainer decisions as the registry
authority.
SpecPM package-set intake now also treats
`package-set-ai-enrichment-proposal.json` as optional proposal-only review
evidence. AI-suggested capabilities, intents, interfaces, and summaries require
ordinary evidence review and explicit maintainer acceptance before they can
become package claims.
`specpm producer-bundle preflight` can also verify package-set handoff identity,
member manifest IDs, evidence digests, bundle-set preflight counts, and
`contains` relation endpoints without executing producer tools.
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
The maintainer-selected accepted-source materialization path is now implemented through
`specpm producer-bundle materialize-package-set`: read a package-set handoff
plus explicit package and relation selections, then prepare review artifacts or
copy only selected package candidates into `public-index/generated` with
`--apply` without auto-accepting producer output.
The `xyflow` package-set acceptance policy is now documented as a transition
rule for the existing `xyflow.core@0.1.0` candidate. Maintainers explicitly
left `xyflow.core` unchanged as previous single-package review evidence while
accepting `xyflow.workspace` plus scoped `xyflow.react`, `xyflow.svelte`, and
`xyflow.system` curated members as the current package-set model. Removing
`preview_only` from generated package-set candidates remains an explicit
maintainer acceptance decision, not a consequence of green producer or SpecPM
preflight checks.
The `xyflow` package-set accepted-source materialization is now completed via a
fresh real checkout run using current SpecHarvester and SpecPM `main`. The
selected accepted-source inputs are maintainer-curated `xyflow.workspace`,
`xyflow.react`, `xyflow.svelte`, and `xyflow.system` artifacts, with three
selected `contains` relations published as accepted registry metadata.
`xyflow.core@0.1.0` remains unchanged as previous single-package review
evidence, and AI enrichment remains proposal-only evidence rather than registry
truth.
Registry-visible package-set relations are now implemented as additive `/v0`
metadata. Maintainer-reviewed `relations[]` entries in
`public-index/accepted-packages.yml` generate `/v0/relations`, advertise
`package_relations` support in `/v0/status`, add `packageSet.members` to
aggregate package payloads, and add `relationContext` to member package and
exact search payloads. Producer-observed relations remain non-authoritative
until explicitly accepted in the manifest.
The accepted `xyflow` package-set members now come from maintainer-curated
artifacts under `public-index/curated/xyflow.*`. Generated SpecHarvester output
remains under `public-index/generated/xyflow.*` as producer evidence; curated
manifests reference generated candidates, receipts, and validation reports
without changing producer receipt hashes or pretending maintainer text was
producer output.
The curated accepted artifact lifecycle is now documented as standard policy:
generated candidates remain immutable evidence, curated artifacts own
maintainer-authored accepted metadata, new harvests update curated artifacts
only through review diffs, `foreignArtifacts` preserve evidence chains,
removing `preview_only` is a maintainer acceptance act, and accepted relations
remain explicit `relations[]` manifest entries.
Generated candidate refresh decisions are now documented as explicit review
records: a fresh run can end with `SpecPMGeneratedCandidateRefreshDecision`
`status: no_update_required`, `updateNeeded: false`, and
`reason: no_contract_delta` when it reproduces the same contract-bearing
generated files and the curated accepted artifact remains the stronger registry
source.
The `xyflow` no-op refresh decision is now captured as a checked example
fixture under `tests/fixtures/refresh_decisions/`, giving future tooling a
stable artifact for `updateNeeded: false` without making no-op records registry
authority.
SpecPM can now prepare refresh decision records from a fresh generated candidate
tree with `specpm producer-bundle prepare-refresh-decision`, compare
contract-bearing generated files, and emit read-only
`SpecPMGeneratedCandidateRefreshDecisionPrepareReport` evidence before any
maintainer registry decision.
The manual `Refresh Decision Prepare` GitHub Actions workflow now packages that
same refresh decision evidence as CI artifacts without write credentials or
registry mutation.
SpecPM now has a consumer-side `preflight-ai-draft` gate for
`SpecHarvesterPackageSetAIDraftProposal`. It verifies AI-proposed member
selection, exclusions, and `contains` relations against deterministic workspace
inventory evidence while keeping the artifact proposal-only and outside registry
acceptance or materialization authority.
SpecPM now has a consumer-side `preflight-baseline-submission` gate for
`SpecHarvesterBaselineSubmissionHandoff`. It verifies first-submission or
seeded-baseline handoff identity, missing-baseline diagnostics, linked
fresh-run and prepare-report digests, maintainer action choices, and authority
flags while keeping baseline seeding and registry acceptance under maintainer
review.
SpecPM now has a consumer-side
`preflight-selected-candidate-handoff` gate for
`SpecHarvesterSelectedCandidateHandoffProposal` and
`SpecHarvesterRefreshedCandidateLayerSelectedHandoff`. It verifies selected and
deferred candidate consistency, preview-only posture, producer preflight and
static viewer status, evidence role digests, refreshed source fixture digests,
and non-authority flags before limited corpus intake review.
The `xyflow` package-set reference scenario is now documented with example
workspace inventory, package-set metadata, relation proposals, and exact intent
search result scope fixtures.

These are planned tracks. They do not add package upload, request-time registry
mutation, package execution, semantic resolution, graph authority, or remote
archive acquisition to SpecPM core.

## Non-Goals For SpecPM Core

SpecPM core does not own:

- PRD, brief, issue breakdown, or test-plan generation;
- prompt execution or agent runtime behavior;
- artifact evaluation runtime;
- graph reasoning or canonical SpecGraph refinement;
- package-provided host instructions;
- public request-time mutation APIs;
- online intent-to-spec runtime.

Package content can describe desired outputs. Package content cannot command the host.

## References

- <doc:StaticRegistryPipeline>
- <doc:IdentifierModel>
- <doc:AddSpecPackage>
- <doc:PublicAlphaRegistry>
- <doc:Deployment>
- <doc:RegistryOperations>
- <doc:SpecGraphIntegration>
- <doc:RemotePackageAcquisition>
- <doc:IntentTaxonomyGovernance>
- <doc:PackageSigningRevocation>
- <doc:ProvenanceReceipts>
- <doc:ProducerReceipts>
- <doc:ProducerBundleProposalPolicy>
- <doc:PackageSets>
- <doc:PackageRelations>
- <doc:PackageSetSearch>
- <doc:PackageSetRegistryMetadata>
- <doc:SpecHarvesterMonorepoDiscovery>
- <doc:MultiPackageProducerIntake>
- <doc:XyflowPackageSetReference>
