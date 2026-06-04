# GitHub Actions Permissions

SpecPM keeps GitHub Actions token scopes and secret access narrow enough for the
current public alpha workflow model.

## Scope

The permissions boundary covers repository workflows under `.github/workflows/`,
their declared `GITHUB_TOKEN` permissions, their secret usage, and the review
rules for workflows that run with base-repository trust.

It complements <doc:GitHubActionsMaintenance>, which tracks official action
runtime-major updates.

## Current Boundary

Most workflows either use read-only repository access or issue-scoped write
access for comments and labels. The documentation deploy workflow has a
separate GitHub Pages deploy job with `pages: write` and `id-token: write`.
The producer bundle preflight workflow is a read-only pull request check: it
only runs consumer-side evidence validation when a pull request body includes
producer bundle evidence blocks.

The only deployment secrets currently allowed are `FTP_HOST`, `FTP_PORT`,
`FTP_USER`, `FTP_PASS`, and `FTP_REMOTE_ROOT`. They are scoped to the `FTP`
environment and are used only by the SpecPM.dev static host deployment and the
read-only SFTP connection check.

## `pull_request_target`

SpecPM permits `pull_request_target` only for the SFTP connection check. That
workflow checks out the base commit, restricts execution to same-repository pull
requests, and performs a directory listing rather than an upload.

Pull request checks are pre-merge evidence. GitHub Pages and SpecPM.dev
deployment evidence comes from the first trusted `main` run after merge.

The SpecPM.dev upload job also records safe deployment diagnostics: static
artifact file count, byte size, `lftp` command tracing, recent transfer log
entries, and elapsed upload seconds. These logs help distinguish a slow SFTP
upload from a stuck upload without exposing FTP secrets.

## Source Contract

The detailed permissions and secret boundary is maintained in
`specs/GITHUB_ACTIONS_PERMISSIONS.md`.
