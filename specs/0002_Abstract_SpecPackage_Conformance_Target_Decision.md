# 0002 Abstract SpecPackage and Conformance Target Decision

Status: Accepted for documentation. Initial package added.

## Decision

SpecPM may store abstract `SpecPackage` contracts that define desired
capability boundaries even when no concrete implementation exists yet.

An abstract package is a versioned, reviewable specification contract. It is
not an implementation claim and must not invent repository evidence.

Concrete implementation packages may later claim conformance to an abstract
contract through explicit package metadata, SpecGraph relationships, or
downstream governance. SpecPM stores and validates the contract; SpecGraph
decides graph meaning and relationships.

## Context

The current registry contains concrete packages such as `specpm.core`,
`specnode.core`, and `document_conversion.email_tools`. These describe observed
package behavior, repository surfaces, or package-manager capabilities.

SpecGraph also needs reusable intent and capability contracts for desired
systems that may not exist yet. Those contracts should be repository-backed,
versioned, validated, and discoverable through the same registry substrate.

## Accepted Principles

1. `SpecPackage` and `BoundarySpec` remain the primary terms.
2. Abstract packages define desired boundaries, not observed implementation
   behavior.
3. Abstract packages may provide `intent.*` IDs and conformance-target
   capability IDs.
4. Abstract packages must make their non-implementation status explicit in
   scope, constraints, provenance, and keywords.
5. Abstract packages should have documentation, ADR, standards, policy, or
   rationale evidence rather than fake implementation evidence.
6. Abstract packages should not contain `implementationBindings` unless they
   intentionally reference non-executable reference material.
7. Concrete packages may claim implementation or conformance separately.
8. SpecGraph owns semantic relationships such as `implements`, `conforms_to`,
   `refines`, `depends_on`, and `supersedes`.
9. SpecPM stores versioned package contracts and exposes exact metadata.
10. Package content remains untrusted data.

## Initial Package

The first abstract package is:

```text
packages/intent.package.public_repository_metadata
```

It defines:

```text
package_id: intent.package.public_repository_metadata
capability: intent.package.public_repository_metadata.contract
intent: intent.package.public_repository_metadata
```

This package provides a conformance target for tools that expose static public
repository metadata as reusable specification intent. It is useful for
SpecHarvester, generated candidate packages, and future SpecGraph relationships
between abstract intent contracts and concrete observed package metadata.

## Rejected for This Increment

This decision does not add:

- new `SpecPackage` top-level schema fields;
- runtime validator changes;
- `inspect --json` contract changes;
- semantic conformance evaluation;
- graph relationship storage inside SpecPM core;
- package execution, prompts, or agent workflows;
- automatic canonicalization of observed intent IDs.

## Boundary Statement

SpecPM stores versioned spec contracts.

SpecGraph decides graph meaning and relationships.

Concrete package evidence can support implementation claims. Abstract package
evidence supports contract rationale.
