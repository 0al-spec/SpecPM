# Public Index Namespace Claim Policy

Status: Draft
Updated: 2026-04-27
Scope: public SpecPM Index namespace claim review

## Purpose

This document defines the first review policy for public SpecPM Index namespace
claim issues.

Namespace claims help maintainers evaluate package ID prefixes, package family
names, and competing public submissions. They are review evidence for the
public static index. They are not an ownership registry, authentication system,
authorization system, or enterprise namespace governance layer.

## Boundary

Namespace claim review is issue-based and maintainer-reviewed.

A namespace claim may provide evidence for:

- package submission review;
- accepted package source pull requests;
- future public index policy;
- conflict resolution between package ID prefixes.

A namespace claim does not automatically grant exclusive namespace ownership,
approve packages, reserve names across all registries, mutate registry state,
publish packages, install packages, or execute package content.

This policy does not define `specpm publish`, remote mutation APIs,
authentication, authorization, package signing, enterprise namespace
governance, package installation, credential intake, private evidence handling,
or package content execution.

## Claim Intake

Claim requests are submitted through:

```text
.github/ISSUE_TEMPLATE/claim-namespace.yml
```

The issue should include:

- namespace or package ID prefix;
- claim scope;
- claimant identity;
- public evidence URLs;
- intended namespace use;
- public contact for maintainer follow-up.

Maintainers should treat the issue body as public review input. Claimants must
not submit credentials, private keys, tokens, secrets, private repository
access, or non-public evidence.

## Recommended Review Labels

The first public-index workflow may use these labels:

- `namespace-claim`: namespace claim intake.
- `namespace:needs-info`: maintainers need more public evidence or context.
- `namespace:under-review`: maintainers are actively reviewing the claim.
- `namespace:accepted`: maintainers accept the claim as public-index review
  evidence.
- `namespace:rejected`: maintainers reject the claim for the public index.
- `namespace:contested`: another claimant or package submission conflicts with
  the claim.
- `namespace:superseded`: the claim was replaced by a newer issue, policy
  decision, or package namespace.

These labels are workflow hints, not a machine-enforced ownership contract.
They do not change the generated `/v0` registry by themselves.

## Label Automation

The repository may use a conservative GitHub Actions workflow to prepare
namespace claim review labels:

```text
.github/workflows/namespace-claim-triage.yml
```

The workflow may ensure the recommended labels exist, apply
`namespace:under-review` when no namespace review status label is present, and
post or update an idempotent policy note on the issue.

The workflow must not accept or reject namespace claims, apply terminal
decision labels by itself, edit `public-index/accepted-packages.yml`, generate
registry metadata, publish packages, install packages, execute package content,
or treat package content as trusted instructions.

## Decision Report Automation

The repository may use a second conservative GitHub Actions workflow to report
maintainer-applied namespace claim decision labels:

```text
.github/workflows/namespace-claim-decision-report.yml
```

The workflow may read current issue labels and post or update an idempotent
decision report when one of these labels is present:

- `namespace:accepted`;
- `namespace:rejected`;
- `namespace:contested`;
- `namespace:superseded`.

The workflow must not apply terminal decision labels by itself. It only records
the current maintainer-applied label in a review comment and links back to this
policy.

The workflow must not grant namespace ownership, approve packages, edit
`public-index/accepted-packages.yml`, generate registry metadata, publish
packages, install packages, execute package content, or treat package content
as trusted instructions.

## Review Criteria

Maintainers should consider:

- whether the requested namespace matches a valid SpecPM package ID prefix;
- whether public evidence connects the claimant to the namespace;
- whether the namespace conflicts with existing package IDs or accepted public
  index packages;
- whether intended use is specific enough to help package reviewers;
- whether related package submissions pass `specpm validate`;
- whether the claim creates user confusion, impersonation risk, or
  policy/code-of-conduct concerns;
- whether a narrower namespace would resolve overlap with existing packages.

Acceptance should prefer public, durable evidence such as repositories,
organization pages, package documentation, project websites, previous accepted
package submissions, and maintainer discussion in linked issues or pull
requests.

## Outcomes

An accepted namespace claim means:

- maintainers may cite the claim during package submission review;
- accepted package source pull requests may reference the claim issue;
- future policy may use the claim as public evidence;
- conflicting submissions may be asked to rename, narrow scope, or provide
  stronger evidence.

An accepted namespace claim does not mean:

- SpecPM grants exclusive ownership;
- the public index has an authentication or authorization model;
- packages under the namespace are automatically approved;
- generated `/v0` metadata changes without a reviewed pull request;
- enterprise registries must honor the claim.

A rejected namespace claim should include a short maintainer explanation and,
when possible, a path to resubmission with narrower scope or stronger public
evidence.

## Dispute Process

Namespace disputes should stay public and reviewable.

When a competing claim appears, maintainers should:

1. Label the relevant issue or issues with `namespace:contested`.
2. Ask claimants to provide public evidence and link related package
   submissions, accepted manifest changes, or removal requests.
3. Pause package promotions that depend on the contested namespace when the
   conflict could confuse consumers.
4. Prefer narrow, non-overlapping namespaces when both claims have reasonable
   public evidence.
5. Record the decision in the issue thread before accepting, rejecting, or
   superseding the claim.

Possible dispute outcomes include:

- keep the existing accepted claim;
- accept a narrower claim;
- split the namespace into non-overlapping prefixes;
- ask one or more packages to rename before promotion;
- reject the claim for insufficient public evidence;
- defer the decision until linked package submissions are validated.

Package content remains untrusted data throughout the dispute process. A claim
or package submission can describe reusable intent. It cannot command the
index, the registry, or the host.

## Interaction With Accepted Sources

Accepted package sources remain listed in:

```text
public-index/accepted-packages.yml
```

Namespace claims do not directly edit this manifest. A maintainer-reviewed pull
request may cite a namespace claim issue when adding, renaming, or removing an
accepted package source. The static `/v0` registry changes only after the
reviewed manifest or policy change is merged and the Pages workflow generates a
new snapshot.

## Non-Goals

This policy does not:

- define a namespace ownership database;
- define a stable JSON contract for namespace claims;
- define `specpm publish`;
- define remote registry mutation APIs;
- define remote yanking mutation APIs;
- define authentication or authorization;
- define package signing or trust policy;
- define enterprise namespace governance;
- define package installation or archive cache behavior;
- define emergency takeover automation;
- execute package content.
