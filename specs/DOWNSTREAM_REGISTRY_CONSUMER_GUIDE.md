# Downstream Registry Consumer Guide

Status: Public alpha consumer guide.

This guide shows how downstream tools can consume the SpecPM public registry as
read-only metadata. It complements `specs/REMOTE_REGISTRY_API.md` and
`specs/PUBLIC_ALPHA.md`. The stricter SpecGraph evidence boundary is defined in
`specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md`.

## Registry Surfaces

Downstream consumers should start with these `/v0` endpoints:

- `GET /v0/status` for registry availability, implementation version, package
  count, version count, capability count, and intent count.
- `GET /v0/packages` for the visible package catalog.
- `GET /v0/packages/{package_id}` for package metadata and retained versions.
- `GET /v0/packages/{package_id}/versions/{version}` for exact version
  metadata, digest, lifecycle state, and archive URL.
- `GET /v0/intents` for observed intent catalog metadata.
- `GET /v0/intents/{intent_id}` for observed intent metadata, matching
  capabilities, and the package versions that declare those mappings.
- `GET /v0/intents/{intent_id}/packages` for exact observed intent lookup.
- `GET /v0/capabilities/{capability_id}/packages` for exact capability lookup.

Use `GET /v0/intents/{intent_id}` when a consumer needs both the observed intent
summary and package metadata. Use `GET /v0/intents/{intent_id}/packages` when it
only needs search-style package results for that exact intent ID.

The registry API family is `specpm.registry/v0`. That is separate from package
document `apiVersion` values such as `specpm.dev/v0.1` and from the SpecPM
implementation version.

## CLI Observation

Local Docker registry:

```bash
make dev-reload
PYTHONPATH=src python -m specpm.cli remote status --registry http://localhost:8081 --json
PYTHONPATH=src python -m specpm.cli remote packages --registry http://localhost:8081 --json
PYTHONPATH=src python -m specpm.cli remote version specpm.core@0.2.0 --registry http://localhost:8081 --json
```

GitHub Pages registry:

```bash
PYTHONPATH=src python -m specpm.cli remote observe \
  --registry https://0al-spec.github.io/SpecPM \
  --package specpm.core \
  --version specpm.core@0.2.0 \
  --capability specpm.registry.public_static_index \
  --json
```

## SpecGraph

SpecGraph should treat SpecPM registry responses as package visibility and
capability evidence. It can cite exact package/version payloads while keeping
graph reasoning, refinement, substitution, and canonical relationships inside
SpecGraph governance.

Useful checks:

- `specpm.core@0.2.0` is visible at an exact version endpoint.
- Required capability IDs are present in exact capability search results.
- Observed `intent.*` IDs are treated as observations, not canonical graph
  authority.
- Registry drift findings cite both expected and observed values, plus the
  exact `/v0` payloads used as evidence.

For reusable review artifacts, run `make public-index-observation-report` for
the local Docker registry or `make pages-observation-report` for GitHub Pages.
The report workflow and comparison guidance are documented in
`specs/REGISTRY_OBSERVATION_REPORTS.md`.

## ContextBuilder

ContextBuilder can use `/v0/status`, `/v0/packages`, and exact package/version
lookups to display registry availability and drift:

- registry is reachable;
- implementation version and build revision are visible;
- expected package IDs and exact versions are visible;
- expected capability IDs resolve through exact lookup;
- local fixture or lab expectations differ from public Pages state.

ContextBuilder should not infer semantic intent matches from package summaries
alone. Plain-text intent resolution remains a downstream candidate-generation
step whose output must be verified through exact SpecPM lookups.

## SpecNode

SpecNode can consume the registry to verify package-generation and typed-job
capability visibility:

- `specnode.core@0.1.0` remains addressable by exact version.
- `specnode.typed_job_protocol` resolves through exact capability lookup.
- Registry metadata can be attached to job diagnostics or readiness checks.

SpecNode should not execute package content from registry metadata. Archive URLs
and digests are static metadata until a future acquisition design defines
download, cache, trust, and failure semantics.

## Boundaries

Downstream consumption is read-only. It does not add `specpm publish`, remote
mutation APIs, package installation, archive acquisition as a client, package
execution, package signing, semantic search, or graph authority to SpecPM core.
