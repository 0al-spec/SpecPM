# SpecPM Index Submission Flow

Status: Draft
Updated: 2026-04-27
Scope: post-MVP public index submission and enterprise registry deployment

## Purpose

This document records the intended submission model for a future public
SpecPM Index without redefining the remote registry API contract.

The public index should follow the same broad operational pattern as package
indexes that accept community submissions through GitHub: submit a public
package repository, validate it in CI, review the result, and publish generated
read-only metadata.

This is not a replacement for the remote registry contract. It is one possible
deployment model for that contract.

## Two Registry Models

SpecPM should keep two registry models separate:

1. Public community index.
2. Enterprise remote registry.

The public community index is optimized for openness, reviewability, and low
operational cost. It can use GitHub Issues, pull requests, Actions, and Pages as
the submission queue, validation gate, audit trail, and static read-only API.

The enterprise remote registry is optimized for private packages, access
control, policy enforcement, audit, internal namespace ownership, retention,
and integration with company infrastructure. It should implement the same
read-only metadata contract where possible, but may require auth, private
storage, signing policy, and operational controls that do not belong in the
public index MVP.

## Public Index Submission Flow

The public index submission flow should be issue-based first:

```text
GitHub Issue: Add SpecPackage(s)
        |
        v
Issue form collects public repository URLs
        |
        v
GitHub Action validates each candidate
        |
        v
Bot comments with pass/fail report
        |
        v
Maintainer reviews labels and accepts
        |
        v
Index metadata PR updates generated records
        |
        v
GitHub Pages publishes static /v0 registry JSON
```

This lets anyone propose a package without granting write access to the index.
It also keeps validation evidence, maintainer discussion, and acceptance
history in GitHub.

## Issue Template

The first reference issue form lives at:

```text
.github/ISSUE_TEMPLATE/add-specpackages.yml
```

The form collects:

- one or more public Git repository URLs;
- an optional package path when `specpm.yaml` is not at the repository root;
- free-form maintainer notes;
- acknowledgements that the repositories are public, contain SpecPM package
  files, do not require package execution during validation, and comply with
  index policy.

The template intentionally does not collect enterprise credentials, private
repository access, signing keys, upload tokens, or publish permissions. Public
index submission is reviewable metadata intake, not a remote mutation API.

## Removal Request Template

The first reference removal request form lives at:

```text
.github/ISSUE_TEMPLATE/remove-specpackages.yml
```

The form collects:

- one or more package IDs or `package_id@version` references;
- requested removal scope;
- removal reason;
- rationale and supporting context;
- requester relationship to the package or concern;
- acknowledgements that removal is maintainer-reviewed and does not
  automatically mutate the registry.

Removal requests are review inputs for maintainers. A request may lead to a
pull request that removes or changes entries in `public-index/accepted-packages.yml`
or adjusts public index policy for future generated snapshots. It does not
define automatic deletion, remote yanking mutation, `specpm publish`, package
installation behavior, credential intake, or package content execution.

## Namespace Claim Template

The first reference namespace claim form lives at:

```text
.github/ISSUE_TEMPLATE/claim-namespace.yml
```

The form collects:

- the namespace or package ID prefix being claimed;
- requested claim scope;
- claimant identity;
- public evidence URLs;
- intended namespace use;
- public contact for maintainer follow-up;
- acknowledgements that the claim is maintainer-reviewed and does not
  automatically grant exclusive namespace ownership.

Namespace claim requests are review inputs for maintainers. A request may
provide public evidence for package review, accepted package context, or future
public index policy. It does not define automatic namespace reservation,
authentication, authorization, enterprise namespace governance, `specpm
publish`, remote mutation APIs, package installation behavior, credential
intake, or package content execution.

Review labels, criteria, outcomes, and dispute handling are documented in:

```text
specs/NAMESPACE_CLAIM_POLICY.md
```

## Submission Validation Workflow

The first reference validation workflow lives at:

```text
.github/workflows/package-submission-check.yml
```

The workflow runs for issues labeled `package-submission`.

It:

- parses the `Add SpecPackage(s)` issue form body;
- validates repository URL and package path shape before clone;
- rejects missing URLs, non-HTTPS URLs, credential-bearing URLs, URL fragments,
  absolute package paths, and package path traversal;
- shallow-clones submitted public repositories without submodules;
- runs `specpm validate` on the submitted package path;
- posts a markdown validation report back to the issue;
- fails the check for invalid submissions.

The workflow uses repository read permission and issue write permission for
comments. It does not publish packages, upload archives, mutate registry state,
install submitted packages, or execute package content.

## Public Index Requirements

Initial public submissions should meet these requirements:

- The package repository is publicly accessible.
- The repository URL includes a protocol, usually `https://`.
- The repository contains `specpm.yaml` at the root or at a declared package
  path.
- Referenced `specs/*.spec.yaml` files exist.
- `specpm validate` passes.
- `metadata.id` is valid and stable.
- `metadata.version` is SemVer.
- `metadata.license` is present.
- Package content is data and does not require execution during validation.
- Package content complies with the index policy and code of conduct.

Future public index policy may require a SemVer Git tag, deterministic pack
digest publication, DocC or rendered documentation configuration, or namespace
claim verification.

## Generated Public Registry

After acceptance, maintainers record accepted package sources in:

