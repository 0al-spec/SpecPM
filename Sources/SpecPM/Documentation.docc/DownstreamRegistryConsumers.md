# Downstream Registry Consumers

SpecGraph, ContextBuilder, SpecNode, and lab deploy checks can consume the
SpecPM public `/v0` registry as read-only metadata.

The canonical source document is
`specs/DOWNSTREAM_REGISTRY_CONSUMER_GUIDE.md`.

## Contract

Downstream consumers should treat `specpm.registry/v0` as an exact lookup and
evidence surface:

- `GET /v0/status` records availability, registry profile, implementation
  version, build revision, and aggregate counts.
- `GET /v0/packages` and package lookup endpoints record package visibility.
- `GET /v0/packages/{package_id}/versions/{version}` records exact version
  lifecycle, digest, archive URL, and declared capabilities.
- `GET /v0/relations` records accepted package-set and package-to-package
  relation metadata.
- `GET /v0/capabilities/{capability_id}/packages` records exact capability
  membership.
- `GET /v0/intents`, `GET /v0/intents/{intent_id}`, and
  `GET /v0/intents/{intent_id}/packages` record observed intent metadata.

Every reusable observation should preserve the registry base URL, endpoint,
registry API family, build revision, observed timestamp, HTTP response status,
expected values, observed values, and payload evidence or payload digest.

## Failure Semantics

Downstream tools should distinguish unavailable registries, unsupported API
versions, malformed payloads, missing subjects, lifecycle-blocked versions,
registry drift, and inconclusive evidence.

Those statuses are downstream review findings. SpecPM exposes metadata; the
consumer decides whether a finding blocks a graph change, context build,
typed-job readiness check, or lab deploy.

## Boundaries

Registry consumption does not add `specpm publish`, request-time mutation,
package installation, archive acquisition, package execution, relation
inference, semantic search, or graph authority to SpecPM.

SpecPM owns the `/v0` metadata shape. Downstream consumers own policy, candidate
selection, graph interpretation, artifact generation, job execution, and
user-facing remediation.

## References

- <doc:PublicAlphaRegistry>
- <doc:SpecGraphRegistryObservation>
- <doc:RegistryObservationReports>
- <doc:SpecGraphIntegration>
