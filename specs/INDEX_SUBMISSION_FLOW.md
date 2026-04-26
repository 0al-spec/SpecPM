# SpecPM Index Submission Flow

Status: Draft
Updated: 2026-04-26
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

After acceptance, the index can generate a static registry with:

```bash
specpm public-index generate <package-dir>... \
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
custom server.

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

- GitHub Pages deployment for the public index;
- package removal request workflow;
- namespace claim workflow;
- enterprise registry reference implementation;
- conformance suites for public index and enterprise registry deployments.
