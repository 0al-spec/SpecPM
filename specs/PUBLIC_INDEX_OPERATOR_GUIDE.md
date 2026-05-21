# Public Index Operator Guide

Status: Public alpha operator guide.
Updated: 2026-05-21
Scope: public index package submission maintainer review

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

The optional `.github/workflows/package-submission-triage.yml` workflow prepares
these labels and applies `package:under-review` when no package review status is
present. It does not apply terminal labels.

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
- The validated revision from the CI report is pinned in the accepted manifest
  entry.
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

Maintainers can ask the validation helper to render a candidate snippet:

```bash
python scripts/validate_index_submission.py \
  --issue-body-file submission-issue.md \
  --json-output submission-report.json \
  --manifest-candidate-output accepted-manifest-candidate.yml
```

The helper output is review input. It is not committed automatically and does
not edit `public-index/accepted-packages.yml`.

After maintainer review, a second helper can prepare the accepted-manifest
change on a review branch:

```bash
git switch -c accept-package-issue-123
python scripts/prepare_accepted_manifest_pr.py \
  --submission-report submission-report.json \
  --manifest public-index/accepted-packages.yml \
  --issue-url https://github.com/0al-spec/SpecPM/issues/123 \
  --apply \
  --json-output accepted-manifest-pr-report.json \
  --pr-body-output accepted-manifest-pr.md
```

This appends only new exact source records to
`public-index/accepted-packages.yml`, skips exact duplicate sources, and writes a
draft pull request body with the submission issue, package identities, source
refs, and exact pinned revisions. Omitting `--apply` performs a dry-run report
without editing the manifest.

The generated pull request body is a draft. Maintainers must still run the
public-index generation checks, keep the PR reviewable, and replace pending
validation notes with the exact commands they ran before merge.

## Boundaries

This operator flow does not add `specpm publish`, upload endpoints, remote
mutation APIs, package installation, archive acquisition as a client, package
execution, automatic namespace ownership, package signing, or enterprise access
control.

Automation may validate a submission, prepare labels, comment with review
evidence, render a candidate manifest snippet, and prepare an accepted-manifest
pull request draft.

Automation must not decide acceptance. It must not edit
`public-index/accepted-packages.yml` without a reviewed pull request.
