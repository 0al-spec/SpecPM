# Package Model

The MVP package format is boundary-first. SpecPM manages product and engineering
intent as package data, not as executable code.

The canonical package layout is:

```text
my-package/
  specpm.yaml
  specs/
    main.spec.yaml
  evidence/
  foreign/
```

## Manifest

`specpm.yaml` declares package identity, package metadata, referenced
`BoundarySpec` files, and indexable capabilities.

Required manifest fields include:

- `apiVersion`
- `kind: SpecPackage`
- `metadata.id`
- `metadata.name`
- `metadata.version`
- `metadata.summary`
- `metadata.license`
- `specs`
- `index.provides.capabilities`

## BoundarySpec

A `BoundarySpec` describes a bounded package contract. Required fields include:

- `apiVersion`
- `kind: BoundarySpec`
- `metadata.id`
- `metadata.title`
- `metadata.version`
- `intent.summary`
- `scope.boundedContext`
- `provides.capabilities`
- `interfaces`
- `evidence`

## YAML Restrictions

SpecPM accepts restricted YAML with JSON-compatible maps, arrays, strings,
numbers, booleans, and null values.

SpecPM rejects or reports unsupported input such as:

- anchors and aliases;
- custom YAML tags;
- multiple YAML documents;
- binary or non-JSON values;
- malformed YAML;
- path traversal and symlink escapes.

## Extension Fields

Unknown top-level fields are rejected unless they use the `x-` extension prefix.
Extension fields are preserved as package data. They are not executable
instructions and do not grant authority over host behavior.

## References

- `SPECS/PRD.md`
- `RFC/SpecGraph-RFC-0001.md`
- <doc:BoundariesAndTrust>
