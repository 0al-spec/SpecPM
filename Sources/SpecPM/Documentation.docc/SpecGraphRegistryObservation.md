# SpecGraph Registry Observation

SpecGraph can cite SpecPM public registry metadata as reviewable evidence, but
SpecPM does not decide graph meaning.

The canonical contract is `specs/SPECGRAPH_REGISTRY_OBSERVATION_CONTRACT.md`.
This page summarizes the public documentation boundary.

## Evidence Surface

SpecGraph should capture the exact `/v0` payloads behind a registry claim:

- `GET /v0/status` for registry availability, profile, implementation version,
  and build revision.
- `GET /v0/packages` for visible package catalog membership.
- `GET /v0/packages/{package_id}` for package metadata and retained versions.
- `GET /v0/packages/{package_id}/versions/{version}` for exact version
  metadata, lifecycle state, source digest, and archive URL.
- `GET /v0/capabilities/{capability_id}/packages` for exact capability lookup.
- `GET /v0/intents/{intent_id}` and `GET /v0/intents/{intent_id}/packages` for
  observed intent metadata and exact intent lookup.

## Finding Vocabulary

Downstream observation artifacts should use reviewable statuses such as
`visible`, `missing`, `yanked`, `deprecated`, `drift`, `unavailable`, and
`inconclusive`.

These statuses describe observed registry metadata only. SpecGraph governance
decides whether a finding changes graph state, opens a proposal, blocks a
consumer, or remains informational.

## Boundary

This contract does not add `specpm publish`, registry mutation, package
acquisition, package execution, semantic resolution, package substitution, or
canonical graph authority to SpecPM.

## References

- <doc:SpecGraphIntegration>
- <doc:PublicAlphaRegistry>
- <doc:StaticRegistryPipeline>
- <doc:JSONContracts>
