# Producer Receipts

SpecPM producer receipts are planned machine-readable evidence records for
tools that generate or assist `SpecPackage` and `BoundarySpec` content.

Producer receipts are evidence, not authority. A receipt records which producer
tool, inputs, configuration, output files, validation result, diagnostics,
human review handoff, privacy claims, and audit evidence produced a package
candidate. It does not make generated content trusted, accept a package into a
registry, verify signatures, or require SpecPM to run the producer.

The first expected downstream producer is SpecHarvester, but the contract is
tool-neutral.

## Receipt Envelope

The draft producer receipt envelope is:

```yaml
apiVersion: specpm.receipts/v0
kind: SpecPMProducerReceipt
schemaVersion: 1
receiptProfile: generated_spec_package_v0
subject: {}
producer: {}
inputs: []
configuration: {}
outputs: []
validation: {}
diagnostics: {}
humanReview: {}
privacy: {}
audit: {}
```

The initial generated package profile is `generated_spec_package_v0`.

## Candidate Bundle

Generated candidates intended for SpecPM review should use this minimum layout:

```text
candidate/
  specpm.yaml
  specs/*.spec.yaml
  producer-receipt.json
  validation-report.json
  diagnostics.json
```

`producer-receipt.json` is the machine-readable handoff contract. It hashes
generated outputs such as `specpm.yaml`, `specs/*.spec.yaml`,
`validation-report.json`, and `diagnostics.json`, but it does not include itself
in `outputs[]`. Receipt byte verification belongs in an external review
artifact or pull request tooling.

## Required Evidence Areas

Producer receipts should record:

- generated package ID, version, API version, and package root;
- producer name, version, repository, and exact source revision when available;
- source, analyzer, template, prompt, configuration, and previous-spec inputs
  by digest;
- `configuration.digest` for the normalized generation configuration;
- generated `specpm.yaml`, `specs/*.spec.yaml`, validation report,
  diagnostics, and evidence file digests;
- validation status, warning count, and error count;
- diagnostics status and entries for skipped files, unsupported languages,
  uncertainty, or lossy summaries;
- human review handoff evidence, including `requiredFor` such as
  `public_index_acceptance`;
- redaction and secret-handling claims;
- audit evidence references.

Public index acceptance requires `humanReview.status: approved` or an explicit
maintainer override recorded in the accepted-manifest pull request. Producer
output alone never accepts or publishes a package.

SpecPM-side proposal review policy for these bundles is documented in
<doc:ProducerBundleProposalPolicy>.

## Boundary

Current SpecPM does not generate, validate, require, or index producer
receipts. Future producer receipt generation, validation, publication, or
registry behavior must reference the detailed policy first.

The detailed policy is maintained in `specs/PRODUCER_RECEIPTS.md`.
