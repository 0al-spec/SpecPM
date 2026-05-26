# Provenance Receipts

SpecPM provenance receipts are planned machine-readable evidence records for
exact package versions or registry snapshots.

Receipts are evidence, not authority. A receipt records what source, archive,
review, build, validation, trust policy, lifecycle, and audit evidence was
observed. It does not make package content trusted, verify signatures, mutate
registry payloads, or execute package content.

## Receipt Envelope

The draft receipt envelope is:

```yaml
apiVersion: specpm.receipts/v0
kind: SpecPMProvenanceReceipt
schemaVersion: 1
receiptProfile: public_static_index_build_v0
subject: {}
source: {}
archive: {}
review: {}
build: {}
validation: {}
trust: {}
lifecycle: {}
audit: {}
```

The initial public static profile is `public_static_index_build_v0`.

## Required Evidence Areas

Receipts should record:

- package ID, version, and registry profile;
- source path and exact source revision when source checkout is involved;
- deterministic archive format and digest;
- maintainer review evidence;
- build workflow evidence;
- validation status and warning/error counts;
- trust policy, signature status, and revocation status;
- visible/deprecated/yanked/revoked/removed lifecycle state;
- audit evidence references.

## Boundary

Current SpecPM does not generate provenance receipts. Future receipt generation,
publication, verification, or registry payload changes must reference the
detailed policy first.

The detailed policy is maintained in `specs/PROVENANCE_RECEIPTS.md`.
