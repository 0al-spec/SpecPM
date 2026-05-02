# Conformance

SpecPM provides portable conformance artifacts for implementations and
downstream SpecGraph tooling.

The current suite lives at:

```text
tests/fixtures/conformance/specpm-conformance-v0.json
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
metadata, package version, exact capability search, adjacent `index.html`
static-host payloads, archive digest metadata, and absent missing
package/capability paths.

Read-only remote registry client tests reuse those payloads behind HTTP fetch
stubs. They verify endpoint construction and stable client reports without a
live registry service.

## Non-Goals

The conformance suite does not define `specpm publish`, remote registry service
runtime, remote archive download/install/cache behavior, package signing,
namespace governance, semantic search, full dependency solving, SpecGraph graph
reasoning, or ContextBuilder artifact generation.

## References

- `specs/CONFORMANCE.md`
- `specs/REMOTE_REGISTRY_API.md`
- `tests/fixtures/conformance/specpm-conformance-v0.json`
- <doc:BoundariesAndTrust>
