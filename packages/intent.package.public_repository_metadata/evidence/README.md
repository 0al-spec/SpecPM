# Public Repository Metadata Contract Evidence

This package is an abstract conformance target and intent-level interface
contract.

It does not claim that a concrete implementation exists. It defines the
reviewable boundary that concrete packages can later claim when they expose
static public repository metadata as reusable specification intent.

At the architecture layer, this supports dependency inversion: a graph node can
depend on the abstract repository metadata contract before downstream
governance selects a concrete provider package.

Concrete packages should provide their own evidence, such as repository URLs,
pinned revisions, package manifests, README/LICENSE files, static public API
surfaces, generated harvest snapshots, or maintainer-reviewed documentation.

SpecPM stores this contract as versioned package data. Downstream graph
governance decides semantic relationships, provider selection, and substitution
between this abstract contract and concrete implementation packages.
