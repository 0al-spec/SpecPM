# Producer Bundle Proposal Policy

SpecPM treats producer-generated candidate bundles as review evidence, not
registry authority.
Producer bundles are not registry authority.

The first expected producer is SpecHarvester. A SpecHarvester bundle may contain
`specpm.yaml`, `specs/*.spec.yaml`, `producer-receipt.json`,
`validation-report.json`, `diagnostics.json`, producer preflight output, and a
static viewer preview. These artifacts help maintainers review a proposal, but
they do not accept or publish a package.

## Boundary

SpecPM owns package validation, accepted-source review, namespace/version
acceptance policy, generated registry metadata after merge, and maintainer
acceptance decisions.

Producer tools own source harvesting, candidate generation, producer receipts,
producer-side reports, producer preflight, and local preview rendering.

The intended flow is:

```text
producer bundle evidence -> SpecPM proposal review -> maintainer decision
```

not:

```text
producer bundle evidence -> automatic SpecPM acceptance
```

## Minimum Evidence

A producer-backed proposal should include or link to:

- `specpm.yaml`
- `specs/*.spec.yaml`
- `producer-receipt.json`
- `validation-report.json`
- `diagnostics.json`
- producer preflight report or command output
- static viewer output, when available
- the proposed accepted-source diff or manifest entry
- the issue, pull request, or maintainer note that records the decision

Absence of producer evidence does not automatically reject a manually authored
package. It means no producer bundle evidence is available for review.

## Intake Checklist

Maintainers should verify that the package validates under SpecPM, the producer
receipt uses `apiVersion: specpm.receipts/v0`,
`kind: SpecPMProducerReceipt`, and
`receiptProfile: generated_spec_package_v0`, output digests match bundle files,
`producer-receipt.json` is not listed in `outputs[]`,
`validation.reportDigest` matches `validation-report.json`,
`diagnostics.digest` matches `diagnostics.json`, public handoff has
`privacy.secretsIncluded: false`, and `humanReview.requiredFor` includes
`public_index_acceptance`.

Reviewers must still inspect package claims against evidence. A generated claim
is not trusted solely because a producer emitted it.

The public-index operator intake checklist is maintained in
`specs/PUBLIC_INDEX_OPERATOR_GUIDE.md` so accepted-manifest pull requests and
producer-backed proposals use the same evidence requirements.

For package-set dry-run evidence, `specpm producer-bundle preflight` can read a
`SpecHarvesterPackageSetHandoffProposal` JSON body directly. It verifies
package-set handoff identity, member IDs, manifest identity, linked evidence
digests, bundle-set preflight status/counts, `contains` relation endpoints, and
the external acceptance boundary without running producer tools.

## Reject And Warning Signals

Reject or request regeneration when required files are missing, receipt identity
is unsupported, digests mismatch, the receipt hashes itself, diagnostics status
is `failed`, public handoff includes secrets, package identity disagrees across
artifacts, or the proposal asks SpecPM to execute producer tools, prompts,
analyzers, package scripts, or package content.

Warnings may be acceptable when producer evidence is absent for a manually
authored package, `humanReview.status` is still `required` or `pending` before a
maintainer decision, diagnostics are warning-only and explained, external
inputs are referenced by digest and redaction policy, or static viewer output is
absent while machine-readable evidence is available.

## Maintainer Override

Overrides must be recorded outside the producer receipt, such as in the
accepted-source pull request, submission issue, or future SpecPM acceptance
record. The override should name the package ID and version, the bundle or
receipt reference, the failed or missing evidence being overridden, the reason
the package can still be reviewed safely, and the maintainer review location.

Receipts describe producer output. SpecPM review records acceptance decisions.

## Optional CI Preflight

SpecPM can preflight machine-readable producer proposal evidence:

```bash
specpm producer-bundle preflight --body <proposal-body.md> [--root <checkout-or-artifact-root>] --json
```

The command reads `producerEvidenceLinks` and `registryAcceptanceDecision`
blocks from a pull request body, checks required roles, explicit path scopes,
and the `evidence_only` producer receipt boundary. With `--root`, it also checks
linked files and SHA-256 digests under that root.

The preflight is review evidence only. It never runs producer tools or package
content and does not replace maintainer acceptance.

The optional `.github/workflows/producer-bundle-preflight.yml` pull request
workflow runs this command only for producer-backed proposal bodies.

## Fixture Alignment

Cross-repository fixture ownership and drift handling are defined in
<doc:ProducerBundleFixturePolicy>. SpecPM owns consumer contract examples and
preflight expectations. SpecHarvester owns generated candidate bundle examples.

## Proposal Automation

SpecHarvester-to-SpecPM pull request body requirements are defined in
<doc:ProducerBundleProposalAutomation>. Producer automation should emit
`producerEvidenceLinks` and `registryAcceptanceDecision` fenced JSON blocks for
consumer-side SpecPM preflight.

## Acceptance Decision Record

Machine-readable maintainer decisions are defined in
<doc:RegistryAcceptanceDecisions>. The record links producer evidence to
maintainer review while keeping producer receipts as `evidence_only`.

## Multi-Package Intake

Package-set proposals that include multiple related generated packages are
covered by <doc:MultiPackageProducerIntake>. Maintainers may accept only part of
the bundle set, and package-set acceptance does not imply member package or
relation acceptance.

Package-set handoff preflight has been exercised end-to-end on a real `xyflow`
checkout: SpecHarvester produced the package-set handoff, SpecPM consumed the
handoff through `specpm producer-bundle preflight`, and the report passed with
zero errors and zero warnings.

The next package-set implementation step should be maintainer-selected
accepted-source materialization. The helper should accept an explicit selection
of package IDs and relation IDs, generate a proposed accepted-source diff, and
leave final acceptance to maintainer review. It must not treat producer output or
a passing package-set preflight as automatic registry acceptance.
