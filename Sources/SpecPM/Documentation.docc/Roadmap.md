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
- public index submission issue form and validation workflow;
- static public index `/v0` metadata generator.
- local public index service and discovery endpoints for SpecGraph and
  ContextBuilder observation.

## Post-MVP Tracks

Current post-MVP tracks include:

- remote registry API;
- public SpecPM Index submission flow through GitHub Issues, Actions, and
  GitHub Pages;
- enterprise remote registry deployment;
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

The read-only remote registry API contract, metadata client, public submission
intake, validation workflow, static metadata generator, and local discovery
surface are implemented. The next useful public-index increment is to wire
accepted submissions into a GitHub Pages deployment workflow while keeping
enterprise registry work separate.

The public index can start as an issue-based submission queue with GitHub
Actions validation and GitHub Pages static `/v0` metadata. The reference
`Add SpecPackage(s)` issue form is available in
`.github/ISSUE_TEMPLATE/add-specpackages.yml`, and the reference issue
validation workflow is available in
`.github/workflows/package-submission-check.yml`. Static registry metadata can
be generated with `specpm public-index generate`. Enterprise registry work
should remain available for private packages, auth, audit, policy, and internal
namespace ownership.

`specpm publish`, auth, signing, namespace governance, and remote yanking
mutation workflows remain separate follow-up tracks unless they are scoped to
the enterprise registry model.

## References

- `specs/WORKPLAN.md`
- `specs/RFC_0001_COVERAGE.md`
- `specs/INDEX_SUBMISSION_FLOW.md`
- <doc:Conformance>
