# SpecGraph Registry Observation Contract

Status: Public alpha downstream contract.
Updated: 2026-05-21
Scope: SpecGraph observation of the SpecPM public `/v0` registry

## Purpose

This contract defines the registry evidence SpecGraph should capture before it
claims that a public SpecPM package, exact version, capability, or observed
intent is visible, missing, yanked, deprecated, or drifting.

SpecPM remains the metadata substrate. SpecGraph remains responsible for graph
reasoning, substitution, refinement, drift interpretation, and canonical graph
mutation.

## Boundary

SpecPM registry evidence is read-only metadata:

```text
SpecPM /v0 registry payloads -> observed package evidence
SpecGraph governance         -> graph meaning and action
```

The observation contract does not add a new registry endpoint, request-time
mutation API, `specpm publish`, package acquisition, package execution,
semantic resolver, or graph authority to SpecPM core.

## Evidence Endpoints

SpecGraph should cite evidence derived from the exact endpoint payloads that
support each claim:

| Claim | Required evidence |
| --- | --- |
| Registry reachable | `GET /v0/status` |
| Package visible or missing | `GET /v0/packages` and `GET /v0/packages/{package_id}` |
| Exact version visible or missing | `GET /v0/packages/{package_id}/versions/{version}` |
| Version yanked or deprecated | `GET /v0/packages/{package_id}/versions/{version}` state fields |
| Capability visible or missing | `GET /v0/capabilities/{capability_id}/packages` |
| Intent observed or missing | `GET /v0/intents/{intent_id}` and `GET /v0/intents/{intent_id}/packages` |
| Registry drift | `GET /v0/status` plus the package, version, capability, or intent payload being compared |

The registry API family is `specpm.registry/v0`. That is separate from package
document `apiVersion` values such as `specpm.dev/v0.1`, package
`metadata.version`, and the SpecPM CLI/library implementation version.

## Observation Evidence Document

SpecGraph may store observation evidence in review artifacts using this shape:

```json
{
  "schemaVersion": 1,
  "kind": "SpecGraphRegistryObservation",
  "registry": {
    "url": "https://0al-spec.github.io/SpecPM",
    "apiVersion": "specpm.registry/v0",
    "profile": "public_static_index",
    "buildRevision": "0de4fca1d8c32bbe443eb9bae7a3fa4bf8f0cb6b"
  },
  "expectation": {
    "packageId": "specpm.core",
    "version": "0.2.0",
    "capabilityIds": ["specpm.registry.public_static_index"],
    "intentIds": ["intent.registry.intent_lookup"]
  },
  "evidence": [
    {
      "id": "registry_status",
      "endpoint": "GET /v0/status",
      "status": "ok",
      "payloadDigest": "sha256:6f8f...",
      "extracted": {
        "profile": "public_static_index",
        "read_only": true,
        "buildRevision": "0de4fca1d8c32bbe443eb9bae7a3fa4bf8f0cb6b"
      }
    }
  ],
  "findings": [
    {
      "subject": "package:specpm.core@0.2.0",
      "status": "visible",
      "evidence": ["registry_status"]
    }
  ]
}
```

The document is a downstream evidence wrapper. Evidence items may embed the
canonical `/v0` response under `payload`, store a `payloadDigest`, point to a
separately attached payload file, and include an `extracted` projection for
review readability. An `extracted` value is not a replacement registry schema;
it is only a named projection from the cited endpoint payload. The important
contract is that each finding cites concrete `/v0` evidence by ID.

## Finding Status

Use this vocabulary for reviewable observations:

- `visible`: the expected package, version, capability, or intent is present in
  the required endpoint payloads.
- `missing`: the endpoint was readable, but the expected subject was absent.
- `yanked`: the exact version is visible and its lifecycle state has
  `yanked: true`.
- `deprecated`: the exact version is visible and its lifecycle state has
  `deprecated: true`.
- `drift`: observed metadata differs from the expected baseline, such as build
  revision, package count, version count, digest, latest version, or capability
  result membership.
- `unavailable`: a required endpoint could not be read or returned an invalid
  payload.
- `inconclusive`: the evidence is insufficient to make the claim.

SpecGraph may choose what a finding means for a graph node. SpecPM only defines
the package registry evidence that can be cited.

## Expected Checks

For a package visibility claim, capture:

1. `GET /v0/status` and record registry `profile`, `read_only`,
   implementation `version`, and build `revision`.
2. `GET /v0/packages` and verify the package ID appears in the catalog.
3. `GET /v0/packages/{package_id}` and verify retained versions.
4. `GET /v0/packages/{package_id}/versions/{version}` and record lifecycle
   state, source digest, archive URL, and declared capabilities.

For capability evidence, capture
`GET /v0/capabilities/{capability_id}/packages` and verify that at least one
expected `package_id@version` appears in exact search results.

For intent evidence, capture `GET /v0/intents/{intent_id}` when the summary is
needed and `GET /v0/intents/{intent_id}/packages` when search-style exact
matches are enough. Observed intent IDs are metadata observations, not
canonical graph authority.

For drift evidence, capture the current `GET /v0/status` payload plus the
subject payload being compared. Drift should cite both expected values and
observed values.

## Fixtures

Reference examples live under:

```text
tests/fixtures/specgraph_registry_observation/
```

- `package-visible.json` shows a successful observation for
  `specpm.core@0.2.0`.
- `package-drift.json` shows a reviewable drift/missing observation without
  assigning graph authority to SpecPM.

These fixtures are examples for downstream consumers. They are not generated
registry payloads and they do not replace the canonical remote registry
contract in `specs/REMOTE_REGISTRY_API.md`.

## Non-Goals

This contract does not define:

- SpecGraph graph mutation semantics;
- semantic package or intent selection;
- package substitution policy;
- registry write APIs;
- package archive download, cache, install, or execution;
- signing, trust, or namespace ownership decisions.
