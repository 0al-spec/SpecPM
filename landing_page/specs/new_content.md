# Финальная структура лендинга SpecPM

## 1. Header / Navigation

```text
SpecPM
```

Navigation:

```text
Registry
How it Works
For Agents
Docs
```

CTA:

```text
Resolve a Need
```

Secondary CTA:

```text
Explore Specs
```

---

# 2. Hero Section

## H1

```text
Resolve needs into specifications.
Implementations come included.
```

## Subheadline

```text
SpecPM is a specification registry and need resolution engine that turns implementation needs into concrete specs — each backed by real modules, subsystems, and code.
```

## Primary CTA

```text
Resolve a Need
```

## Secondary CTA

```text
Explore the Registry
```

## Small trust / positioning line

```text
Spec-first. Implementation-backed. Built for agentic software creation.
```

---

# 3. Hero UI Mock Text

```text
Need:
User authentication for a B2B SaaS dashboard

Resolved specification:
auth.user-session

Implementation included:
OAuth adapter
JWT session module
Passwordless login flow
Role-based access layer

Fit:
98% match

Why this spec:
Matches SaaS auth requirements, supports enterprise identity providers, and includes production-ready implementation paths.
```

Alternative compact UI version:

```text
Need
User authentication

Resolved Spec
auth.user-session

Includes
OAuth adapter
JWT sessions
Passwordless login
RBAC subsystem

Best Fit
98%
```

---

# 4. Core Product Statement

## Section title

```text
Not another package manager.
A registry of working specifications.
```

## Body

```text
Traditional package managers expose code first.

SpecPM works differently.

It stores specifications as the primary unit — structured, reusable definitions of what a module or subsystem should do. Each specification is connected to real implementation options, so a need can be resolved into a spec, and the spec can lead directly to working code.
```

## Punchline

```text
You don’t start with packages.
You start with the right specification.
```

---

# 5. Problem Section

## Title

```text
Implementation decisions slow everything down.
```

## Body

```text
Every product need creates the same loop:

Search for libraries.
Compare APIs.
Read docs.
Evaluate trade-offs.
Wire integrations.
Rewrite glue code.

SpecPM removes that loop.

Instead of searching for implementation details, agents and developers resolve needs into specification-backed modules that already know how they can be implemented.
```

## Short card copy

```text
Stop searching.
Stop comparing.
Stop wiring from scratch.
```

---

# 6. How It Works

## Title

```text
How SpecPM works
```

## Step 1

```text
1. Describe the need
```

```text
A user, developer, or agent describes what is required: authentication, billing, notifications, audit logs, data sync, search, permissions, or any other system part.
```

## Step 2

```text
2. Resolve the best specification
```

```text
SpecPM searches the specification registry and finds the best matching spec for the need — not just by name, but by structure, constraints, context, and intended use.
```

## Step 3

```text
3. Get implementation paths included
```

```text
Each resolved spec is backed by real modules, subsystems, adapters, or code templates. The implementation is not the starting point — it comes with the specification.
```

## Step 4

```text
4. Use it in the system graph
```

```text
The resolved spec can be used by SpecGraph agents, developers, or automation workflows as a concrete building block for the system being designed.
```

---

# 7. Main Value Proposition

## Title

```text
Specifications are the new dependency layer.
```

## Body

```text
Code dependencies tell you what you installed.

Specifications tell you what the system needs, why it exists, how it should behave, and which implementation can satisfy it.

SpecPM makes specifications searchable, reusable, resolvable, and implementation-backed.
```

## Highlight

```text
Need → Specification → Implementation
```

---

# 8. Registry Section

## Title

```text
A registry for specs, not just code.
```

## Body

```text
SpecPM stores reusable specifications for common modules, subsystems, and integration patterns. Every spec is structured enough for agents to reason about and practical enough to connect to real implementation.
```

## Cards

### Card 1

```text
Authentication
```

```text
User sessions, OAuth flows, passwordless login, enterprise SSO, RBAC, and identity lifecycle specs.
```

### Card 2

```text
Billing
```

```text
Subscriptions, invoices, metering, checkout flows, payment adapters, and revenue operations specs.
```

### Card 3

```text
Notifications
```

```text
Email, push, SMS, webhooks, routing logic, templates, delivery policies, and retry behavior specs.
```

### Card 4

```text
Data Systems
```

```text
Pipelines, sync jobs, storage interfaces, indexing, search, analytics, and data transformation specs.
```

### Card 5

```text
Security & Audit
```

```text
Access policies, audit logs, permission boundaries, compliance events, and operational visibility specs.
```

### Card 6

```text
Infrastructure Modules
```

```text
Deployment units, runtime requirements, background workers, queues, schedulers, and service boundaries.
```

---

# 9. For Agents Section

## Title

```text
Built for agents that write specs.
```

## Body

```text
SpecGraph agents don’t need to implement every system part from scratch.

When an agent identifies a need inside a system design, it can ask SpecPM for the best matching specification. SpecPM returns a concrete, implementation-backed spec that the agent can use as part of the larger system graph.
```

## Supporting line

```text
The agent keeps designing.
SpecPM handles resolution.
```

## Example

```text
SpecGraph agent:
“I need enterprise-ready authentication for a SaaS product.”

SpecPM:
“Use auth.enterprise-sso.
It includes SAML, OAuth, SCIM provisioning, RBAC, and audit-ready session tracking.”
```

---

# 10. Differentiation Section

## Title

```text
Why SpecPM is different
```

