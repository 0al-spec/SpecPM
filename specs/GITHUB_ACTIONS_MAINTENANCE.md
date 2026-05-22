# GitHub Actions Maintenance Policy

Status: Draft
Updated: 2026-05-22
Scope: SpecPM repository GitHub Actions workflow references and runtime drift

## Purpose

This policy defines how SpecPM keeps GitHub Actions workflows current enough to
avoid platform runtime deprecations while preserving stable, reviewable
automation.

The policy covers repository workflow references under `.github/workflows/`.
It does not define SpecPM package versioning, registry API versioning, release
publishing, or third-party deployment credentials.

## Maintained Action Set

Official `actions/*` references used by SpecPM workflows should stay on
maintained action major versions that support GitHub's current JavaScript
runtime generation.

The current guard covers these official actions:

| Action | Minimum major |
| --- | ---: |
| `actions/checkout` | `v6` |
| `actions/setup-python` | `v6` |
| `actions/upload-artifact` | `v7` |
| `actions/download-artifact` | `v8` |
| `actions/upload-pages-artifact` | `v5` |
| `actions/deploy-pages` | `v5` |
| `actions/github-script` | `v9` |

SpecPM may keep third-party actions, such as Xcode setup helpers, outside this
table when the observed deprecation or migration notice is specific to official
`actions/*` references. Third-party action upgrades should be reviewed
separately because their release, trust, and compatibility profiles differ.

## Reference Style

SpecPM workflows should use official action major tags, for example
`actions/checkout@v6`, rather than older runtime generations. Major tags keep
workflow files readable and allow official action maintainers to ship compatible
minor and patch fixes within the selected major line.

If a workflow uses a quoted YAML value or a full semantic version such as
`"actions/checkout@v6.0.2"`, the maintenance guard must still extract and check
the major version. The guard should not fail merely because a currently unused
action from the maintained set is absent; it should fail only when a referenced
maintained action is below its required major.

## Update Trigger

Maintainers should update the maintained action table when one of these is true:

- GitHub Actions logs emit a runtime deprecation warning for a referenced
  action.
- GitHub announces a forced JavaScript runtime change that affects one of the
  referenced actions.
- A workflow adds a new official `actions/*` dependency that belongs in the
  repository-wide guard.
- A maintained workflow removes an action from active use.

When a new action is added to the guard, update both this policy and the
workflow guard test in `tests/test_core.py`.

## Verification

Pull requests that update workflow actions should run:

```bash
.venv/bin/python -m pytest tests/test_core.py::test_github_workflows_use_node24_action_generations -q
make lint
make format-check
make test
```

After merge, maintainers should inspect the relevant `main` workflow logs for
the deprecation text that motivated the change. For Node runtime migrations,
the expected post-merge state is no match for:

```text
Node.js 20 actions are deprecated
```

## `pull_request_target` Boundary

Workflows triggered by `pull_request_target` run with the workflow definition
from the base branch. A pull request that edits such a workflow cannot fully
prove that workflow's own updated action references until after merge.

For these workflows, PR validation should still parse and test the proposed
YAML, but the final runtime confirmation is the first `main` run after merge.
PR notes should call out this boundary when an old warning appears only because
GitHub executed the base-branch workflow definition.

## Boundaries

This policy does not:

- require exact SHA pinning for official GitHub-maintained actions;
- change workflow permissions or secret handling;
- approve third-party action upgrades automatically;
- replace review of workflow behavior, shell commands, or deployment safety;
- treat skipped deploy jobs on pull requests as production deploy evidence.
