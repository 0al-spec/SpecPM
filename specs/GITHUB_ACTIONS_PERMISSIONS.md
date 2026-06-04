# GitHub Actions Permissions and Secret Boundary

Status: Draft
Updated: 2026-05-23
Scope: SpecPM repository GitHub Actions permissions, secrets, and deploy trust boundaries

## Purpose

This policy defines the least-privilege boundary for SpecPM GitHub Actions
workflows. It complements `specs/GITHUB_ACTIONS_MAINTENANCE.md`, which tracks
action runtime-major maintenance.

The policy covers workflow files under `.github/workflows/`, their declared
`GITHUB_TOKEN` permissions, their repository or environment secret access, and
the review boundary for workflows that run with base-repository trust.

It does not add secrets, rotate credentials, approve package submissions, grant
namespace ownership, publish packages, or change registry runtime behavior.

## Principles

- Workflows should declare only the `GITHUB_TOKEN` scopes needed for their job.
- Deployment credentials must be available only to workflows that deploy or
  explicitly check deployment connectivity.
- Issue automation may comment, label, or summarize review state, but must not
  accept packages, grant namespace ownership, edit accepted package manifests,
  generate production registry metadata, or publish packages.
- Pull request checks are build and policy evidence, not production deploy
  evidence.
- `pull_request_target` workflows must not execute pull request head code while
  repository secrets or write scopes are available.

GitHub Actions treats unspecified permissions as `none` once a workflow or job
declares any permission. GitHub also does not pass repository secrets to forked
pull request workflows, except for `GITHUB_TOKEN`. SpecPM's policy still treats
all secrets as privileged and keeps explicit workflow boundaries around them.

## Workflow Permission Matrix

| Workflow | Trigger surface | Token boundary | Secret boundary | Allowed effect |
| --- | --- | --- | --- | --- |
| `.github/workflows/ci.yml` | `push`, `pull_request` | `contents: read`. | No repository or environment secrets. | Install, lint, format-check, test, and build Docker image. |
| `.github/workflows/docs.yml` `build` | `push`, `pull_request`, `workflow_dispatch` | `contents: read` at workflow level. | No repository or environment secrets. | Build DocC, generated `/v0` metadata, landing page, viewer, and static artifact. |
| `.github/workflows/docs.yml` `deploy` | `push` to `main` | `contents: read`, `pages: write`, `id-token: write` at job level. | No FTP secrets. | Deploy the built artifact to GitHub Pages. |
| `.github/workflows/docs.yml` `deploy-static-host` | `push` to `main`, `workflow_dispatch` | Inherits workflow-level `contents: read`. | May read `FTP_HOST`, `FTP_PORT`, `FTP_USER`, `FTP_PASS`, and `FTP_REMOTE_ROOT` from the `FTP` environment. | Upload the already-built static artifact to `https://SpecPM.dev` over SFTP. |
| `.github/workflows/deploy-connection-check.yml` | `pull_request_target` for deployment workflow paths | `contents: read`. | May read `FTP_HOST`, `FTP_PORT`, `FTP_USER`, `FTP_PASS`, and `FTP_REMOTE_ROOT` from the `FTP` environment. | Check that the SFTP target is reachable without uploading files. |
| `.github/workflows/package-submission-check.yml` | `issues` labeled `package-submission` | `contents: read`, `issues: write`. | No repository or environment secrets. | Validate public package submission text and post/update one validation comment. |
| `.github/workflows/package-submission-triage.yml` | `issues` labeled `package-submission` | `contents: read`, `issues: write`. | No repository or environment secrets. | Prepare review labels and an idempotent maintainer guidance comment. |
| `.github/workflows/producer-bundle-preflight.yml` | `pull_request` | `contents: read`. | No repository or environment secrets. | If the pull request body includes producer bundle evidence blocks, run consumer-side `specpm producer-bundle preflight`; otherwise report a skip. |
| `.github/workflows/namespace-claim-triage.yml` | `issues` labeled `namespace-claim` | `contents: read`, `issues: write`. | No repository or environment secrets. | Prepare namespace review labels and an idempotent policy comment. |
| `.github/workflows/namespace-claim-decision-report.yml` | `issues` labeled/unlabeled `namespace-claim` | `contents: read`, `issues: write`. | No repository or environment secrets. | Report maintainer-applied namespace decision labels. |
| `.github/workflows/namespace-claim-decision-summary.yml` | `workflow_dispatch`, schedule | `contents: read`, `issues: read`. | No repository or environment secrets. | Write read-only namespace decision summaries and upload workflow artifacts. |

