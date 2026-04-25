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

## Suite Shape

The suite is JSON so non-Python implementations can consume it directly:

```text
{
  schemaVersion: 1,
  suite: string,
  cases: ConformanceCase[]
}
```

Each case has:

```text
{
  id: string,
  kind: string,
  expected: object
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

## Non-Goals

The conformance suite does not define remote registry APIs, `specpm publish`,
package signing, namespace governance, semantic search, full dependency solving,
SpecGraph graph reasoning, or ContextBuilder artifact generation.

## References

- `SPECS/CONFORMANCE.md`
- `tests/fixtures/conformance/specpm-conformance-v0.json`
- <doc:BoundariesAndTrust>
