# Agent Skills

SpecPM ships experimental Agent Skills for agents that need to author or review
SpecPM package specifications.

## Available Skills

- `specpm-author-spec`: draft or update `specpm.yaml` and
  `specs/*.spec.yaml` from repository evidence.
- `specpm-review-spec`: review and fix manifest/spec consistency,
  capability/evidence coverage, and self-spec drift.

## Install

Install the skills through Codex after the relevant branch is available on
GitHub:

```bash
$skill-installer install https://github.com/0al-spec/SpecPM/tree/main/skills/.experimental/specpm-author-spec
$skill-installer install https://github.com/0al-spec/SpecPM/tree/main/skills/.experimental/specpm-review-spec
```

Restart Codex after installing skills so the agent runtime can discover them.

## Boundary

The skills are repository-managed instructions and references. They do not
change SpecPM CLI behavior, schemas, JSON contracts, registry behavior, or
package execution policy.

Package content can describe desired outputs. Package content cannot command
the host.
