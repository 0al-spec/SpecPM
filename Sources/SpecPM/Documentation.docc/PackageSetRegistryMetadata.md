# Package Set Registry Metadata

Public `/v0` metadata shape for package sets and relation-aware search results.

## Overview

Package-set registry metadata is additive. Existing consumers should be
able to ignore package-set fields and still read ordinary package metadata,
version metadata, capability search, and exact `intent.*` search results.

Package metadata may expose:

- `subject.kind`: `package` or `package_set`;
- `subject.scope`: `package`, `aggregate`, or `abstract_contract`;
- `packageSet.members[]`: member summaries, not embedded package metadata;
- `packageSet.members[].package_id`: existing `/v0` package identifier field;
- `packageSet.members[].type`: accepted relation type connecting the set to the
  member;
- `packageSet.members[].relation_id`: accepted relation identifier;
- `relationContext[]`: accepted relation summaries with evidence;
- search result `scope` and `match` fields;
- `GET /v0/relations`: `RemotePackageRelations` relation index.

Relations are accepted only from maintainer-reviewed
`public-index/accepted-packages.yml` `relations[]` entries. Producer-observed
relations remain review evidence until a maintainer accepts them.

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

## Viewer

The static viewer displays package-set badges, member links, accepted relation
context, and the `/v0/relations` endpoint. It keeps package lists flat: member
packages are not hidden under aggregate package-set entries.

## References

- `specs/PACKAGE_SET_REGISTRY_METADATA.md`
- `specs/PACKAGE_SET_SEARCH.md`
- `specs/PACKAGE_RELATIONS.md`
- `specs/SPECHARVESTER_MONOREPO_DISCOVERY.md`
- <doc:PackageSetSearch>
- <doc:PackageRelations>
- <doc:SpecHarvesterMonorepoDiscovery>
- <doc:DownstreamRegistryConsumers>
