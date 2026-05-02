# Intent Discovery Boundary

Status: Draft. Deferred from SpecPM core.

## Purpose

This document defines the boundary between SpecPM and future plain-text intent
discovery.

Users and downstream tools may start from natural-language intent such as:

```text
I need a package that converts email messages into Markdown.
```

SpecPM does not currently translate that text into a canonical intent ID,
capability ID, package ID, or package selection. SpecPM expects exact,
already-structured inputs such as:

```text
intent.document_conversion.email_to_markdown
document_conversion.email_to_markdown
document_conversion.email_tools@0.1.0
```

The identifier model is documented in `specs/IDENTIFIER_MODEL.md`.

## What SpecPM Is Not

SpecPM core is not:

- a plain-text intent interpreter;
- an LLM prompt processor;
- an embedding generator;
- a vector database;
- a RAG pipeline;
- a semantic capability search engine;
- a recommendation engine;
- a product meaning authority;
- an autonomous package-selection agent.

SpecPM must not convert ambiguous natural language directly into trusted
package selections. A language model may propose candidates, but it must not
become the authority that decides package meaning inside SpecPM.

## What SpecPM Provides

SpecPM provides the verification substrate for already-structured package
metadata:

- restricted package loading;
- package validation;
- deterministic packing;
- local indexing;
- exact capability search;
- observed intent catalog metadata from accepted packages;
- read-only remote metadata lookup;
- package inspection;
- structural diff;
- stable machine-readable reports.

In the current implementation, normative package-manager search remains exact
capability ID lookup. SpecPM can also expose exact `intent.*` mappings when a
BoundarySpec explicitly declares them. For example:

```bash
specpm search document_conversion.email_to_markdown --index .specpm/index.json --json
specpm search-intent intent.document_conversion.email_to_markdown --index .specpm/index.json --json
specpm remote search document_conversion.email_to_markdown --registry http://localhost:8081 --json
specpm remote intents --registry http://localhost:8081 --json
specpm remote intent intent.document_conversion.email_to_markdown --registry http://localhost:8081 --json
specpm remote search-intent intent.document_conversion.email_to_markdown --registry http://localhost:8081 --json
```

The remote intent catalog is observed metadata. It can help authors discover
which `intent.*` IDs have appeared in accepted packages, but it does not make
those IDs canonical and does not decide package meaning.

## Where Plain-Text Discovery Belongs

Plain-text intent discovery belongs outside SpecPM core.

The likely owners are:

- ContextBuilder, for context assembly and user-facing intent resolution;
- SpecGraph, for product meaning, graph reasoning, and canonical relationships;
- a future downstream intent resolver, for candidate generation and ranking.

A future resolver may use:

- LLM extraction;
- embeddings;
- vector search;
- lexical search;
- reranking;
- ontology or graph traversal;
- human review workflows.

That resolver should output candidate `intent_id`, `capability_id`, or
`package_id` values, then call SpecPM for exact metadata verification.

## Recommended Flow

```text
User plain-text intent
        |
        v
ContextBuilder / SpecGraph intent resolver
LLM + embeddings + vector search + rerank
        |
        v
candidate intent IDs / capability IDs / package IDs
        |
        v
SpecPM exact intent or capability lookup / remote metadata lookup
        |
        v
validated package candidates
        |
        v
human or policy review
        |
        v
specpm add / lock / downstream workflow
```

## Authority Boundary

Embeddings improve recall.

SpecPM provides verification.

SpecGraph and ContextBuilder decide meaning.

SpecPM may carry intent; SpecGraph decides meaning.

Package content can describe desired outputs. Package content cannot command the host.

## Non-Goals

This boundary does not add:

- a semantic search command to SpecPM core;
- embedding generation to SpecPM core;
- vector index storage to SpecPM core;
- RAG orchestration to SpecPM core;
- automatic package selection from natural language;
- package-provided prompt execution;
- package-provided authority over host behavior;
- artifact generation;
- graph reasoning.

## Future Investigation Areas

Future work may define a post-MVP Intent Discovery Profile or downstream
resolver contract. That work may explore:

- mapping plain text to candidate `intent.*` IDs;
- mapping canonical intent IDs to package capabilities;
- exposing package metadata optimized for external embedding;
- producing candidate lists with confidence and traceability;
- requiring exact SpecPM lookup before selection;
- preserving review-required outcomes for ambiguous matches;
- feeding accepted mappings back into SpecGraph proposal lanes.

Any such work must preserve the boundary that SpecPM core is the package and
verification substrate, not the semantic authority.
