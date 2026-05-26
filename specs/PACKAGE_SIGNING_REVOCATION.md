# SpecPM Package Signing and Revocation Policy

Status: Draft
Updated: 2026-05-26
Scope: future package signature verification, revocation, lifecycle, and provenance receipt policy

## Purpose

This document defines the trust boundary for future SpecPM package signing and
revocation behavior.

Current SpecPM can validate package shape, build deterministic archives, expose
archive digests, and generate static registry metadata from maintainer-reviewed
sources. Current SpecPM does not verify package signatures, manage signing keys,
publish revocation lists, or enforce publisher trust.

Digest verification proves bytes, not publisher authority. A matching archive
digest can show that downloaded bytes match registry metadata, but it does not
prove who authored, reviewed, accepted, or later revoked the package.

## Current Boundary

Today, public registry trust comes from:

- reviewed changes to `public-index/accepted-packages.yml`;
- pinned public Git source revisions for remote accepted entries;
- deterministic `specpm-tar-gzip-v0` archives;
- generated archive SHA-256 digests;
- GitHub Actions build evidence and Pages/SFTP deployment evidence.

Those inputs are useful operational evidence. They are not a cryptographic
publisher trust web.

No current command may treat the presence of `source.digest`, `yanked`,
`deprecated`, package provenance fields, or public index visibility as signature
verification.

## Future Signature Subjects

A future signing profile must define exactly what is signed before runtime
verification is implemented.

At minimum, a package signature must bind:

- package ID;
- package version;
- archive format;
- archive digest algorithm and value;
- registry API profile or registry namespace where the signature is asserted;
- issuer identity or public key identity;
- signing time or signed build event time;
- optional source repository, exact source revision, and build workflow identity
  when the registry claims source-to-archive provenance.

Signing a mutable branch name, tag label, package summary, or registry UI label
is not sufficient. Mutable labels may be included for operator readability only
when the signed subject also includes immutable revision or digest data.

## Verification Policy

Signature verification must be policy-driven. Different registries may require
different trust roots, but the active trust root must be explicit.

A future verification implementation must:

1. Select an exact package ID and version.
2. Read registry metadata and archive descriptor.
3. Verify archive digest before trusting archive bytes.
4. Verify any required signature or attestation against the configured trust
   policy.
5. Check revocation and lifecycle policy before cache or lock writes.
6. Validate package shape as untrusted data.
7. Record deterministic verification evidence in cache, lock, or audit metadata
   only after the required checks succeed.

Verification runtime must fail closed when policy requires a signature and the
signature is missing, invalid, expired, revoked, or bound to different package
metadata.

When a registry profile declares signatures optional, missing or unverifiable
signatures may be warnings, but they must not be reported as verified trust.

## Revocation and Lifecycle

Revocation is a policy decision, not deletion.

Recommended lifecycle meanings:

- `visible`: registry metadata is present and may be considered by consumers.
- `deprecated`: visible and usually eligible, but discouraged for new
  selections when a better version exists.
- `yanked`: visible for audit and reproducibility, but should not be selected
  for new adds unless an explicit override policy allows it.
- `revoked`: cryptographic or governance trust is withdrawn; future
  acquisition must fail closed unless an explicit emergency recovery policy
  allows a pinned exception.
- `removed`: metadata is intentionally absent from the current registry view;
  historical evidence may still exist in Git history, workflow artifacts, or
  external audit logs.

Yanked and deprecated state are registry lifecycle metadata. They do not prove
signature status. Revocation may be caused by key compromise, publisher
identity loss, malicious package content, incorrect provenance, policy breach,
or superseding governance decision.

Revocation must not silently rewrite package metadata, archive digests, lock
entries, or historical receipts. Consumers need enough evidence to explain why
a package that was once visible is no longer trusted.

## Provenance Receipts

A future provenance receipt should be a machine-readable record of what the
registry accepted, generated, verified, and deployed.

At minimum, a stronger receipt should record:

- package ID and version;
- source repository and exact source revision when applicable;
- archive format, size, and digest;
- accepted manifest entry or reviewed pull request;
- build workflow name, run ID, run attempt, and source revision;
- registry profile and output endpoint;
- verification policy version;
- signature subject and verification result when signing exists;
- lifecycle state at receipt creation time.

Receipts should be append-only evidence where practical. They may live in
workflow artifacts, generated registry metadata, transparency logs, enterprise
audit stores, or a later SpecPM-defined receipt format. This policy does not
choose a storage backend.

The draft receipt envelope and audit evidence profile are documented in
`specs/PROVENANCE_RECEIPTS.md`.

## Public vs Enterprise Registries

The public static registry and future enterprise registries have different
trust needs.

Public static registry policy should prefer:

- reviewed Git changes;
- static generated metadata;
- deterministic archives and digests;
- public build evidence;
- optional public signatures or attestations when the profile is designed.

Enterprise registry policy may additionally require:

- private trust anchors;
- tenant-specific signer allowlists;
- identity provider integration;
- private revocation feeds;
- audit retention rules;
- incident response workflows.

Enterprise requirements must not be forced into the public static index unless
the public profile explicitly adopts them.

## Non-Goals

This policy does not add:

- runtime signature verification;
- signing key generation, storage, rotation, or recovery;
- private key handling;
- Sigstore, Cosign, PKI, DID, or transparency log integration;
- registry mutation APIs;
- package upload or publish endpoints;
- revocation feed hosting;
- automatic package removal;
- package execution;
- semantic package selection;
- graph authority.

No private keys, signing tokens, recovery codes, or credential material belong
in SpecPM package metadata, issue forms, registry fixtures, generated receipts,
or tests.

Package content can describe desired outputs. Package content cannot command the
host.

## Source Contract

This document is policy evidence for future package trust work. Runtime
signature verification, revocation feed handling, or provenance receipt schema
changes must reference this boundary and define machine-readable fields before
implementation.
