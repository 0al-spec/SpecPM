# Package Set Registry Metadata

Draft public `/v0` metadata shape for package sets and relation-aware search
results.

## Overview

Package-set registry metadata should be additive. Existing consumers should be
able to ignore package-set fields and still read ordinary package metadata,
version metadata, capability search, and exact `intent.*` search results.

Future package metadata may expose:

- `subject.kind`: `package` or `package_set`;
- `subject.scope`: `package`, `aggregate`, or `abstract_contract`;
- `packageSet.members[]`: member summaries, not embedded package metadata;
- `packageSet.members[].package_id`: existing `/v0` package identifier field;
- `packageSet.members[].type`: accepted relation type connecting the set to the
  member;
- `relations[]`: accepted relation summaries with evidence;
- search result `scope` and `match` fields;
- optional `relationContext[]` for explaining connected results.

## Boundary

Registry metadata must not merge aggregate and member package records.

Package-set metadata does not imply:

- inherited capabilities;
- inherited constraints;
- inherited lifecycle state;
- inherited namespace ownership;
- trust propagation;
- automatic package selection.

## Search Results

Exact search results should remain direct indexed matches first. Relation context
may explain a result after discovery:

```json
{
  "package_id": "xyflow.react",
  "scope": "package",
  "match": "direct",
  "relationContext": [
    {
      "type": "contains",
      "source": "xyflow.workspace",
      "target": "xyflow.react"
    }
  ]
}
```

Consumers that ignore `relationContext` should still see the direct result.

## References

- `specs/PACKAGE_SET_REGISTRY_METADATA.md`
- `specs/PACKAGE_SET_SEARCH.md`
- `specs/PACKAGE_RELATIONS.md`
- <doc:PackageSetSearch>
- <doc:PackageRelations>
- <doc:DownstreamRegistryConsumers>
