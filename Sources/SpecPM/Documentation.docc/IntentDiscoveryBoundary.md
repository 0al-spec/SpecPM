# Intent Discovery Boundary

SpecPM does not translate plain-text user intent into canonical `intent.*`
IDs, capability IDs, package IDs, or package selections.

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
specpm search-intent intent.document_conversion.email_to_markdown --index .specpm/index.json --json
specpm search document_conversion.email_to_markdown --index .specpm/index.json --json
specpm remote intents --registry http://localhost:8081 --json
specpm remote intent intent.document_conversion.email_to_markdown --registry http://localhost:8081 --json
specpm remote search-intent intent.document_conversion.email_to_markdown --registry http://localhost:8081 --json
specpm remote search document_conversion.email_to_markdown --registry http://localhost:8081 --json
```

The package-manager contract is exact lookup plus validation, inspection, and
metadata verification. `search-intent` only matches explicit capability
`intentIds`; it does not infer intent from package text.

The remote intent catalog is observed metadata from accepted packages. It helps
authors discover existing IDs, but it is not a canonical dictionary.

## Downstream Resolver

Plain-text discovery belongs in ContextBuilder, SpecGraph, or a future
downstream intent resolver.

That resolver may use LLM extraction, embeddings, vector search, lexical
search, reranking, graph traversal, and human review to produce candidate
`intent_id`, `capability_id`, or `package_id` values. Those candidates must then
be verified through SpecPM exact lookup before they become reviewable package
selections.

## Boundary Statement

Embeddings improve recall.

SpecPM provides verification.

SpecGraph and ContextBuilder decide meaning.

## References

- `specs/INTENT_DISCOVERY_BOUNDARY.md`
- `specs/IDENTIFIER_MODEL.md`
- <doc:IdentifierModel>
- <doc:BoundariesAndTrust>
- <doc:SpecGraphIntegration>
