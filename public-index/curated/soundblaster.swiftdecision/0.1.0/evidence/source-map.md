# SwiftDecision: pinned source evidence

This SpecPM description is curated from public files in the upstream repository
at commit `de28736b2d022aa2e4f31f8fec870eab459d0d93`. The upstream README
identifies package version 0.5.0. `0.1.0` in this SpecPM package is the initial
catalog-record version, not an upstream release number.

| Claim area | Pinned source evidence |
| --- | --- |
| Product purpose, decision kinds, policy outcomes, backend choices, platform requirements, and limitations | [README.md](https://github.com/SoundBlaster/SwiftDecision/blob/de28736b2d022aa2e4f31f8fec870eab459d0d93/README.md) |
| SwiftPM product, dependencies, platform declarations, and optional MLX trait | [Package.swift](https://github.com/SoundBlaster/SwiftDecision/blob/de28736b2d022aa2e4f31f8fec870eab459d0d93/Package.swift) |
| Public request, backend, prediction, and policy interfaces | [DecisionAPI.swift](https://github.com/SoundBlaster/SwiftDecision/blob/de28736b2d022aa2e4f31f8fec870eab459d0d93/Sources/SwiftDecision/DecisionAPI.swift) |
| Decision engine and typed output APIs | [DecisionAPI.swift](https://github.com/SoundBlaster/SwiftDecision/blob/de28736b2d022aa2e4f31f8fec870eab459d0d93/Sources/SwiftDecision/DecisionAPI.swift) |
| Optional local Laya/MLX backend | [LayaMLXBackend.swift](https://github.com/SoundBlaster/SwiftDecision/blob/de28736b2d022aa2e4f31f8fec870eab459d0d93/Sources/SwiftDecision/LayaMLXBackend.swift) |
| Trace data boundaries and ordering | [Decision tracing guide](https://github.com/SoundBlaster/SwiftDecision/blob/de28736b2d022aa2e4f31f8fec870eab459d0d93/Documentation/DecisionTracing.md) |
| License and model-weight notice | [LICENSE](https://github.com/SoundBlaster/SwiftDecision/blob/de28736b2d022aa2e4f31f8fec870eab459d0d93/LICENSE), [NOTICE](https://github.com/SoundBlaster/SwiftDecision/blob/de28736b2d022aa2e4f31f8fec870eab459d0d93/NOTICE) |

The pinned package manifest makes SpecificationCore a runtime dependency and
declares MLX and Swift Transformers for the optional `MLX` trait. The backend
is invoked through a protocol; the configured implementation determines its
transport effects. No package code, build scripts, package manager commands,
or tests were executed to prepare this evidence map.
