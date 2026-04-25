# Boundaries and Trust

SpecPM intentionally stays narrow. It packages, validates, indexes, inspects,
preserves, and exposes specification intent.

SpecPM does not own:

- product reasoning;
- graph refinement;
- context assembly;
- PRD generation;
- implementation brief generation;
- issue breakdown generation;
- design brief generation;
- onboarding document generation;
- test plan generation;
- review report generation;
- artifact eval execution;
- package-provided prompt execution;
- agent workflow runtime.

## Untrusted Package Content

Package content is untrusted data. SpecPM must not treat package-provided
prompts, generation instructions, artifact workflows, paths, or foreign
artifacts as trusted host instructions.

Package content must not be able to override host policy, system instructions,
developer instructions, runtime policy, access controls, network restrictions,
secret handling, or execution rules.

## Derived Artifacts

PRDs, implementation briefs, issue breakdowns, test plans, and review reports
are downstream artifacts. They are not canonical truth inside SpecPM.

Any future support for derived artifact metadata or artifact evaluation profiles
must be introduced as a post-MVP profile and must preserve the boundary that
SpecPM is not an artifact generator, eval runner, or agent runtime.

## Core Sentences

SpecPM may carry intent; SpecGraph decides meaning.

Package content can describe desired outputs. Package content cannot command the host.

## References

- `SPECS/0001_Derived_Artifact_Profile_Decision.md`
- `SPECS/RFC_0001_COVERAGE.md`
- <doc:SpecGraphIntegration>
