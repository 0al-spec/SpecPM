# JSON Contracts

SpecPM JSON output is intended for ContextBuilder, viewers, automation, and
other downstream consumers.

The MVP treats these output shapes as stable contracts:

- validation reports;
- inspection reports;
- pack results;
- search results;
- intent search results;
- add results;
- registry lifecycle results;
- remote registry client results, including status, package index, and intent
  catalog discovery;
- static registry root payloads for the public `/v0` entrypoint;
- observed intent catalog payloads from accepted packages;
- public index generator results;
- inbox list and inbox inspect payloads;
- structural diff results.

## Stability Rules

Consumers can rely on these rules:

- existing top-level fields should not be renamed or removed without a Workplan
  update;
- status vocabularies are closed unless the JSON contract document is updated;
- new optional fields may be added when they are additive;
- arrays are emitted in deterministic order where ordering affects rendering;
- paths are data only and must not be executed or fetched automatically;
- validation warnings and inspection `contract_warnings` are separate surfaces.

## API Versioning

SpecPM has several versioned surfaces:

- package document schema: `specpm.dev/v0.1`;
- registry payload API: `specpm.registry/v0`;
- public endpoint family: `/v0`;
- archive format: `specpm-tar-gzip-v0`;
- local lock/index schema versions;
- CLI and Python JSON reports;
- conformance suite names such as `specpm-conformance-v0`.

These surfaces are related but not interchangeable. A package can use
`apiVersion: specpm.dev/v0.1` while being served through `/v0` registry
payloads using `apiVersion: specpm.registry/v0`.

## Status Vocabularies

Current status vocabularies include:

- validation: `valid`, `warning_only`, `invalid`;
- pack: `packed`, `invalid`;
- index: `indexed`, `unchanged`, `invalid`;
- search: `ok`, `invalid`;
- intent search: `ok`, `invalid`;
- add: `added`, `unchanged`, `ambiguous`, `invalid`;
- registry lifecycle: `yanked`, `unyanked`, `unchanged`, `invalid`;
- remote registry client: `ok`, `not_found`, `invalid`;
- public index generator: `ok`, `invalid`;
- inbox bundle: `draft_visible`, `ready_for_review`, `invalid`, `blocked`;
- diff: `ok`, `invalid`.

## Golden Fixtures

Golden fixtures live under:

```text
tests/fixtures/golden/
```

The tests assert stable documented field subsets while allowing additive object
fields in runtime payloads.

## References

- `specs/JSON_CONTRACTS.md`
- `specs/0003_SpecPM_API_Versioning_Decision.md`
- <doc:IdentifierModel>
- `tests/fixtures/golden/`
- <doc:Conformance>
