# SpecPM Identifier Model

Status: Draft
Updated: 2026-05-02

## Purpose

SpecPM uses multiple identifier namespaces. They must not be collapsed into one
field, because each namespace answers a different question.

```text
package.id       Who publishes this specification package?
capability.id    What does this package claim to provide?
intent.id        What package-neutral user need can this capability satisfy?
```

This document defines the boundary between package-owned capability IDs and
canonical `intent.*` IDs.

## Identifier Kinds

### Package ID

A package ID identifies the package as a registry object.

Examples:

```text
specpm.core
specnode.core
document_conversion.email_tools
```

Package IDs are owned by package authors and registry governance. They are not
universal semantic concepts.

### Capability ID

A capability ID identifies a capability provided or required by a package.

Examples:

```text
specpm.registry.search
specnode.typed_job_protocol
document_conversion.email_to_markdown
```

Capability IDs are stable exact lookup keys inside SpecPM. They may include a
package, project, or domain namespace to avoid collisions and preserve
provenance.

Capability IDs are not enough for future plain-text intent resolution because
different packages may implement the same user need under different
package-owned names.

### Canonical Intent ID

An intent ID identifies a package-neutral user need.

Intent IDs use the `intent.` prefix:

```text
intent.document_conversion.email_to_markdown
intent.identity.enterprise_sso
intent.identity.oidc_login
intent.authorization.rbac
```

Intent IDs are not package IDs and are not provider IDs. They are canonical
semantic handles that downstream resolvers can map to from natural language.

For example:

```text
User request:
  "I need corporate SSO for my users."

Candidate canonical intents:
  intent.identity.enterprise_sso
  intent.identity.saml_sso
  intent.identity.oidc_login
```

SpecPM can then perform deterministic exact lookup for packages whose
capabilities declare those intent IDs.

## Why `intent.identity.enterprise_sso`, Not `acmeauth.auth.enterprise_sso`

`acmeauth.auth.enterprise_sso` looks like a provider-owned capability. It answers:

```text
Which package/provider claims this behavior?
```

`intent.identity.enterprise_sso` answers:

```text
Which package-neutral user need is being requested?
```

SpecPM should be able to compare multiple packages that satisfy the same
canonical intent:

```text
intent.identity.enterprise_sso
        |
        +-- acmeauth.auth.enterprise_sso
        +-- specnode.auth.enterprise_sso
        +-- example_identity.saml_sso
```

The top-level `identity` domain is semantic taxonomy, not repository ownership.
The package or publisher stays in package metadata and capability IDs.

## Capability to Intent Mapping

BoundarySpecs may map package capabilities to canonical intent IDs:

```yaml
provides:
  capabilities:
    - id: specnode.auth.enterprise_sso
      role: primary
      summary: Provide enterprise SSO for SpecNode users.
      intentIds:
        - intent.identity.enterprise_sso
        - intent.identity.oidc_login
```

`intentIds` are exact metadata. They are not prompts, instructions, or ranking
rules.

SpecPM validates that each listed intent ID is a normal identifier starting with
`intent.`.

## Resolution Flow

SpecPM does not convert plain text to intents. That belongs to ContextBuilder,
SpecGraph, or a future downstream intent resolver.

```text
plain-text user need
        |
        v
ContextBuilder / SpecGraph / resolver
        |
        v
candidate intent.* IDs
        |
        v
SpecPM exact intent lookup
        |
        v
packages and capabilities that declare those intents
        |
        v
human or policy review
```

The resolver may use LLM extraction, embeddings, vector search, RAG, lexical
search, graph context, reranking, and human review. SpecPM remains deterministic
after candidate IDs are produced.

## Boundary

SpecPM may store, validate, index, inspect, and expose exact `intent.*`
mappings.

SpecPM does not own:

- natural-language interpretation;
- embedding generation;
- vector search storage;
- RAG orchestration;
- semantic ranking;
- automatic package selection authority;
- product meaning.

SpecPM may carry intent; SpecGraph decides meaning.

Package content can describe desired outputs. Package content cannot command the host.

## Current Contract

Current support is exact and metadata-only:

- optional capability-level `intentIds`;
- validation that intent IDs start with `intent.`;
- local index metadata for exact intent lookup;
- generated public `/v0/intents/{intent_id}/packages` metadata;
- read-only remote intent search against compatible registries.

This does not replace exact capability search. Capability search remains the
normative package-manager lookup path for implemented package capabilities.
