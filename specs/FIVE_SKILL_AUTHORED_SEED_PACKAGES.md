# Five Skill-Authored Seed Packages

This catalog submission curates the five P56-T4 candidates authored with the
SpecHarvester `specpm-author-candidate` skill by GPT 5.6 Luna, medium reasoning.
It reuses that new-skill work, not the older generic-intent harvest, and does not
claim a new generation run. Originals and producer receipts remain unchanged.

| SpecPackage | Version | Discovery purpose |
| --- | --- | --- |
| `rtk.shell_output_proxy` | `0.1.0` | Reduce shell-output context for coding agents; rewrite supported commands |
| `openai.codex` | `0.1.0` | Local coding-agent turns and TypeScript/Python embedding |
| `axios.http_client` | `1.19.0` | Browser/Node.js HTTP requests, configuration and cancellation |
| `bitcoin.core.fullnode` | `0.1.0` | Full-node validation, authenticated RPC and optional wallet/GUI |
| `n8n.platform` | `0.1.0` | Workflow automation and snapshot-specific Instance AI tools |

## Acceptance Boundary

Merging the catalog PR is the SpecPM maintainer acceptance action. Removing
`preview_only` in these separate curated copies proposes that action; it is not
upstream author approval. BoundarySpecs remain `draft`: catalog availability is
not a runtime conformance, security, or suitability certificate. Package authors
identify AI-assisted SpecPM curation, not upstream ownership.

Each manifest links its exact upstream revision and the original P56-T4 archive
at a pinned SpecHarvester commit. `evidence/curation.json` records the archive
digest, original candidate file digests, source paths/ranges/full-file digests,
and the digests of the evidence actually shipped. Source files were checked
against the frozen custodian inventory. No upstream package code was executed.
These snapshots are not advertised as the latest upstream releases. SpecPackage
versions identify these descriptions; Axios preserves its original candidate's
version, while the other four use `0.1.0` rather than an upstream software version.

No canonical intent mappings are invented. Discovery uses meaningful purpose
and capability descriptions with stable package-owned IDs.

## Source Review Corrections

- RTK: replace inaccurate excerpts with byte-preserving source selections;
  include the runner, source receipt and upstream license in the archive.
  Output reduction remains an estimate, not a universal token-billing promise.
- Codex: include installation/logging documentation and complete LICENSE/NOTICE;
  limit the unknown Python-version statement to the inspected README.
- Axios: describe fetch alongside XHR/HTTP adapters and outgoing requests as
  potentially state-changing, not merely network reads.
- Bitcoin: include the full RPC security documentation and COPYING notice;
  remove the invalid P2P interface kind. P2P behavior remains in capabilities and
  network effects, without pretending that an HTTP or event interface models it.
- n8n: use pinned references and source digests instead of redistributing
  upstream documentation. This intentionally limits offline evidence portability.
  Keep Sustainable Use/Enterprise licensing restrictions and conditional feature
  availability explicit. Workflow verification is documented simulation behavior,
  not an independently tested guarantee that destructive effects cannot occur.

The receipt distinguishes verbatim evidence from reference-only evidence. Author
notes are not represented as source bytes. All referenced evidence and receipts
must survive `specpm pack`; regression tests enforce this property.

## Validation

Run the focused catalog contracts and the deployment checks:

```sh
.venv/bin/python -m pytest tests/test_curated_seed_packages.py
make dev-reload
make dev-smoke
```

The local registry validates and packs all accepted sources, including these five.
Public Pages will only contain the additions after merge and deployment; a smoke
test of the currently deployed Pages cannot certify an unmerged change.

Validation on 2026-09-06: all five packages validate without errors or warnings;
the seven focused contracts and all 287 Python tests pass. Ruff lint/format checks
pass for the new test file. Original archive bindings were independently checked
for all 38 original candidate files. `make dev-reload` and `make dev-smoke` pass:
the local catalog contains 14 package IDs and 15 versions. `make pages-smoke`
passes for the existing deployed catalog (9 IDs, 10 versions), not these additions.

## Review Follow-Up: Outbound Data Flow

PR #141 identified an inherited semantic error: the Codex candidate classified
remote agent requests as `network_read`, omitting the outbound disclosure of
prompts and potentially images or repository context. The curated copy now uses
`network_write`, describes those data categories and configuration-dependent
limits, and links the effect to the SDK evidence covering inputs and API routing.

The source evidence was available; this was not an evidence-access failure.
The original candidate used the wrong classification, and curation failed to
apply the Axios outbound-request correction consistently to Codex. Validation
accepts both effect kinds and does not infer data flow from natural language.
The initial tests checked structure, evidence integrity and packaging, not this
semantic obligation. Passing those tests did not prove the effects were accurate.

The regression suite now checks outbound request effects for Codex, Axios and
n8n, including Codex disclosure text and its evidence link. Future source review
must trace each boundary crossing: what leaves, where it goes, what returns,
and which conditions apply. Receiving a response must not hide a request's
outbound data. These bounded tests protect reviewed facts, not arbitrary future
AI-authored descriptions; a general semantic guarantee is still not claimed.
