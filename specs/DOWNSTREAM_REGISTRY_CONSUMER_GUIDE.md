# Downstream Registry Consumer Guide

Status: Public alpha consumer guide.
Updated: 2026-06-01

This guide shows how downstream tools can consume the SpecPM public registry as
read-only metadata. It complements `specs/REMOTE_REGISTRY_API.md` and
`specs/PUBLIC_ALPHA.md`. The stricter SpecGraph evidence boundary is defined in
`specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md`.

## Contract Summary

Downstream consumers may use the public `/v0` registry as an exact lookup and
evidence surface. They must keep interpretation, graph decisions, generated
artifact policy, and runtime behavior in the downstream project.

Consumer integrations should follow these rules:

- Treat `specpm.registry/v0` as the registry API family being consumed.
- Record the registry base URL, endpoint, observed timestamp, build revision,
  response status, and payload digest or attached payload for every claim.
- Verify exact package IDs, exact package versions, exact capability IDs, and
  exact observed `intent.*` IDs. Do not derive canonical meaning from summaries
  or free text.
- Distinguish registry drift from downstream interpretation. Drift is a
  difference between expected registry evidence and observed registry evidence.
- Treat archive URLs and digests as metadata until a future acquisition design
  defines download, cache, trust, and failure semantics.
- Never execute package content as part of registry observation.

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

## Normative Endpoint Classes

Use these endpoint classes when writing downstream tests or review reports:

| Class | Endpoint | Consumer use |
| --- | --- | --- |
| Registry status | `GET /v0/status` | Availability, registry API family, profile, implementation version, build revision, and aggregate counts. |
| Package catalog | `GET /v0/packages` | Visible package IDs and high-level package list checks. |
| Package metadata | `GET /v0/packages/{package_id}` | Retained versions and package-level metadata for one exact package ID. |
| Version metadata | `GET /v0/packages/{package_id}/versions/{version}` | Exact version state, digest, archive URL, lifecycle flags, and declared capabilities. |
| Package relations | `GET /v0/relations` | Accepted package-set and package-to-package relation metadata. |
| Capability lookup | `GET /v0/capabilities/{capability_id}/packages` | Exact capability membership evidence. |
| Intent catalog | `GET /v0/intents` | Observed intent catalog overview for discovery and duplicate detection. |
| Intent metadata | `GET /v0/intents/{intent_id}` | Observed intent summary plus exact package mappings for one declared intent ID. |
| Intent package lookup | `GET /v0/intents/{intent_id}/packages` | Search-style exact package results for one declared intent ID. |

`GET /v0/status` is required for every reusable observation report. Other
endpoint classes are required only when the downstream claim depends on that
subject. For example, a capability visibility claim needs status plus exact
capability lookup; an exact package-version claim needs status plus package and
version metadata. A package-set membership claim needs status plus
`GET /v0/relations` and the exact package payloads for the aggregate and member
packages.

## Minimum Evidence Envelope

Downstream projects can use their own report schema, but a reviewable registry
claim should preserve this minimum envelope:

```json
{
  "registry": {
    "baseUrl": "https://0al-spec.github.io/SpecPM",
    "apiVersion": "specpm.registry/v0",
    "profile": "public_static_index",
    "buildRevision": "f399b11122b91c3880d655fd5f4bb944e522af60"
  },
  "observedAt": "2026-06-01T00:00:00Z",
  "subject": {
    "kind": "packageVersion",
    "packageId": "specpm.core",
    "version": "0.2.0"
  },
  "expectation": {
    "status": "visible"
  },
  "evidence": [
    {
      "id": "status",
      "endpoint": "GET /v0/status",
      "httpStatus": 200,
      "payloadDigest": "sha256:..."
    }
  ],
  "finding": {
    "status": "visible",
    "evidence": ["status"]
  }
}
```

The envelope is intentionally generic. SpecGraph uses the stricter
`SpecGraphRegistryObservation` shape in
`specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md`. ContextBuilder, SpecNode,
and lab deploy checks can use the same minimum fields in their own diagnostics
or attach the reusable reports described in
`specs/REGISTRY_OBSERVATION_REPORTS.md`.

## Failure Semantics

Use explicit failure vocabulary so downstream reviews do not silently collapse
different problems:

- `unavailable`: the registry base URL or required endpoint could not be read.
- `unsupported_api_version`: `/v0/status` reports an unexpected registry API
  family or profile for the consumer.
- `malformed_payload`: the endpoint returned JSON that does not match the
  expected `/v0` payload shape.
- `missing_subject`: the registry is readable, but the expected package,
  version, capability, or intent is absent.
- `lifecycle_blocked`: the exact version is present but yanked, deprecated, or
  otherwise not acceptable for the consumer's policy.
- `drift`: observed registry metadata differs from the consumer's pinned
  expectation, such as build revision, package count, digest, lifecycle state,
  or search result membership.
- `inconclusive`: the consumer lacks enough evidence to make the claim.

Downstream integrations should report both expected and observed values for
`drift`, `lifecycle_blocked`, and `missing_subject`.

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
- Accepted package-set relations are present in `/v0/relations` and cited as
  registry metadata, not inferred graph authority.
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

ContextBuilder reports should keep enough registry evidence for a user or
reviewer to distinguish "candidate not found in registry" from "candidate was
found but rejected by downstream policy".

## SpecNode

SpecNode can consume the registry to verify package-generation and typed-job
capability visibility:

- `specnode.core@0.1.0` remains addressable by exact version.
- `specnode.typed_job_protocol` resolves through exact capability lookup.
- Registry metadata can be attached to job diagnostics or readiness checks.

SpecNode should not execute package content from registry metadata. Archive URLs
and digests are static metadata until a future acquisition design defines
download, cache, trust, and failure semantics.

SpecNode readiness checks should prefer exact capability and package-version
lookups over package catalog scans. A job diagnostic may cite registry metadata,
but the job protocol remains owned by SpecNode.

## Boundaries

Downstream consumption is read-only. It does not add `specpm publish`, remote
mutation APIs, package installation, archive acquisition as a client, package
execution, package signing, semantic search, or graph authority to SpecPM core.

SpecPM owns the registry metadata shape. Downstream consumers own policy,
candidate selection, graph interpretation, artifact generation, job execution,
and user-facing remediation.
