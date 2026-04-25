// swift-tools-version:5.9
// This package exists only to generate DocC documentation for the SpecPM
// Python project. The runtime implementation lives under src/specpm.

import PackageDescription

let package = Package(
    name: "SpecPM",
    products: [
        .library(
            name: "SpecPM",
            targets: ["SpecPM"]
        ),
        .executable(
            name: "SpecPM-docs",
            targets: ["SpecPM-docs"]
        ),
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-docc-plugin", from: "1.0.0"),
    ],
    targets: [
        .target(
            name: "SpecPM",
            path: "Sources/SpecPM",
            exclude: []
        ),
        .executableTarget(
            name: "SpecPM-docs",
            path: "Sources/SpecPM-docs",
            exclude: []
        ),
    ]
)
