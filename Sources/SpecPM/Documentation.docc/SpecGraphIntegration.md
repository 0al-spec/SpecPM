# SpecGraph Integration

SpecPM is a package substrate for SpecGraph. It makes specification intent
portable, inspectable, and locally testable.

## Inbox Bridge

SpecGraph can materialize draft package bundles under:

```text
.specgraph_exports/<package_id>/
```

SpecPM can list and inspect these bundles:

```bash
specpm inbox list --root .specgraph_exports --json
specpm inbox inspect <package-id> --root .specgraph_exports --json
```

The inbox bridge is local and review-oriented. It does not automatically import
draft bundles into canonical SpecGraph files.

## Public Index Observation

The local public index service gives SpecGraph and ContextBuilder a read-only
registry surface to observe:

```bash
make public-index-up
specpm remote status --registry http://localhost:8081 --json
specpm remote packages --registry http://localhost:8081 --json
specpm remote search document_conversion.email_to_markdown --registry http://localhost:8081 --json
```

`status` answers whether the registry surface is visible and which profile it
implements. `packages` lists the visible package IDs and versions. These
commands read metadata only; they do not download archives, install packages,
mutate SpecGraph state, or execute package content.

## Responsibilities

SpecPM owns:

- package layout;
- package validation;
- deterministic packing;
- local indexing and exact search;
- machine-readable inspection;
- structural diff;
- local lifecycle metadata;
- stable viewer-facing JSON contracts.

SpecGraph owns or coordinates:

- canonical graph semantics;
- relationships between specs;
- refinement and proposal lanes;
- feedback incorporation;
- product reasoning over specs;
- deciding what context is needed.

ContextBuilder or downstream tools own:

- assembling context for a target artifact;
- generating PRDs, briefs, issues, test plans, or review reports;
- applying artifact-specific policies;
- running artifact-level evaluation.

## Boundary Statements

SpecPM may carry intent; SpecGraph decides meaning.

Package content can describe desired outputs. Package content cannot command the host.

## References

- `specs/PRD.md`
- `specs/0001_Derived_Artifact_Profile_Decision.md`
- <doc:BoundariesAndTrust>
