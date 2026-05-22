# GitHub Actions Maintenance

SpecPM keeps repository workflows on maintained GitHub Actions runtime
generations so CI and deployment checks do not drift into platform deprecation
warnings.

## Maintained Official Actions

SpecPM tracks official `actions/*` references used by the repository and keeps
them on current major versions. The current guarded set includes checkout,
Python setup, artifact upload/download, Pages artifact/deploy, and
`github-script`.

The repository guard lives in `tests/test_core.py` and checks the major version
of referenced official actions. It accepts quoted YAML values and semantic
version refs, but it only enforces minimum versions for actions that are
actually present in the workflows.

## Update Flow

Update workflow action majors when GitHub logs a runtime deprecation warning,
announces a forced JavaScript runtime migration, or when a new official
`actions/*` reference is added to a workflow.

Action-maintenance pull requests should run:

```bash
make lint
make format-check
make test
```

After merge, inspect the `main` workflow logs for the deprecation warning that
motivated the update.

## `pull_request_target`

`pull_request_target` workflows execute the workflow definition from the base
branch. A PR can validate the proposed YAML, but it cannot fully prove that the
changed workflow's own action references are warning-free until the first
post-merge `main` run.

## Source Contract

The detailed maintenance policy is maintained in
`specs/GITHUB_ACTIONS_MAINTENANCE.md`.
