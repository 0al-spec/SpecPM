# Producer Bundle Fixture Policy

SpecPM and SpecHarvester keep producer bundle fixtures aligned without making
either repository depend on the other's mutable `main` branch during ordinary
CI.

## Boundary

SpecPM owns the consumer contract examples: producer receipt shape, proposal
policy, proposal body examples, and preflight expectations. SpecHarvester owns
generated candidate bundle examples. SpecHarvester owns generated candidate
bundle examples such as `specpm.yaml`, `specs/*.spec.yaml`,
`producer-receipt.json`, validation report, diagnostics report, producer
preflight report, static viewer evidence, and handoff examples.

Cross-repository checks should pin an exact commit, resolve a release tag to an
expected commit, or copy reviewed local fixtures. They should not treat the
other repository's `main` branch as a trust root.

## Drift-Sensitive Fields

The shared contract is sensitive to producer evidence roles, path scopes,
required flags, evidence status, registry acceptance decision metadata,
producer receipt profile fields, output roles, validation/diagnostics paths, and
`humanReview.requiredFor`.

Digest values, timestamps, workflow URLs, and pull request URLs may differ
between repositories. They are evidence values, not shape authority.

## Update Rule

A pull request that changes the producer bundle shape should either update both
sides, link the matching follow-up pull request, or state that the change is
local-only and does not affect drift-sensitive fields.

The canonical policy is `specs/PRODUCER_BUNDLE_FIXTURE_POLICY.md`.
