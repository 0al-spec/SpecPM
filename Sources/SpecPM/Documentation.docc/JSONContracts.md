# JSON Contracts

SpecPM JSON output is intended for ContextBuilder, viewers, automation, and
other downstream consumers.

The MVP treats these output shapes as stable contracts:

- validation reports;
- inspection reports;
- pack results;
- search results;
- add results;
- registry lifecycle results;
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

## Status Vocabularies

Current status vocabularies include:

- validation: `valid`, `warning_only`, `invalid`;
- pack: `packed`, `invalid`;
- index: `indexed`, `unchanged`, `invalid`;
- search: `ok`, `invalid`;
- add: `added`, `unchanged`, `ambiguous`, `invalid`;
- registry lifecycle: `yanked`, `unyanked`, `unchanged`, `invalid`;
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

- `SPECS/JSON_CONTRACTS.md`
- `tests/fixtures/golden/`
- <doc:Conformance>
