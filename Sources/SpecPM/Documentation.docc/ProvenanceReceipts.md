# Provenance Receipts

SpecPM provenance receipts are machine-readable evidence records for exact
package versions or registry snapshots.

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

Producer-side receipts for tools that generate `SpecPackage` and
`BoundarySpec` candidates are documented separately in <doc:ProducerReceipts>.

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

Current SpecPM generates non-authoritative provenance receipt artifacts for
public static index package versions during `specpm public-index generate`.
These receipts are static evidence artifacts only; they do not verify
signatures, enforce trust, mutate remote registry state, write lockfiles, cache
archives, or execute package content. Future receipt verification, trust
enforcement, acquisition, or enterprise registry behavior must reference the
detailed policy first.

The detailed policy is maintained in `specs/PROVENANCE_RECEIPTS.md`.
