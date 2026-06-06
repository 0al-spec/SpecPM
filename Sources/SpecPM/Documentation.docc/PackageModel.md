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

## Self-Describing Repository

SpecPM dogfoods its own package model. The repository root contains
`specpm.yaml` and `specs/specpm.spec.yaml`, which describe the implemented
public CLI command surface and importable core functions as a `SpecPackage`.

The self-spec is intentionally limited to implemented package-manager behavior.
It may describe explicit read-only remote registry metadata lookup, but it does
not claim remote registry hosting, `specpm publish`, remote archive download,
signing, semantic search, derived artifact generation, or SpecGraph graph
reasoning.

The repository documentation directory is lowercase `specs/`. This avoids a
fragile uppercase/lowercase directory split on case-insensitive filesystems and
keeps the self-spec in the same documentation namespace as the PRD, Workplan,
coverage notes, and JSON contracts.

CI validates the root package and compares the self-spec against the live CLI
parser and exported `specpm.core.__all__` API. Changes to the public command or
core function surface must update `specs/specpm.spec.yaml`.

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

`index.provides.intents` is optional first-class registry metadata. When
present, every listed `intent.*` ID must be backed by a BoundarySpec capability
`intentIds` mapping, and every declared capability intent must appear in the
manifest summary.

Capability entries may optionally include `intentIds`, a list of canonical
`intent.*` IDs that the package-owned capability satisfies. These mappings are
exact metadata, not inferred meaning.

## Abstract Packages

SpecPM may also store abstract `SpecPackage` contracts. An abstract package
defines a desired capability boundary even when no concrete implementation
exists yet. In architecture terms, it acts as an abstract contract or port.
The `intent.*` IDs provide the machine-readable intent marker, so human-facing
fields can stay focused on the domain contract. Concrete packages act as
providers or adapters that may later claim to satisfy the contract.

Abstract packages are still ordinary package data: they use `specpm.yaml`,
`specs/*.spec.yaml`, evidence, provenance, constraints, and exact declared
capabilities. They should make their non-implementation status explicit in
scope, constraints, provenance, and keywords.

This supports dependency inversion at the specification layer: architecture
nodes can depend on abstract contracts before a concrete provider is
selected. For example, a node can depend on a code version control service
contract before a downstream resolver or reviewer chooses GitHub, GitLab,
SourceForge, Gitea, or another provider package.

Concrete packages may later claim implementation or conformance through
reviewed evidence and downstream graph relationships. SpecPM stores the
versioned contract; downstream graph governance decides meaning, relationships,
selection, and substitution.

Other specifications may refine an abstract contract by adding capabilities,
constraints, or provider-specific metadata. They may also compose several
abstract contracts into an aggregate package. This is not object-oriented
inheritance: downstream packages should keep relationships explicit while
architecture modules depend on shared intermediate contracts and more specific
packages carry provider and evidence details.

This increment does not add a first-class `type`, `classification`, or
`conformance` schema field. Abstract package status is expressed through the
current package model: `intent.*` IDs, capability IDs, constraints, provenance,
keywords, and evidence.

The first abstract package is:

```text
packages/intent.package.public_repository_metadata
```

A smaller authoring-only reference example is:

```text
examples/abstract_email_to_markdown_contract
```

It pairs with `examples/email_tools` to show how an abstract contract can
sit between consumers and a concrete provider package without requiring
implicit inheritance.

## Package Sets

SpecPM may also describe package sets as collection entrypoints for related
packages. Package sets are useful for repositories, workspaces, ecosystems, and
product families where one broad package would overclaim the repository but one
narrow package would lose important discovery intent.

A package set groups separate package subjects. It does not make member
packages inherit capabilities, constraints, lifecycle state, acceptance status,
namespace ownership, or trust.

For example:

```text
xyflow.workspace
  contains xyflow.system
  contains xyflow.react
  contains xyflow.svelte
```

The aggregate `xyflow.workspace` package can preserve broad product discovery
intent, while scoped members such as `xyflow.system` and `xyflow.react` keep
their own evidence, capabilities, and acceptance decisions.

Package-set discovery should remain index-based. Exact `intent.*` lookup may
return aggregate and scoped package results directly; consumers should not need
to traverse a root-to-leaf tree before finding a useful package.

The current package-set boundary is documented in <doc:PackageSets> and
`specs/PACKAGE_SETS.md`. Package relation vocabulary is documented in
<doc:PackageRelations> and `specs/PACKAGE_RELATIONS.md`. Search semantics are
documented in <doc:PackageSetSearch> and `specs/PACKAGE_SET_SEARCH.md`.
Registry metadata shape is drafted in <doc:PackageSetRegistryMetadata> and
`specs/PACKAGE_SET_REGISTRY_METADATA.md`. Runtime generator implementation is
planned follow-up work.

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

- `specs/PRD.md`
- `specs/IDENTIFIER_MODEL.md`
- `specs/0002_Abstract_SpecPackage_Conformance_Target_Decision.md`
- `specs/PACKAGE_SETS.md`
- `specs/PACKAGE_RELATIONS.md`
- `specs/PACKAGE_SET_SEARCH.md`
- `specs/PACKAGE_SET_REGISTRY_METADATA.md`
- `RFC/SpecGraph-RFC-0001.md`
- <doc:IdentifierModel>
- <doc:PackageSets>
- <doc:PackageRelations>
- <doc:PackageSetSearch>
- <doc:PackageSetRegistryMetadata>
- <doc:BoundariesAndTrust>
