# Package Signing and Revocation

SpecPM currently exposes deterministic archive digests and reviewed registry
metadata, but it does not verify package signatures or enforce publisher trust.

Digest verification proves bytes, not publisher authority.

## Current Boundary

The public static registry is built from reviewed accepted-source changes,
pinned Git revisions, deterministic archives, generated SHA-256 digests, and
CI/deploy evidence. Those records are operational evidence, not a cryptographic
trust web.

No current command treats `source.digest`, lifecycle state, package provenance,
or public index visibility as signature verification.

## Future Verification Policy

Any future signing profile must define the exact signed subject before runtime
verification exists. A package signature should bind package ID, version,
archive format, archive digest, registry profile, issuer identity, signing time,
and source revision when source provenance is claimed.

Verification runtime must fail closed when policy requires a signature and the
signature is missing, invalid, expired, revoked, or bound to different package
metadata.

## Revocation and Lifecycle

Revocation is a policy decision, not deletion.

Recommended lifecycle meanings are `visible`, `deprecated`, `yanked`,
`revoked`, and `removed`.

`deprecated` means visible and usually eligible, but discouraged for new
selections. `yanked` means visible for audit and reproducibility, but not
selected for new adds unless an explicit override policy allows it. `revoked`
means trust is withdrawn and future acquisition must fail closed unless an
explicit emergency recovery policy applies.

## Provenance Receipts

Future provenance receipts should record package ID and version, source revision,
archive digest, reviewed manifest or pull request evidence, build workflow
identity, registry profile, verification policy version, signature result when
available, and lifecycle state.

The draft receipt envelope and audit evidence profile are documented in
<doc:ProvenanceReceipts>.

The detailed policy is maintained in `specs/PACKAGE_SIGNING_REVOCATION.md`.
