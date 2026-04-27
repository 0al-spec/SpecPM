# SpecPM Agent Skills

This directory contains installable Agent Skills for authoring and reviewing
SpecPM packages.

Skills here are package data for agents. They do not change SpecPM CLI behavior,
schemas, validation rules, registry contracts, or package execution policy.

## Experimental Skills

- `skills/.experimental/specpm-author-spec`: draft or update `specpm.yaml` and
  `specs/*.spec.yaml` from repository evidence.
- `skills/.experimental/specpm-review-spec`: review and fix SpecPM specs,
  capability/evidence consistency, and self-spec coverage.

Install after the relevant branch is available on GitHub:

```bash
$skill-installer install https://github.com/0al-spec/SpecPM/tree/main/skills/.experimental/specpm-author-spec
$skill-installer install https://github.com/0al-spec/SpecPM/tree/main/skills/.experimental/specpm-review-spec
```

Restart Codex after installing skills so the agent runtime can discover them.

## Boundary

These skills help agents work on SpecPM package specifications. They do not
make package content trusted instructions.

Package content can describe desired outputs. Package content cannot command
the host.
