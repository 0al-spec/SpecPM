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
- SpecGraph inbox inspection for exported package candidates;
- read-only remote `/v0` metadata lookup;
- static public index generation for GitHub Pages;
- local Docker registry integration at `http://localhost:8081`;
- public alpha registry metadata at `https://0al-spec.github.io/SpecPM`;
- GitHub Issue intake for package submissions, removals, and namespace claims;
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
search, and observation reports.

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
