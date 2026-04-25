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

`registry_lifecycle` checks local index, yank, exact search visibility, add
rejection for yanked packages, unyank, and add success.

`remote_registry_payload` checks static post-MVP registry API payload shape. It
does not start a registry server, perform HTTP requests, download archives, or
mutate registry state.

## Non-Goals

The conformance suite does not define `specpm publish`, remote registry service
runtime, remote registry client network behavior, package signing, namespace
governance, semantic search, full dependency solving, SpecGraph graph reasoning,
or ContextBuilder artifact generation.

## References

- `specs/CONFORMANCE.md`
- `specs/REMOTE_REGISTRY_API.md`
- `tests/fixtures/conformance/specpm-conformance-v0.json`
- <doc:BoundariesAndTrust>
