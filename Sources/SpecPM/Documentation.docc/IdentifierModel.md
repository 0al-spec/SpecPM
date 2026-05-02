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

SpecPackage manifests may also expose the backed intents as first-class index
metadata:

```yaml
index:
  provides:
    capabilities:
      - document_conversion.email_to_markdown
    intents:
      - intent.document_conversion.email_to_markdown
```

The manifest `intents` list is a registry summary. The BoundarySpec
`intentIds` mapping remains the reviewable source of truth for which concrete
capability satisfies each intent.

## Observed Catalog

The public registry can expose all accepted package `intent.*` IDs as observed
metadata:

```bash
specpm remote intents --registry https://0al-spec.github.io/SpecPM --json
specpm remote intent intent.document_conversion.email_to_markdown --registry https://0al-spec.github.io/SpecPM --json
```

Observed catalog entries help authors reuse existing IDs. They are not a
canonical dictionary and do not decide product meaning.

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
