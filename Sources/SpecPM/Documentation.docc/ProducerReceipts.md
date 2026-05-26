# Producer Receipts

SpecPM producer receipts are planned machine-readable evidence records for
tools that generate or assist `SpecPackage` and `BoundarySpec` content.

Producer receipts are evidence, not authority. A receipt records which producer
tool, inputs, configuration, output files, validation result, diagnostics,
review handoff, privacy claims, and audit evidence produced a package
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
diagnostics: []
review: {}
privacy: {}
audit: {}
```

The initial generated package profile is `generated_spec_package_v0`.

## Required Evidence Areas

Producer receipts should record:

- generated package ID, version, API version, and package root;
- producer name, version, repository, and exact source revision when available;
- source, analyzer, template, prompt, configuration, and previous-spec inputs
  by digest;
- generated `specpm.yaml`, `specs/*.spec.yaml`, and evidence file digests;
- validation status, warning count, and error count;
- diagnostics for skipped files, unsupported languages, uncertainty, or lossy
  summaries;
- review handoff evidence;
- redaction and secret-handling claims;
- audit evidence references.

## Boundary

Current SpecPM does not generate, validate, require, or index producer
receipts. Future producer receipt generation, validation, publication, or
registry behavior must reference the detailed policy first.

The detailed policy is maintained in `specs/PRODUCER_RECEIPTS.md`.
