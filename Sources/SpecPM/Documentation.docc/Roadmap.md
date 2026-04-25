# Roadmap

The local MVP phases are complete through conformance artifacts.

Completed areas include:

- repository baseline;
- core data loading;
- validator;
- inspect;
- deterministic pack;
- local registry index;
- exact search;
- add and lock;
- SpecGraph inbox;
- structural diff;
- viewer contract stabilization;
- release hardening;
- local registry lifecycle;
- conformance test artifacts.
- remote registry API contract documentation and static payload fixtures;
- read-only remote registry metadata client.

## Post-MVP Tracks

Current post-MVP tracks include:

- remote registry API;
- `specpm publish`;
- remote package yanking governance;
- package signing and trust policies;
- namespace governance;
- natural-language or semantic capability search;
- full dependency solving;
- expanded conformance suites;
- richer import adapters;
- cross-repo PR workflow automation with SpecGraph;
- SpecGraph feedback promotion from observed downstream adoption.

## Recommended Next Track

The read-only remote registry API contract and metadata client are implemented.
The next useful remote increment is service-side behavior or a controlled
download/cache design that still avoids publish, signing, namespace governance,
and remote mutation semantics.

`specpm publish`, auth, signing, namespace governance, and remote yanking
mutation workflows remain separate follow-up tracks.

## References

- `specs/WORKPLAN.md`
- `specs/RFC_0001_COVERAGE.md`
- <doc:Conformance>
