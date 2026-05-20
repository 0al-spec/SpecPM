# Public Index Operator Guide

Status: Public alpha operator guide.

This guide defines the maintainer workflow for accepting public
`SpecPackage` submissions into the generated SpecPM public index. It complements
`specs/INDEX_SUBMISSION_FLOW.md`, which defines the submitter-facing intake and
static registry boundary.

## Review Labels

Package submission issues use the root label `package-submission`. Maintainers
may use these status labels during review:

- `package:under-review` means the submission is ready for maintainer review.
- `package:needs-fix` means validation or policy review found fixable issues.
- `package:validated` means automated validation passed and the issue has a
  reviewable accepted-manifest candidate.
- `package:accepted` means maintainers accepted the package version through a
  reviewed pull request.
- `package:rejected` means maintainers declined the submission for the public
  index.
- `package:blocked` means review is blocked by policy, ownership, safety, or
  repository-access questions.
- `package:duplicate` means the submitted `package_id@version` is already
  represented by an accepted source or an equivalent open review.

Only maintainers apply terminal labels such as `package:accepted`,
`package:rejected`, `package:blocked`, or `package:duplicate`.

## Acceptance Checklist

Before adding an entry to `public-index/accepted-packages.yml`, maintainers
should verify:

- The issue has the `package-submission` label.
- The submitted repository URL is public HTTPS Git, has no embedded
  credentials, and points to reviewable source.
- The package path is relative, does not escape the repository root, and
  contains `specpm.yaml` plus referenced `specs/*.spec.yaml` files.
- The validation report status is `valid`.
- Any validation warnings are understood and acceptable for public alpha.
- The candidate package identity is the expected `package_id@version`.
- The exact submitted revision is pinned in the accepted manifest entry.
- Re-publishing the same `package_id@version` does not overwrite different
  content.
- Namespace or ownership questions have explicit maintainer review evidence
  when they matter for acceptance.
- The accepted manifest pull request shows generated registry checks passing.

## Accepted Manifest PR

The accepted manifest pull request should add one immutable source record per
accepted package version:

```yaml
- repository: https://github.com/example/package-repo.git
  ref: main
  revision: 0123456789abcdef0123456789abcdef01234567
  path: .
```

The `revision` is the root of trust for that source record. A mutable `ref` is
allowed only as a human-readable source label; the generator must verify that
the checkout resolves to the pinned revision.

## Boundaries

This operator flow does not add `specpm publish`, upload endpoints, remote
mutation APIs, package installation, archive acquisition as a client, package
execution, automatic namespace ownership, package signing, or enterprise access
control.

Automation may validate a submission, prepare labels, comment with review
evidence, and render a candidate manifest snippet.

Automation must not decide acceptance. It must not edit
`public-index/accepted-packages.yml` without a reviewed pull request.
