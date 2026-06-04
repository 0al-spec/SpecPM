# Producer Bundle Fixture Policy

Status: Draft
Scope: SpecPM and SpecHarvester fixture alignment for producer-backed package proposals

## Purpose

This policy defines how SpecPM contract examples and SpecHarvester generated
candidate bundle examples stay aligned without making either repository depend
on mutable files from the other repository during ordinary CI.

The goal is drift visibility, not runtime coupling. SpecPM owns the consumer
contract. SpecHarvester owns producer output. Both sides may carry local
fixtures, but changes to the shared shape must be reviewed as a cross-repository
contract update.

## Fixture Classes

SpecPM owns these contract fixtures and examples:

- `tests/fixtures/provenance_receipts/generated-spec-package-receipt.example.json`
- producer proposal body examples embedded in `tests/test_core.py`
- `specs/PRODUCER_RECEIPTS.md`
- `specs/PRODUCER_BUNDLE_PROPOSAL_POLICY.md`
- `specs/PRODUCER_BUNDLE_FIXTURE_POLICY.md`

SpecHarvester owns generated candidate bundle examples and smoke fixtures.
SpecHarvester generated candidate bundle examples include:

- generated `specpm.yaml`
- generated `specs/*.spec.yaml`
- generated `producer-receipt.json`
- generated `validation-report.json`
- generated `diagnostics.json`
- generated producer preflight report
- generated static viewer output or static viewer evidence link
- generated SpecPM handoff documentation examples

Neither repository should read the other repository's `main` branch as a CI
trust root. Cross-repository fixture checks should use an exact commit, a
release tag resolved to an expected commit, or copied local fixtures reviewed in
the same pull request.

## Drift-Sensitive Fields

The following fields are cross-repository contract fields. A change to one of
them requires coordinated fixture updates or an explicit compatibility note:

- `producerEvidenceLinks[].role`
- `producerEvidenceLinks[].path`
- `producerEvidenceLinks[].pathScope`
- `producerEvidenceLinks[].required`
- `producerEvidenceLinks[].status`
- `registryAcceptanceDecision.status`
- `registryAcceptanceDecision.requiredFor`
- `registryAcceptanceDecision.recordKind`
- `registryAcceptanceDecision.producerReceiptAuthority`
- producer receipt `apiVersion`
- producer receipt `kind`
- producer receipt `schemaVersion`
- producer receipt `receiptProfile`
- producer receipt `outputs[].role`
- producer receipt `validation.reportPath`
- producer receipt `diagnostics.path`
- producer receipt `humanReview.requiredFor`

Digest values, generated timestamps, local workflow run URLs, and exact pull
request URLs may differ between repositories. They are review evidence, not
shape authority.

## Update Rule

A pull request that changes the producer bundle shape should do at least one of
the following:

1. Update SpecPM contract fixtures and docs, then open or reference the matching
   SpecHarvester fixture update.
2. Update SpecHarvester generated examples, then open or reference the matching
   SpecPM contract update.
3. State explicitly that the change is local-only and does not affect the
   drift-sensitive fields listed above.

The pull request description should include a short fixture alignment note:

```text
Fixture alignment: SpecPM contract updated; matching SpecHarvester fixture PR: <link-or-not-yet-opened>.
```

## Non-Goals

This policy does not:

- make SpecHarvester output trusted;
- make producer receipts registry authority;
- require SpecPM CI to clone SpecHarvester;
- require SpecHarvester CI to clone SpecPM;
- accept, publish, sign, install, or execute package content.

## Review Checklist

For producer bundle fixture changes, reviewers should verify:

- The change touches the correct owner repository for the edited fixture class.
- Drift-sensitive fields remain compatible or the compatibility note explains
  the change.
- SpecPM proposal preflight still validates required evidence roles.
- SpecHarvester generated examples still emit the required evidence links.
- Any cross-repository follow-up is linked from the pull request.
