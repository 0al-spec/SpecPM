# Registry Acceptance Decisions

`SpecPMRegistryAcceptanceDecision` is the machine-readable maintainer decision
record for public-index acceptance.

## Boundary

Producer evidence can support a maintainer decision, but it cannot make the
decision. Authority remains with SpecPM maintainer review.

```text
producer evidence -> SpecPM maintainer review -> registry acceptance decision
```

The record keeps `producerReceiptAuthority` as `evidence_only`.

## Shape

Decision records use `apiVersion: specpm.decisions/v0`, `kind:
SpecPMRegistryAcceptanceDecision`, and `schemaVersion: 1`. They identify the
package, version, proposal location, maintainer review location, status,
accepted-source effect, and producer evidence paths.

Valid record statuses are `pending`, `approved`, `rejected`, `override`, and
`withdrawn`.

The canonical contract is `specs/REGISTRY_ACCEPTANCE_DECISIONS.md`.
