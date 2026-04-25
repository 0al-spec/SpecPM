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

- `SPECS/PRD.md`
- `SPECS/0001_Derived_Artifact_Profile_Decision.md`
- <doc:BoundariesAndTrust>
