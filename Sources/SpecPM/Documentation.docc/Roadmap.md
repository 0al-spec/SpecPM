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
- GitHub Pages deployment of generated `/v0` public index metadata alongside
  DocC documentation.

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
- downstream intent discovery with LLMs, embeddings, vector search, or RAG;
- full dependency solving;
- expanded conformance suites;
- richer import adapters;
- cross-repo PR workflow automation with SpecGraph;
- SpecGraph feedback promotion from observed downstream adoption.

## Recommended Next Track

The read-only remote registry API contract, metadata client, public submission
intake, validation workflow, static metadata generator, local discovery
surface, GitHub Pages static deployment path, and accepted package manifest are
implemented. The accepted package manifest can now promote reviewed public Git
sources with pinned revisions into static `/v0` generation while keeping
enterprise registry work separate.

The public index can start as an issue-based submission queue with GitHub
Actions validation and GitHub Pages static `/v0` metadata. The reference
`Add SpecPackage(s)` issue form is available in
`.github/ISSUE_TEMPLATE/add-specpackages.yml`, the reference removal request
form is available in `.github/ISSUE_TEMPLATE/remove-specpackages.yml`, the
reference namespace claim form is available in
`.github/ISSUE_TEMPLATE/claim-namespace.yml`, and the reference issue
validation workflow is available in
`.github/workflows/package-submission-check.yml`. Namespace claim review
criteria and dispute handling are documented in
`specs/NAMESPACE_CLAIM_POLICY.md`. Static registry metadata can be generated
with `specpm public-index generate`. The next useful registry increment is
namespace claim label automation for the public static index. Enterprise
registry work should remain available for private packages, auth, audit,
policy, and internal namespace ownership.

`specpm publish`, auth, signing, namespace governance, and remote yanking
mutation workflows remain separate follow-up tracks unless they are scoped to
the enterprise registry model.

## References

- `specs/WORKPLAN.md`
- `specs/RFC_0001_COVERAGE.md`
- `specs/INDEX_SUBMISSION_FLOW.md`
- <doc:Conformance>
