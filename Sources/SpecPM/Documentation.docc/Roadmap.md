# Roadmap

SpecPM is in public alpha as a package and registry substrate for SpecGraph.

The canonical repository roadmap is `ROADMAP.md`. This DocC page summarizes the
same direction for public documentation readers.

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
- GitHub Actions runtime-major maintenance policy for official `actions/*`
  workflow references;
- GitHub Actions permissions and secret-boundary policy for repository
  workflows, deploy credentials, and `pull_request_target` review;
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

## Next Planned Sequence

The Public Index Operator UX baseline is complete. Maintainer tooling can now
prepare accepted-manifest pull request drafts from valid submission reports. The
SpecGraph public registry observation contract is also documented so downstream
graph work can cite exact `/v0` evidence without giving SpecPM graph authority.
Reusable registry observation reports now write local Docker and GitHub Pages
JSON artifacts under `.specpm/registry-observations/` for downstream reviews.
GitHub Actions runtime maintenance is documented for official action majors,
update triggers, validation commands, and the `pull_request_target` post-merge
verification boundary.
GitHub Actions workflow permissions and secret boundaries are documented for
allowed `GITHUB_TOKEN` scopes, FTP secret usage, `pull_request_target` review
rules, and SFTP/Pages deploy evidence boundaries.
The next planned work is:

1. Design the remote package acquisition boundary before archive fetch/cache/add
   behavior is implemented.
2. Define intent taxonomy governance for canonical `intent.*` IDs.

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
