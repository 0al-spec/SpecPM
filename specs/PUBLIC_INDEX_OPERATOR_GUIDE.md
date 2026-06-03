# Public Index Operator Guide

Status: Public alpha operator guide.
Updated: 2026-05-31
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

## Label Transition Policy

The label state is review evidence, not registry state. The accepted manifest
and generated static registry remain the source of public package visibility.

- Automation may apply `package:under-review` and keep the review labels
  available on the repository.
- `package:validated` means a candidate is reviewable. It does not mean the
  package is accepted into the public index.
- `package:needs-fix` should include an actionable issue comment or validation
  report section that explains the requested change.
- `package:blocked` should include the policy, ownership, safety, or repository
  access question that prevents acceptance.
- `package:duplicate` should link the already accepted source or the open
  accepted-manifest pull request that covers the same `package_id@version`.
- `package:accepted` should link the reviewed accepted-manifest pull request
  and, when available, the generated registry evidence for the accepted
  package version.
- A package-submission issue should have at most one terminal label:
  `package:accepted`, `package:rejected`, `package:blocked`, or
  `package:duplicate`.

Changing a terminal label after new evidence appears is a maintainer decision.
The new comment should explain the reason and link the replacement pull request,
validation report, or registry evidence.

## Operator Flow

Maintainers should use this sequence for ordinary public package intake:

1. Confirm the issue has `package-submission` and the triage workflow left it in
   `package:under-review`.
2. Read the latest validation report and confirm that the submitted repository,
   package path, `package_id@version`, and pinned revision are the expected
   candidate.
3. Choose the next review state: `package:needs-fix`, `package:blocked`,
   `package:duplicate`, or proceed toward an accepted-manifest pull request.
4. Run the accepted-manifest helper in dry-run mode first and review the source
   records it would append.
5. Apply the helper on a review branch only after maintainer review agrees with
   the candidate records.
6. Run the public-index generation checks and record the commands in the pull
   request body.
7. After merge, apply `package:accepted` and link the issue, reviewed pull
   request, and generated static registry evidence.

This flow intentionally keeps issue validation, maintainer review, manifest
changes, and generated registry publication as separate steps.

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
- The accepted manifest pull request references the source submission issue.
- The accepted manifest pull request changes only
  `public-index/accepted-packages.yml` or directly related policy/docs/test
  files needed for the acceptance.
- The accepted manifest pull request shows generated registry checks passing
  and records the commands that were actually run.

## Producer-Backed Candidate Bundle Intake

When a public-index proposal relies on a SpecHarvester or other producer
candidate bundle, maintainers should treat the bundle as review evidence and
apply the normal acceptance checklist above. Producer evidence does not replace
SpecPM validation, accepted-source review, namespace review, or the maintainer
decision. The producer bundle is not registry authority.

The proposal or accepted-manifest pull request should include or link:

- `specpm.yaml` and referenced `specs/*.spec.yaml` files from the candidate
  bundle;
- `producer-receipt.json`;
- `validation-report.json`;
- `diagnostics.json`;
- producer preflight report or command output;
- static viewer output or reviewer-accessible preview, when available;
- the proposed accepted-source diff or manifest entry;
- the issue, pull request, or maintainer note that records the final
  acceptance decision.

Before accepting the producer-backed entry, maintainers should verify:

- the candidate package validates under a supported SpecPM package API version;
- the receipt uses `apiVersion: specpm.receipts/v0`,
  `kind: SpecPMProducerReceipt`, and
  `receiptProfile: generated_spec_package_v0`;
- `producer-receipt.json` is not listed in `outputs[]`;
- receipt output digests match the candidate bundle files;
- `validation.reportDigest` matches `validation-report.json`;
- `diagnostics.digest` matches `diagnostics.json`;
- `privacy.secretsIncluded` is `false` for public handoff;
- `humanReview.requiredFor` includes `public_index_acceptance`;
- `humanReview.status` is still treated as review-gated until the maintainer
  records acceptance outside the producer receipt;
- diagnostics are `clean` or warning-only with maintainer-reviewed rationale;
- no private local paths, tokens, credentials, private keys, or confidential
  source bodies are included in public evidence;
- generated claims are reviewed against package evidence and are not trusted
  solely because the producer emitted them.

Reject or request regeneration when required producer files are missing, digest
checks disagree, diagnostics are `failed`, public handoff includes secrets, the
candidate identity disagrees across artifacts, or the proposal asks SpecPM to
execute producer tools, prompts, analyzers, package scripts, or package
content. Any override must be recorded in the accepted-manifest pull request,
submission issue, or future acceptance decision record, not by editing the
producer receipt.

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

## Helper Contract

The helper tools produce review inputs for maintainers. They are intentionally
not registry publication authority.

- `scripts/validate_index_submission.py` may render validation evidence and a
  candidate accepted-manifest snippet.
- `scripts/prepare_accepted_manifest_pr.py` may prepare a manifest diff and a
  draft pull request body from a valid submission report.
- Dry-run mode is the default review posture; maintainers should inspect it
  before using `--apply`.
- Helper output must keep the issue URL, repository URL, source `ref`, exact
  `revision`, package path, and package identities visible for review.
- Helpers must not apply terminal labels, decide acceptance, push branches,
  open pull requests, merge pull requests, grant namespace ownership, execute
  package content, or publish a package.
- Helpers must not publish a package as a side effect of validation, dry-run, or
  manifest preparation.

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
