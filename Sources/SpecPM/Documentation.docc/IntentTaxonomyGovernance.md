# Intent Taxonomy Governance

SpecPM exposes exact `intent.*` metadata, but observation is not
standardization. The rule is simple:
observed package declarations do not become canonical vocabulary.

## Current Boundary

The public `/v0` registry publishes observed intent catalog metadata with
`canonical: false`. This helps authors and downstream tools discover existing
IDs, but it is not a standardization decision.

SpecPM does not infer intent meaning from package summaries, rank candidate
packages, or turn natural language into trusted package selections.

## Governance Process

An intent proposal should document:

- proposed `intent.*` ID;
- package-neutral summary;
- user need represented by the ID;
- package-owned capabilities that could map to it;
- nearby intents that should remain separate;
- duplicate and overlap analysis;
- migration notes for deprecation, rename, or supersession.

Reviewers should prefer IDs that are provider-neutral, reusable across packages,
specific enough for exact lookup, and broad enough that more than one
implementation can satisfy them.

## Lifecycle

Intent lifecycle states are policy metadata. Current registry payloads do not
enforce them.

Recommended states are `observed`, `proposed`, `accepted`, `deprecated`,
`superseded`, `rejected`, and `reserved`.

Deprecation or supersession must not silently rewrite package metadata. Package
authors update explicit `intentIds` through normal package version changes.

## Experimental and Private IDs

Experimental and private IDs should stay visibly non-canonical, for example:

- `intent.experimental.<domain>.<name>`
- `intent.private.<org>.<domain>.<name>`

Promotion to accepted canonical vocabulary requires normal review.

## Source Contract

The detailed policy is maintained in `specs/INTENT_TAXONOMY_GOVERNANCE.md`.
