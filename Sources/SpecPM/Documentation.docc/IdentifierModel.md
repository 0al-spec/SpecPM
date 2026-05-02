# Identifier Model

SpecPM separates package identity, package-owned capability identity, and
package-neutral intent identity.

```text
package.id       Registry package identity.
capability.id    Capability claimed by a package.
intent.id        Package-neutral user need.
```

## Package IDs

Package IDs identify registry objects:

```text
specpm.core
specnode.core
document_conversion.email_tools
```

They answer who is publishing the specification package.

## Capability IDs

Capability IDs identify what a package claims to provide or require:

```text
specpm.registry.search
specnode.typed_job_protocol
document_conversion.email_to_markdown
```

They are stable exact lookup keys for SpecPM package-manager behavior.

## Intent IDs

Intent IDs use the `intent.` prefix and describe package-neutral user needs:

```text
intent.document_conversion.email_to_markdown
intent.identity.enterprise_sso
intent.authorization.rbac
```

They are not provider namespaces. A future resolver may map plain text to
candidate `intent.*` IDs, then ask SpecPM for exact metadata lookup.

## Mapping

BoundarySpecs can map package-owned capabilities to canonical intents:

```yaml
provides:
  capabilities:
    - id: document_conversion.email_to_markdown
      role: primary
      summary: Convert email content into Markdown.
      intentIds:
        - intent.document_conversion.email_to_markdown
```

SpecPM validates and indexes these mappings exactly. It does not infer them
from text, embeddings, or package names.

## Commands

```bash
specpm search-intent intent.document_conversion.email_to_markdown --index .specpm/index.json --json
specpm remote search-intent intent.document_conversion.email_to_markdown --registry https://0al-spec.github.io/SpecPM --json
```

## References

- `specs/IDENTIFIER_MODEL.md`
- `specs/INTENT_DISCOVERY_BOUNDARY.md`
- <doc:IntentDiscoveryBoundary>
- <doc:CLIReference>
