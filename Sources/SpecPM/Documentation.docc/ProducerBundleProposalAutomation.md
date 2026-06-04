# Producer Bundle Proposal Automation

SpecHarvester-style producer automation should emit machine-readable proposal
evidence that SpecPM can preflight without running the producer.

## Required Blocks

Producer-backed pull requests should include fenced JSON blocks for:

- `producerEvidenceLinks`
- `registryAcceptanceDecision`

Required evidence roles are `accepted_source_bundle`, `manifest`,
`boundary_spec`, `producer_receipt`, `validation_report`, `diagnostics`, and
`accepted_source_diff`. Optional roles are `producer_preflight` and
`static_viewer`.

Each evidence link declares `role`, non-empty `path`, `pathScope`, `required`,
and `status`. File evidence may also carry a `sha256:<hex>` digest.

## Acceptance Boundary

Producer automation should set `registryAcceptanceDecision.status` to
`external_required`, include `public_index_acceptance` in `requiredFor`, and
keep `producerReceiptAuthority` as `evidence_only`.

Producers must not mark proposals as approved. Maintainer review remains the
registry acceptance authority.

The canonical contract is
`specs/PRODUCER_BUNDLE_PROPOSAL_AUTOMATION.md`.