```text
public-index/accepted-packages.yml
```

The accepted package manifest is the reviewed data source for the generated
public index. It supports repository-local package directories:

```yaml
schemaVersion: 1
packages:
  - path: examples/email_tools
```

It also supports pinned public Git package sources for maintainer-reviewed
promotion from validated submission issues:

```yaml
schemaVersion: 1
packages:
  - repository: https://github.com/example/email-tools.git
    ref: main
    revision: 0123456789abcdef0123456789abcdef01234567
    path: packages/email_tools
```

Remote entries must use public HTTPS repositories, a safe branch or tag ref, an
exact 40-character commit revision, and a relative package path. The generator
checks out the ref without submodules or Git LFS smudging, verifies that the
checkout resolves to the pinned revision, then validates and packs the package
as untrusted data.

Entries are accepted sources that have already passed review. The manifest is
not a remote registry API, not a package upload format, and not a `specpm
publish` replacement. The Pages workflow reads this manifest, validates and
packs the listed packages as untrusted data, and writes generated static `/v0`
metadata.

The index can generate a static registry from explicit local package directories
or from the accepted package manifest:

```bash
specpm public-index generate --manifest public-index/accepted-packages.yml \
  --output <generated-site-dir> \
  --registry <public-registry-url> \
  --json
```

The first generator writes metadata compatible with the read-only remote
registry API contract:

```text
index repo
  generated/
    v0/
      status/index.json
      status/index.html
      packages/index.json
      packages/index.html
      packages/{package_id}/index.json
      packages/{package_id}/index.html
      packages/{package_id}/versions/{version}/index.json
      packages/{package_id}/versions/{version}/index.html
      packages/{package_id}/versions/{version}/{package_id}-{version}.specpm.tgz
      capabilities/{capability_id}/packages/index.json
      capabilities/{capability_id}/packages/index.html
```

GitHub Pages can serve those generated files as the read-only registry API.
The current `specpm remote` commands should be able to read this API without a
custom server. `specpm remote status` and `specpm remote packages` provide the
discovery surface that local SpecGraph and ContextBuilder integrations can use
before requesting a specific package or capability.

The first repository deployment uses the existing DocC GitHub Pages workflow.
That workflow builds the DocC site into `.docc-build`, then runs:

```bash
python -m specpm.cli public-index generate \
  --manifest public-index/accepted-packages.yml \
  --output ./.docc-build \
  --registry https://0al-spec.github.io/SpecPM \
  --json
```

The deployed Pages artifact therefore contains both:

```text
documentation/specpm/
v0/
```

This is still static hosting. The workflow does not accept submissions, publish
through a remote mutation API, install packages, fetch remote archives as a
client, or execute package content. Remote accepted manifest entries are source
checkouts used for static generation only.

The generator validates package directories, creates deterministic
`specpm-tar-gzip-v0` archives, validates generated package/version/capability
payloads against the remote registry contract, and writes static files in
deterministic order.

`index.html` files contain the same JSON body as the adjacent `index.json`
files. They exist so static hosts such as GitHub Pages can serve extensionless
registry endpoints like `/v0/packages/{package_id}` without a custom backend.

This command is still a static metadata generator. It does not accept public
submissions, change issue labels, publish through a remote mutation API,
install packages, fetch remote archives as a client, or execute package
content.

## Local Public Index Service

The repository includes a Docker Compose service for local integration testing:

```bash
make public-index-up
make public-index-smoke
make public-index-down
```

The service:

- generates `.specpm/public-index` from `public-index/accepted-packages.yml`;
- serves the generated static `/v0` tree at `http://localhost:8081` by default;
- exposes `/v0/status`, `/v0/packages`, package lookup, package version lookup,
  and exact capability search metadata;
- can be pointed at another host-visible URL with
  `SPECPM_PUBLIC_INDEX_REGISTRY_URL`;
- can use another accepted package manifest with
  `SPECPM_PUBLIC_INDEX_MANIFEST`;
- can use another host port with `SPECPM_PUBLIC_INDEX_PORT`.

This service is intended for local SpecGraph, ContextBuilder, and manual
ecosystem testing. It is not a remote registry server implementation and does
not add publish, auth, signing, issue mutation, package installation, or
package execution behavior.

## Enterprise Remote Registry

Enterprise users may need a registry that is not issue-based and not public.
That registry may provide:

- private package visibility;
- authentication and authorization;
- organization namespace ownership;
- audit logs;
- retention and deletion policy;
- package signing and trust policy;
- private archive blob storage;
- approval workflows;
- integration with internal Git hosting and CI;
- policy-based yanking or deprecation workflows.

These capabilities are useful, but they are not requirements for the public
index MVP and should not be forced into the static GitHub Pages deployment
model.

## Boundary

The public index and enterprise registry share the read-only remote registry
metadata contract where possible.

The public index submission flow does not define:

- `specpm publish`;
- remote package upload APIs;
- remote yanking mutation APIs;
- authentication;
- package signing;
- namespace governance for enterprises;
- archive download/install/cache behavior;
- semantic search;
- package content execution.

Package content remains untrusted data. A submission can describe reusable
intent. A submission cannot command the index, the registry, or the host.

## Future Work

Future work may add:

- namespace claim label automation;
- enterprise registry reference implementation;
- conformance suites for public index and enterprise registry deployments.
