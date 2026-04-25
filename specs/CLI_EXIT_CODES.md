# SpecPM CLI Exit Code Contract

Status: Draft
Updated: 2026-04-25
Scope: MVP commands

SpecPM uses a small CLI exit code surface so shell scripts, Docker jobs, and
ContextBuilder automation can treat command outcomes consistently.

## General Rules

- `0` means the command completed and produced a usable report.
- `1` means the command completed with an invalid, unresolved, missing, or
  review-required result.
- Parser-level usage errors are handled by `argparse` and may raise its
  standard `SystemExit(2)` path before a SpecPM report exists.
- JSON mode does not change exit code semantics.
- Warnings do not imply failure unless the command-specific result status is
  invalid.

## Command Outcomes

| Command | Exit `0` | Exit `1` |
| --- | --- | --- |
| `specpm validate` | validation status is `valid` or `warning_only` | validation status is `invalid` |
| `specpm inspect` | package validation status is `valid` or `warning_only` | package validation status is `invalid` |
| `specpm pack` | pack status is `packed` | pack status is `invalid` |
| `specpm index` | index status is `indexed` or `unchanged` | index status is `invalid` |
| `specpm search` | search status is `ok`, including empty or missing local index results | search status is `invalid` |
| `specpm add` | add status is `added` or `unchanged` | add status is `invalid` or `ambiguous` |
| `specpm yank` | yank status is `yanked` or `unchanged` | yank status is `invalid` |
| `specpm unyank` | unyank status is `unyanked` or `unchanged` | unyank status is `invalid` |
| `specpm diff` | diff status is `ok` | diff status is `invalid` |
| `specpm inbox list` | always returns a list report, even when empty | reserved for future unrecoverable command errors |
| `specpm inbox inspect` | bundle is found | bundle is missing |
| `specpm remote package` | remote client status is `ok` | remote client status is `invalid` or `not_found` |
| `specpm remote version` | remote client status is `ok` | remote client status is `invalid` or `not_found` |
| `specpm remote search` | remote client status is `ok` | remote client status is `invalid` or `not_found` |

## Automation Guidance

Automation should parse JSON output first and use exit codes as a coarse gate:

- Treat `0` with warnings as reviewable success.
- Treat `1` with a JSON report as a handled SpecPM outcome.
- Treat parser `2` or process-level failures as invocation or runtime errors,
  not package validation outcomes.
