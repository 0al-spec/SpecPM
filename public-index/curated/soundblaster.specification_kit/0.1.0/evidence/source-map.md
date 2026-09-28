# SpecificationKit: pinned source evidence

This SpecPM description is curated from public files in the upstream repository
at commit `60850e758d020ceacc1cfe83801c09b4749eab6f`. The README describes
SpecificationKit 4.0.0. `0.1.0` in this SpecPM package is the initial
catalog-record version, not an upstream release number. Its manifest declares
a SpecificationCore dependency beginning at 1.0.1; that dependency bound is
reported as checked in the pinned manifest and is not inferred from a different
checkout.

| Claim area | Pinned source evidence |
| --- | --- |
| Product boundary and feature overview | [README.md](https://github.com/SoundBlaster/SpecificationKit/blob/60850e758d020ceacc1cfe83801c09b4749eab6f/README.md) |
| SwiftPM product, supported platforms, and declared dependencies | [Package.swift](https://github.com/SoundBlaster/SpecificationKit/blob/60850e758d020ceacc1cfe83801c09b4749eab6f/Package.swift) |
| SwiftUI observation wrappers | [ObservedSatisfies.swift](https://github.com/SoundBlaster/SpecificationKit/blob/60850e758d020ceacc1cfe83801c09b4749eab6f/Sources/SpecificationKit/Wrappers/ObservedSatisfies.swift), [ObservedDecides.swift](https://github.com/SoundBlaster/SpecificationKit/blob/60850e758d020ceacc1cfe83801c09b4749eab6f/Sources/SpecificationKit/Wrappers/ObservedDecides.swift) |
| Provider and product-rule surfaces | [Providers](https://github.com/SoundBlaster/SpecificationKit/tree/60850e758d020ceacc1cfe83801c09b4749eab6f/Sources/SpecificationKit/Providers), [Specs](https://github.com/SoundBlaster/SpecificationKit/tree/60850e758d020ceacc1cfe83801c09b4749eab6f/Sources/SpecificationKit/Specs) |
| License | [LICENSE](https://github.com/SoundBlaster/SpecificationKit/blob/60850e758d020ceacc1cfe83801c09b4749eab6f/LICENSE) |

Provider I/O is described conditionally because the package contains provider
types with different effects. No provider was configured or invoked for this
catalog record. No package code, build scripts, package manager commands, or
tests were executed to prepare this evidence map.
