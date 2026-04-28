# SpecPM Agent Instructions

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
