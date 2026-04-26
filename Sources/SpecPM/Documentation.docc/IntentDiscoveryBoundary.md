# Intent Discovery Boundary

SpecPM does not translate plain-text user intent into canonical capability IDs,
package IDs, or package selections.

SpecPM is not:

- an LLM prompt processor;
- an embedding generator;
- a vector database;
- a RAG pipeline;
- a semantic capability search engine;
- a recommendation engine;
- a product meaning authority.

## Current Behavior

SpecPM accepts exact structured identifiers:

```bash
specpm search document_conversion.email_to_markdown --index .specpm/index.json --json
specpm remote search document_conversion.email_to_markdown --registry http://localhost:8081 --json
```

The package-manager contract is exact lookup plus validation, inspection, and
metadata verification.

## Downstream Resolver

Plain-text discovery belongs in ContextBuilder, SpecGraph, or a future
downstream intent resolver.

That resolver may use LLM extraction, embeddings, vector search, lexical
search, reranking, graph traversal, and human review to produce candidate
`capability_id` or `package_id` values. Those candidates must then be verified
through SpecPM exact lookup before they become reviewable package selections.

## Boundary Statement

Embeddings improve recall.

SpecPM provides verification.

SpecGraph and ContextBuilder decide meaning.

## References

- `specs/INTENT_DISCOVERY_BOUNDARY.md`
- <doc:BoundariesAndTrust>
- <doc:SpecGraphIntegration>
