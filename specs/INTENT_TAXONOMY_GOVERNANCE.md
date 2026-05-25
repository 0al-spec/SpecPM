# SpecPM Intent Taxonomy Governance

Status: Draft
Updated: 2026-05-26
Scope: canonical `intent.*` review, lifecycle, and capability mapping policy

## Purpose

This document defines how SpecPM treats package-neutral `intent.*` IDs before
any downstream resolver turns natural language into package candidates.

SpecPM can store, validate, index, inspect, and expose exact `intent.*`
mappings. SpecPM must not make observed package declarations canonical by
itself. Taxonomy governance is the review process that decides when an
`intent.*` ID is accepted as a stable package-neutral semantic handle.

## Terms

- `capability.id`: package-owned exact capability key.
- `intent.id`: package-neutral user need under the `intent.` prefix.
- `observed intent`: an `intent.*` ID found in accepted package metadata.
- `candidate intent`: an `intent.*` ID proposed for canonical review.
- `accepted intent`: a reviewed canonical `intent.*` ID.
- `deprecated intent`: an accepted intent that should not be used for new
  packages.
- `rejected intent`: a reviewed proposal that should not be reused without new
  evidence.

Observed intent metadata is useful for discovery, duplicate detection, and exact
lookup. Observation is not standardization.

## Current Boundary

The current public `/v0` registry publishes observed intent catalog metadata.
Observed catalog entries are metadata evidence and use `canonical: false`.

SpecPM does not currently publish a canonical intent dictionary, does not rank
intents, does not infer meaning from package summaries, and does not convert
plain text into trusted package selections.

Canonical meaning belongs to a reviewed governance process and may be consumed
by ContextBuilder, SpecGraph, or downstream resolver tools.

## Proposal Requirements

An intent proposal should be made as a reviewed repository change or issue and
should include:

- proposed `intent.*` ID;
- short package-neutral summary;
- user need the intent represents;
- examples of package-owned capabilities that could map to the intent;
- non-goals and nearby intents that should not be collapsed into it;
- duplicate and overlap analysis against observed intent IDs;
- expected downstream consumers;
- migration notes when replacing or deprecating an existing intent;
- reviewer decision: accept, reject, deprecate, supersede, or request changes.

The proposed ID must be stable enough to outlive one package, provider, product,
repository, or implementation technology.

## Review Criteria

Reviewers should accept an intent only when it is:

- provider-neutral;
- package-neutral;
- phrased as a user or system need rather than an implementation brand;
- specific enough for exact lookup;
- broad enough that more than one implementation can satisfy it;
- distinct from existing accepted or observed intents;
- compatible with explicit capability-to-intent mappings;
- safe to expose as metadata without granting package execution authority.

Reviewers should reject or request changes when an intent is:

- a package ID or provider name in disguise;
- a concrete implementation detail rather than a need;
- too broad to support useful lookup;
- too narrow to be reusable;
- a duplicate of an existing accepted intent;
- dependent on natural-language inference to be understood;
- likely to grant false authority to package content.

## Lifecycle

Intent lifecycle is policy metadata. Current SpecPM registry payloads do not
enforce canonical lifecycle states.

Recommended lifecycle states:

- `observed`: found in package metadata; not canonical.
- `proposed`: under review.
- `accepted`: reviewed canonical ID for package-neutral lookup.
- `deprecated`: accepted but discouraged for new mappings.
- `superseded`: replaced by one or more newer accepted intents.
- `rejected`: reviewed and not accepted.
- `reserved`: held for future design, not available for package claims.

Deprecation and supersession must not silently rewrite package metadata.
Package authors should update explicit `intentIds` through normal package
version changes.

## Experimental and Private Namespaces

Experimental or private intent IDs may be useful before public governance
settles a stable term. These experimental or private intent IDs must stay
visibly non-canonical.

Recommended prefixes:

- `intent.experimental.<domain>.<name>`
- `intent.private.<org>.<domain>.<name>`

Public packages may expose these IDs as observed metadata, but the public
registry must not treat them as accepted canonical vocabulary by observation
alone. Promotion from experimental or private usage to accepted canonical
vocabulary requires a normal proposal and review.

## Conflict Handling

When multiple packages use similar or overlapping intent IDs, maintainers should
record the conflict rather than silently merging meaning.

Possible outcomes:

- keep distinct intents when the user needs differ;
- accept one canonical intent and mark others as deprecated or superseded;
- reject overly broad or provider-specific names;
- reserve a domain while the taxonomy needs more design;
- leave all entries observed-only until downstream evidence is clearer.

SpecPM exact lookup should continue to expose what packages declare. Governance
may guide authors toward better IDs.
It must not hide or mutate declared metadata without an explicit package or registry change.

## Boundary

This governance policy does not add:

- semantic search;
- embedding generation;
- vector search;
- RAG;
- LLM reranking;
- automatic package selection;
- canonical graph mutation;
- package execution;
- runtime enforcement of accepted/deprecated/rejected states.

SpecPM verifies exact IDs and package shape. ContextBuilder, SpecGraph, or
downstream resolver tools may interpret plain text and propose candidate IDs.

SpecPM may carry intent; SpecGraph decides meaning.

Package content can describe desired outputs. Package content cannot command the
host.

## Source Contract

This document is policy evidence for `intent.*` taxonomy work. Future runtime or
registry changes that publish accepted intent dictionaries must reference this
boundary and define machine-readable lifecycle fields separately.
