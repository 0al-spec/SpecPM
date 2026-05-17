# 0002 Abstract SpecPackage Intent Contract Decision

Status: Accepted for documentation. Initial package added.

## Decision

SpecPM may store abstract `SpecPackage` contracts that define desired
capability boundaries even when no concrete implementation exists yet. In this
model, an abstract package acts like an intent-level interface contract or
architecture port. Concrete packages act like providers or adapters that may
later satisfy that contract.

An abstract package is a versioned, reviewable specification contract. It is
not an implementation claim, not a provider selection, and must not invent
repository evidence.

Other specifications may later refine the abstract contract by adding
capabilities, stricter constraints, or provider-specific requirements. They may
also compose several abstract contracts into aggregate packages. Concrete
implementation packages may claim conformance through explicit package
metadata, downstream graph relationships, or governance decisions. SpecPM
stores, validates, indexes, and exposes the versioned contract. Downstream
graph governance decides meaning, relationships, selection, and substitution.

## Context

The current registry contains concrete packages such as `specpm.core`,
`specnode.core`, and `document_conversion.email_tools`. These describe observed
package behavior, repository surfaces, or package-manager capabilities.

SpecGraph and other architecture tools also need reusable intent and capability
contracts for desired systems that may not exist yet. Those contracts should be
repository-backed, versioned, validated, and discoverable through the same
registry substrate.

This enables dependency inversion at the specification layer:

```text
SpecGraph architecture node
        |
        | depends on
        v
Abstract SpecPackage
        ^
        | satisfies / conforms_to
        |
Concrete SpecPackage: github.repository_hosting
Concrete SpecPackage: gitlab.repository_hosting
Concrete SpecPackage: gitea.repository_hosting
```

For example, an architecture node can depend on an abstract code version
control service contract before choosing GitHub, GitLab, SourceForge, Gitea, or
another concrete provider package.

This is not object-oriented inheritance. A downstream package may specialize one
contract, satisfy one contract, or compose multiple contracts into a larger
aggregate package, as long as the relationships and evidence remain explicit.

## Accepted Principles

1. `SpecPackage` and `BoundarySpec` remain the primary terms.
2. Abstract packages define desired boundaries, substitution points, and
   evidence expectations, not observed implementation behavior.
3. Abstract packages may provide `intent.*` IDs and intent-contract capability
   IDs that architecture nodes can reference before provider
   selection.
4. Concrete packages act as provider or adapter packages when they claim to
   satisfy an abstract contract.
5. Downstream packages may specialize one abstract contract or compose several
   contracts into an aggregate package, but should keep relationships explicit
   instead of relying on implicit inheritance.
6. Abstract packages must make their non-implementation status explicit in
   scope, constraints, provenance, and keywords.
7. Abstract packages should have documentation, ADR, standards, policy, or
   rationale evidence rather than fake implementation evidence.
8. Abstract packages should not contain `implementationBindings` unless they
   intentionally reference non-executable reference material.
9. Downstream graph governance owns semantic relationships such as
   `implements`, `conforms_to`, `satisfies`, `refines`, `depends_on`, and
   `supersedes`.
10. SpecPM stores versioned package contracts and exposes exact metadata.
11. Package content remains untrusted data.
12. A first-class schema marker for package classification is deferred until
    the package model needs validator-enforced semantics.

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

This package provides an intent-level interface contract for tools that expose
static public repository metadata as reusable specification intent. It is useful
for SpecHarvester, generated candidate packages, and future downstream
relationships between abstract intent contracts and concrete observed package
metadata.

The repository also includes an authoring-only reference example:

```text
examples/abstract_email_to_markdown_contract
```

That example pairs an abstract `intent.document_conversion.email_to_markdown`
contract with the concrete `examples/email_tools` provider-style package. It is
not published in the public alpha registry; it exists to make the contract
shape easy to copy and review.

## Rejected for This Increment

This decision does not add:

- new `SpecPackage` top-level schema fields;
- a `type`, `classification`, or `conformance` schema field;
- runtime validator changes;
- `inspect --json` contract changes;
- semantic conformance evaluation;
- graph relationship storage inside SpecPM core;
- package execution, prompts, or agent workflows;
- automatic canonicalization of observed intent IDs.

## Boundary Statement

SpecPM stores versioned spec contracts and exact package metadata.

Downstream graph governance decides meaning, relationships, provider selection,
and substitution.

Concrete package evidence can support implementation claims. Abstract package
evidence supports contract rationale.

Refining or aggregate package evidence supports the additional capabilities,
constraints, or composition choices introduced by that package.
