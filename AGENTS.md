# SpecPM Agent Instructions

## 0AL Local Ops Logging

For cross-repo observations, coordination tasks, blockers, or handoffs, write a
local ops entry through the `.0al` logging CLI when it is available:

```bash
../.0al/scripts/0al-log.py --project specpm --kind note --owner unclassified \
  --title "<short title>" \
  --text "<what happened, what is needed, and any suggested next action>"
```

Use `.0al` only for coordination. Canonical SpecPM changes belong in this
repository. Do not edit `../.0al/tasks.md` or `../.0al/decisions.md` directly unless
the user explicitly asks for tracker maintenance, and never write secrets,
credentials, private keys, or machine-local tokens to `.0al`.

## GitHub Pull Requests

When a task creates one or more commits, push the branch and create or update a
GitHub pull request before the final response, unless the user explicitly asks
not to create a PR.

The final response should include the PR URL and the validation commands that
were actually run.

## Deploy-First Workflow

For registry, public-index, Docker, or deployment-related tasks, prefer the
live Docker service as the first integration surface.

After changing registry generation, accepted package sources, Compose/Make
deployment targets, or remote registry contracts, run the local deploy gate when
practical:

```bash
make dev-reload
make dev-smoke
```

If the task affects GitHub Pages output or public `/v0` metadata, also run or
explicitly discuss:

```bash
make pages-smoke
```

If a Pages smoke check cannot reflect the PR before merge, state that clearly
in the final response and rely on CI Pages build checks until deployment.