## Secret Boundary

The only non-`GITHUB_TOKEN` secrets currently allowed in SpecPM workflows are:

- `FTP_HOST`
- `FTP_PORT`
- `FTP_USER`
- `FTP_PASS`
- `FTP_REMOTE_ROOT`

These secrets are scoped to the GitHub Environment named `FTP` and are used only
by:

- `.github/workflows/docs.yml`, job `deploy-static-host`;
- `.github/workflows/deploy-connection-check.yml`, job
  `deploy-connection-check`.

Package submission, producer bundle preflight, and namespace claim workflows
must not read repository or environment secrets. They process public GitHub
Issue or pull request content and may use `GITHUB_TOKEN` only for the documented
comment, label, search, artifact, and read-only checkout operations.

## `pull_request_target` Review Rules

`pull_request_target` runs in the context of the base repository. It is useful
when a workflow needs base-repository trust for comments, labels, or controlled
connectivity checks, but it is unsafe if the job checks out or executes pull
request head code while privileged token scopes or secrets are available.

SpecPM currently allows `pull_request_target` only for
`.github/workflows/deploy-connection-check.yml`. That workflow must keep all of
these guards:

- run only for deployment workflow path changes;
- require `github.event.pull_request.head.repo.full_name == github.repository`;
- check out `github.event.pull_request.base.sha`, not the pull request head;
- use `contents: read`;
- perform a read-only SFTP directory listing, not an upload;
- avoid running scripts or shell fragments from the pull request branch.

Any new `pull_request_target` workflow or expansion of this one must update this
policy and its regression tests in the same pull request.

## Deploy Trust Boundary

Pull request checks can prove that proposed source changes parse, build, and
satisfy policy tests. They cannot prove production deployment for GitHub Pages
or SpecPM.dev because deployment jobs intentionally run only after merge or
manual dispatch from trusted workflow definitions.

Deployment evidence is:

- GitHub Pages: the first successful `main` documentation deploy run after
  merge;
- SpecPM.dev: the first successful `main` or approved `workflow_dispatch`
  `Deploy SpecPM.dev static host` job after merge;
- deploy connection check: evidence that the base-branch trusted workflow can
  authenticate to the configured SFTP root and list it, not evidence that a
  candidate pull request can upload or publish content.

The SpecPM.dev upload job must summarize the static artifact before it connects
to SFTP, including file count and byte size. Its upload step must keep an
explicit wall-clock timeout and emit transfer diagnostics that are safe for logs:
command tracing for `lftp` commands, recent transfer log entries, and elapsed
seconds. These diagnostics are deployment evidence, not secret disclosure; logs
must not print passwords, private keys, or raw credential values.

When a pull request changes workflow permissions, secrets, deployment commands,
or `pull_request_target` behavior, reviewers should treat green PR checks as
pre-merge evidence only and verify the first post-merge `main` run.

## Review Checklist

- Does the workflow need each requested `GITHUB_TOKEN` scope?
- Does any job gain access to `FTP_*` secrets?
- Does any privileged workflow read issue bodies, PR head files, generated
  artifacts, or shell commands from untrusted input?
- Does any `pull_request_target` job check out or execute pull request head
  content?
- Does the PR clearly distinguish PR evidence from post-merge deploy evidence?

## Verification

Pull requests that change workflow permissions, secrets, deployment commands, or
this policy should run:

```bash
.venv/bin/python -m pytest tests/test_core.py::test_github_actions_permissions_and_secrets_boundary_is_documented -q
make lint
make format-check
make test
```

After merge, maintainers should inspect the `main` workflow runs that exercise
the changed trust boundary.