## Block 1

```text
Package managers expose implementation.
SpecPM resolves intent into specs.
```

## Block 2

```text
Registries give you options.
SpecPM gives you the best-fit specification.
```

## Block 3

```text
Libraries require interpretation.
Specs carry structure, purpose, and implementation paths.
```

## Block 4

```text
Developers choose packages manually.
Agents resolve needs automatically.
```

---

# 11. “Before / After” Section

## Title

```text
From manual implementation search to spec resolution.
```

## Before

```text
Before SpecPM

1. Search for a library
2. Compare APIs
3. Read documentation
4. Guess the right fit
5. Write integration glue
6. Maintain implementation decisions manually
```

## After

```text
With SpecPM

1. Describe the need
2. Resolve the best specification
3. Get implementation paths included
4. Attach the spec to the system design
5. Let agents compose from structured building blocks
```

## Punchline

```text
SpecPM does not remove implementation.
It moves implementation behind the specification.
```

---

# 12. Feature Cards

## Feature 1

```text
Need Resolution
```

```text
Turn natural-language or structured implementation needs into concrete specifications from the registry.
```

## Feature 2

```text
Specification Registry
```

```text
Store, search, version, and reuse specifications for modules, subsystems, and integrations.
```

## Feature 3

```text
Implementation-Backed Specs
```

```text
Every useful spec can point to real code, adapters, templates, modules, or subsystem implementations.
```

## Feature 4

```text
Best-Fit Matching
```

```text
Resolve the most suitable spec based on context, constraints, system requirements, and intended behavior.
```

## Feature 5

```text
Agent-Ready Interface
```

```text
Designed for agents that need structured building blocks while creating larger system specifications.
```

## Feature 6

```text
Reusable System Parts
```

```text
Avoid rebuilding the same auth, billing, notification, search, audit, and data modules again and again.
```

---

# 13. Strong Mid-Page Statement

```text
You don’t choose implementations first.

You resolve the need into a specification —
and the implementation follows.
```

Alternative:

```text
The specification is the contract.
The implementation is attached.
```

---

# 14. Example Section

## Title

```text
Example: resolving authentication
```

## Input

```text
Need:
A secure authentication module for a B2B SaaS product with enterprise SSO and role-based access.
```

## SpecPM output

```text
Resolved specification:
auth.enterprise-sso

Includes:
SAML / OAuth integration
SCIM user provisioning
Role-based access control
Session lifecycle management
Audit event tracking
Implementation templates
Integration contract
```

## Summary

```text
Instead of choosing between auth providers, libraries, and custom flows, SpecPM resolves the need into a reusable spec that already knows which implementations can satisfy it.
```

---

# 15. Secondary Example

## Title

```text
Example: resolving billing
```

## Input

```text
Need:
Subscription billing for a usage-based SaaS product.
```

## Output

```text
Resolved specification:
billing.usage-subscription

Includes:
Metered usage tracking
Plan management
Invoice generation
Payment provider adapters
Webhook handling
Dunning flow
Revenue event schema
```

## Summary

```text
The need becomes a spec.
The spec comes with implementation paths.
```

---

# 16. SpecGraph Integration Section

## Title

```text
Designed to work with SpecGraph
```

## Body

```text
SpecGraph defines what the system should do.

SpecPM helps fill that system with concrete, implementation-backed specifications.

When a SpecGraph agent writes or expands a system design, it can use SpecPM to resolve individual needs into reusable specs instead of generating every implementation from scratch.
```

## Formula

```text
SpecGraph defines the system.
SpecPM resolves the parts.
```

Alternative formula:

```text
SpecGraph creates the architecture.
SpecPM supplies the specs.
```

---

# 17. Developer / Agent API Teaser

## Title

```text
Resolve specs programmatically
```

## Body

```text
SpecPM is built for both humans and agents. Search the registry, resolve needs, inspect specs, and retrieve implementation-backed modules through a simple API.
```

## CLI Mock

```bash
specpm resolve "enterprise authentication for B2B SaaS"
```

## Output Mock

```yaml
resolved:
  spec: auth.enterprise-sso
  match: 0.98
  includes:
    - saml-sso
    - oauth-adapter
    - scim-provisioning
    - rbac
    - audit-events
  implementations:
    - auth-enterprise-module
    - oauth-saml-adapter
    - session-service-template
```

---

# 18. Final CTA Section

## Title

```text
Resolve your next implementation need.
```

## Body

```text
Start with a need.
Get the right specification.
Use the implementation already behind it.
```

## Primary CTA

```text
Resolve a Need
```

## Secondary CTA

```text
Explore Specs
```

---

# 19. Footer Taglines

Варианты для footer / metadata / OpenGraph:

```text
SpecPM — specification registry and need resolution engine.
```

```text
Resolve needs into specifications. Implementations come included.
```

```text
A registry of implementation-backed specifications for agentic software creation.
```

```text
The spec-first way to find working modules and subsystems.
```

---

# Финальный короткий набор для первого экрана

```text
Resolve needs into specifications.
Implementations come included.

SpecPM is a specification registry and need resolution engine that turns implementation needs into concrete specs — each backed by real modules, subsystems, and code.

[Resolve a Need] [Explore the Registry]

Spec-first. Implementation-backed. Built for agentic software creation.
```

---

# Самая важная формула продукта

```text
Need → Specification → Implementation
```

И главный differentiator:

```text
SpecPM does not give you packages to choose from.
It gives you the right specification — with implementation already attached.
```
