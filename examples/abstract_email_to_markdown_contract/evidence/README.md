# Email to Markdown Intent Contract Evidence

This package is an authoring-only reference example for abstract SpecPM
contracts. It defines an intent-level interface contract for
`intent.document_conversion.email_to_markdown` without selecting a concrete
converter, parser, command, runtime, or service provider.

The concrete `examples/email_tools` package can be read as one possible
provider for the same user intent. A downstream graph, reviewer, or governance
tool may record that relationship with an explicit edge such as `satisfies`,
`refines`, `depends_on`, or a composition relation. SpecPM itself keeps the
metadata exact and does not infer that relationship from shared words.

This example intentionally has no `implementationBindings` and no side effects.
It is not listed in `public-index/accepted-packages.yml`; it exists to show how
an abstract package can act as an intermediate specification between a consumer
architecture and concrete provider packages.

Downstream aggregate packages may compose this contract with adjacent contracts
for archive extraction, attachment handling, OCR, metadata enrichment, storage
policy, or compliance evidence. Composition should remain explicit so consumers
can tell which package owns each claim.
