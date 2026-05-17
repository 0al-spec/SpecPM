# Conformance

SpecPM provides portable conformance artifacts for implementations and
downstream SpecGraph tooling.

The current suite lives at:

```text
tests/fixtures/conformance/specpm-conformance-v0.json
```

The downstream fixture manifest lives at:

```text
tests/fixtures/conformance/fixture-manifest.json
```

Fixture packages live under:

```text
tests/fixtures/conformance/packages/
```

Remote registry API payload fixtures live under:

```text
tests/fixtures/conformance/remote_registry/
tests/fixtures/conformance/enterprise_registry/
```

## Suite Shape

The suite is JSON so non-Python implementations can consume it directly:

```json
{
  "schemaVersion": 1,
  "suite": "specpm-conformance-v0",
  "cases": []
}
```

Each case has:

```json
{
  "id": "valid-package",
  "kind": "validate_package",
  "expected": {}
}
```

Paths are repository-relative. Package content is test data only and must not be
executed.

## Fixture Manifest

`fixture-manifest.json` declares versioned conformance fixture metadata for
downstream consumers. It lists named fixture sets, repository-relative fixture
paths, expected payload `kind` values, `valid` markers, optional `staticPath`
values, and the registry API version used by the payloads.

Positive static smoke sets declare source fixture paths and destination
`staticPath` values for downstream `/v0` trees. Lifecycle examples, error
examples, and negative validation fixtures are separate sets, so consumers do
not accidentally publish invalid or error payloads as normal static endpoints.

The manifest is not a lock file. Consumers such as SpecSpace own their fixture
lock by pinning the SpecPM checkout to an exact commit SHA outside the manifest,
then reading the manifest only as contract metadata. A tag can be used as a
human-readable label, but CI trust should come from the externally pinned
commit revision.

## Current Case Kinds

`validate_package` checks stable validation outcome fields:

- `status`
- `capabilities`
- `error_codes`
- `warning_codes`

Validation fixtures include strict authoring quality warnings for dangling
evidence support targets, ambiguous document IDs, and weak `kind: unknown`
entries.

`registry_lifecycle` checks local index, yank, exact search visibility, add
rejection for yanked packages, unyank, and add success.

`remote_registry_payload` checks static post-MVP registry API payload shape. It
does not start a registry server, perform HTTP requests, download archives, or
mutate registry state. It also includes negative payload-shape cases and
enterprise registry compatibility payloads for the same read-only metadata
contract.

`public_registry_static_index` generates a static public `/v0` tree from
repository fixtures and checks the registry status, package index, package
metadata, package version, exact capability search, observed intent catalog,
exact intent search, adjacent `index.html` static-host payloads, archive digest
metadata, and absent missing package/capability/intent paths.

Read-only remote registry client tests reuse those payloads behind HTTP fetch
stubs. They verify endpoint construction and stable client reports without a
live registry service.

## Non-Goals

The conformance suite does not define `specpm publish`, remote registry service
runtime, remote archive download/install/cache behavior, package signing,
namespace governance, semantic search, full dependency solving, SpecGraph graph
reasoning, semantic intent inference, or ContextBuilder artifact generation.

## References

- `specs/CONFORMANCE.md`
- `specs/REMOTE_REGISTRY_API.md`
- `tests/fixtures/conformance/specpm-conformance-v0.json`
- <doc:BoundariesAndTrust>
