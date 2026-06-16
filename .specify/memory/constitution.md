<!--
SYNC IMPACT REPORT
==================
Version change: [TEMPLATE / unversioned] → 1.0.0
Bump rationale: MINOR — initial population of all principle placeholders from template.

Placeholders filled:
  PROJECT_NAME, PRINCIPLE_1..5 (names + descriptions), SECTION_2, SECTION_3,
  GOVERNANCE_RULES, CONSTITUTION_VERSION, RATIFICATION_DATE, LAST_AMENDED_DATE

Templates reviewed:
  - .specify/templates/plan-template.md   ✅ aligned (Constitution Check gate present)
  - .specify/templates/spec-template.md   ✅ aligned (NFR Success Criteria present)
  - .specify/templates/tasks-template.md  ✅ aligned (Security + Performance tasks in Phase N)

Deferred TODOs: none
-->

# i2i-anticlock-upskilling Constitution
<!-- Example: Spec Constitution, TaskFlow Constitution, etc. -->

## Core Principles

### I. Coding Standards & Clean Code
<!-- Example: I. Library-First -->
All code MUST follow language-idiomatic style guides (e.g., PEP 8 for Python, Airbnb/Google
for JS/TS). Functions and classes MUST have a single, clearly named purpose. Inline comments
are reserved for non-obvious WHY rationale only. Design patterns (Factory, Repository,
Strategy, Observer, etc.) MUST be applied only when they solve a concrete, present problem —
speculative abstraction is a violation. Pattern use MUST be justified; complexity introduced
MUST be outweighed by the benefit delivered.

### II. SOLID Principles & Design Patterns
<!-- Example: II. CLI Interface -->
- **S — Single Responsibility**: Each class/module MUST have exactly one reason to change.
- **O — Open/Closed**: Modules MUST be open for extension, closed for modification.
- **L — Liskov Substitution**: Subtypes MUST be substitutable for their base types without
  altering correctness.
- **I — Interface Segregation**: Interfaces MUST be narrow and client-specific; no caller SHOULD
  depend on methods it does not use.
- **D — Dependency Inversion**: High-level modules MUST depend on abstractions, not concrete
  implementations; dependencies MUST be injected, not instantiated internally.
SOLID violations MUST be documented in the Complexity Tracking table of plan.md with explicit
justification.

### III. Code Reusability & DRY
<!-- Example: III. Test-First (NON-NEGOTIABLE) -->
Duplication is a defect. Any logic appearing more than once MUST be extracted into a shared
utility, service, or base class before the second use is merged. Copy-paste code MUST NOT be
used as a shortcut. Shared utilities MUST be independently testable. Re-use of existing
libraries or internal packages SHOULD be evaluated before writing new logic.

### IV. Security First
<!-- Example: IV. Integration Testing -->
Security is non-negotiable and MUST be treated as a first-class requirement.
- All user inputs MUST be validated and sanitised at system boundaries.
- Authentication and authorisation MUST follow the principle of least privilege.
- Secrets, credentials, and API keys MUST NEVER appear in source code or version control.
- Dependencies MUST be kept up to date; known CVEs MUST be remediated before release.
- SQL queries MUST use parameterised statements; dynamic query construction is forbidden.
- All external-facing APIs MUST enforce rate limiting.
- PRs touching auth, data persistence, or external integrations MUST receive a dedicated
  security review.

### V. User Experience (UX)
<!-- Example: V. Observability, VI. Versioning & Breaking Changes, VII. Simplicity -->
The end user's time and cognitive load MUST be respected.
- Primary UI flows MUST be completable without documentation.
- Error messages MUST be actionable (state what went wrong and what the user can do next);
  stack traces MUST NEVER appear in user-facing surfaces.
- Response times MUST meet the NFR performance targets defined below.
- Accessibility (WCAG 2.1 AA) MUST be addressed from day one, not retrofitted.
- Forms MUST provide inline validation feedback before submission.
- Destructive actions MUST require explicit user confirmation.

## Non-Functional Requirements
<!-- Example: Additional Constraints, Security Requirements, Performance Standards, etc. -->

**Performance**
- API p95 latency: ≤ 200 ms under expected load; ≤ 500 ms at 2× peak load.
- Page/screen initial render MUST complete within 2 s on standard broadband; TTI ≤ 3 s.
- No unbounded queries (missing WHERE clause or full-table scans on tables > 10 k rows) MUST
  reach production. Query plans MUST be reviewed for such queries.
- Frequently-read, rarely-changed data MUST be cached; cache invalidation strategy MUST be
  documented at design time.

**Scalability & Maintainability**
- Architecture MUST support horizontal scaling of stateless services without code changes.
- All state MUST be externalised to a backing service; no in-process state that cannot survive
  a restart.
- Modules MUST be loosely coupled; a change in one bounded context MUST NOT require changes in
  another to keep tests green.
- Cyclomatic complexity per function MUST stay ≤ 10; functions longer than 40 lines SHOULD be
  refactored.
- Dependencies MUST be pinned to exact versions in lock files; upgrades MUST go through the
  standard PR review cycle.

## Development Workflow & Quality Gates
<!-- Example: Development Workflow, Review Process, Quality Gates, etc. -->

All contributions MUST pass the following gates before merge:
1. **Linting & Formatting**: CI MUST reject code that fails the project linter/formatter.
2. **Test Coverage**: New code MUST be accompanied by tests; coverage MUST NOT decrease on main.
3. **Constitution Check**: Every plan.md MUST include a Constitution Check section that maps the
   design to each core principle; violations MUST be justified in Complexity Tracking.
4. **Security Review**: PRs touching auth, data persistence, or external integrations MUST
   receive a dedicated security review comment.
5. **Performance Baseline**: Features adding or modifying data-fetching paths MUST include an
   expected query count and estimated latency in the plan.
6. **Peer Review**: All PRs MUST be approved by at least one other engineer before merge.

## Governance
<!-- Example: Constitution supersedes all other practices; Amendments require documentation, approval, migration plan -->

This constitution supersedes all other internal practices. When a practice conflicts with this
document, this document wins. Amendments require:
1. A proposal PR describing the change and its rationale.
2. Approval from at least two engineers.
3. A migration plan if existing code is affected.
4. A version bump following the semantic versioning policy (MAJOR: principle removal/redef;
   MINOR: new principle or material expansion; PATCH: clarification or wording fix).

All PRs and code reviews MUST verify compliance. Use `.specify/memory/constitution.md` as the
single source of truth for project governance during runtime development.

**Version**: 1.0.0 | **Ratified**: 2026-06-15 | **Last Amended**: 2026-06-15
<!-- Example: Version: 2.1.1 | Ratified: 2025-06-13 | Last Amended: 2025-07-16 -->
