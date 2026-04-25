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

## Recommended Next Documentation Track

The next useful documentation increment is a read-only remote registry API
contract:

- package metadata lookup;
- version lookup;
- exact capability search metadata;
- yanked and deprecated state;
- stable error and status vocabulary;
- static conformance fixtures without network tests.

`specpm publish`, auth, signing, namespace governance, and remote service
implementation should follow after the remote API contract is stable.

## References

- `specs/WORKPLAN.md`
- `specs/RFC_0001_COVERAGE.md`
- <doc:Conformance>
