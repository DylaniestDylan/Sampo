# AGENTS.md

## Purpose

This file gives repository-level instructions to **Codex while developing Sampo**.

It answers:

> **How must I work?**

It does not define Sampo's product architecture. `docs/project/Architecture.md` is the canonical source of product architecture and permanent architectural constraints.

Codex is the development agent building Sampo. It is **not** the local model/runtime that Sampo will expose to the user.

## Repository Context

Sampo is exclusively for **one trusted local end user on their own machine**.

Do not introduce multi-user tenancy, account/role administration, remote hosting, LAN/public deployment, or enterprise-service assumptions unless the user explicitly approves the corresponding architecture change.

Godot/GDScript is the first major use case, not the product boundary.

## Documentation Rules

Follow the documentation responsibility and authority model in `docs/project/Architecture.md` §1.1. Do not create a competing source of truth.

During repository work:

- planned product semantics belong in `docs/project/Architecture.md`;
- current phase scope, tasks, tests, and acceptance criteria belong in the active approved phase contract;
- verified implementation reality belongs in `docs/project/STATUS.md`;
- verified setup/run/test/troubleshooting procedures belong in `docs/project/DEVELOPMENT.md`;
- significant accepted technical rationale belongs in an ADR under `docs/project/adr/`;
- human-facing notes, sketches, diagrams, and exploratory material belong under `docs/human/` and are non-authoritative unless promoted into a governing project document;
- code and tests are implementation evidence, not authority to contradict the governing documents.

Do not duplicate large sections of one canonical document into another. Cross-reference the governing document when a short operational reminder is sufficient.

## Read Before Implementing

For any non-trivial implementation task, read what is relevant in this order:

1. `docs/project/Architecture.md`;
2. `docs/project/STATUS.md` to establish verified implementation reality and identify the current active phase;
3. the active approved phase contract;
4. relevant ADRs, if any;
5. nearby code and tests;
6. `docs/project/DEVELOPMENT.md` when the task affects setup, execution, testing, smoke tests, or troubleshooting.

This is a reading sequence, not an authority-precedence ladder. Authority remains domain-specific as defined by `docs/project/Architecture.md` §1.1.

Identify the applicable architectural invariants and phase acceptance criteria before changing code.

If substantial phase implementation is requested but the required approved phase contract does not exist, report the gap rather than inventing product semantics.

## Architecture Authority

Implementation documents may refine `docs/project/Architecture.md` only within their defined scope. They may not weaken or contradict an architectural invariant or requirement.

If implementation appears to require an architectural contradiction:

1. stop the conflicting implementation path;
2. identify the exact conflict;
3. present it to the user;
4. do not infer that an invariant has been waived;
5. continue only after explicit user approval of the architectural change.

Do not modify `docs/project/Architecture.md` unless the user explicitly requests an architecture change.

Routine implementation details explicitly deferred by `docs/project/Architecture.md` may be decided without escalation when they preserve all architectural invariants and active-phase acceptance criteria.

## Phase Discipline

Implementation follows the roadmap in `docs/project/Architecture.md`.

Before substantially implementing a phase:

1. identify the current phase;
2. read its approved implementation contract;
3. verify its prerequisites;
4. stay within its defined scope;
5. implement the smallest coherent compliant change;
6. satisfy the relevant tests and acceptance criteria before substantially advancing.

Phases are sequential by default. Do not pull later-phase product behavior forward merely because it is convenient.

Small preparatory abstractions are acceptable only when necessary for the current phase and when they do not effectively implement later-phase behavior.

Do not mark a phase task complete until its behavior and required focused tests are actually satisfied.

## Codex Development Permissions

Within the user's task and the available development environment, Codex may perform normal software-development work required to build Sampo, including:

- inspect, create, edit, move, and delete repository files when necessary;
- run repository development commands;
- create and use the local development environment;
- install or update project dependencies when justified by the current phase/task;
- run tests, linters, type checks, migrations, and the local application;
- inspect logs and development artifacts;
- use Git for inspection, status, diff, and other non-destructive development workflows;
- research external technical documentation when needed for implementation.

Do not perform destructive Git operations, discard user-authored work, push, publish, release, or commit unless explicitly requested.

Preserve user-authored changes unless they are directly incompatible with the explicitly requested task.

## Codex Permissions Are Not Sampo Model Permissions

Codex's development capabilities must never be used as justification for expanding Sampo's model-facing authority.

Sampo's model-facing capabilities remain governed by `docs/project/Architecture.md`. In particular, never expose Codex-like generic host capabilities such as filesystem mutation, shell/process execution, generated-code execution, Git/VCS control, package installation, unrestricted networking/browser automation, IDE/Godot control, or dynamic host-tool/plugin creation to Sampo's model.

Security must come from capability absence, narrow application-owned interfaces, and backend enforcement rather than model obedience.

A trusted backend operation does not automatically become a model-facing capability.

## Responsibility Boundaries During Implementation

Preserve the responsibility boundaries defined by `docs/project/Architecture.md` and refined by the active phase contract.

The exact folder layout may evolve where Architecture permits it, but do not conflate responsibilities merely for convenience.

In particular:

- browser/UI code must not become the enforcing authority for permissions or security policy;
- the harness remains model-facing orchestration rather than a second durable application state layer;
- runtime-specific `llama.cpp` transport details remain behind the application-owned runtime adapter;
- later-phase knowledge, research, memory, and observation behavior must not be smuggled into earlier phases through generic abstractions or placeholders.

## Dependency and Change Discipline

Before adding a dependency, verify that it:

1. is required by the current phase/task;
2. cannot reasonably be satisfied by the standard library or existing dependencies;
3. does not create an unnecessary process, network, or capability boundary;
4. preserves the local-only and lightweight product requirements;
5. is free/open-source where required by `docs/project/Architecture.md`.

Avoid speculative abstractions for hypothetical cloud providers, multi-user hosting, autonomous agents, distributed infrastructure, or future phases.

Avoid broad unrelated refactors during scoped work.

Prefer clear application-owned interfaces over framework magic. Keep security-sensitive decisions deterministic where practical, model-facing data structured and bounded, and failure behavior explicit.

Do not add silent fallback behavior that changes the configured model, service, permission set, Persona, knowledge scope, or capability when something fails.

## Testing Workflow

Testing is part of implementation.

For each change:

1. run the narrowest relevant tests while iterating;
2. add regression coverage for bugs and architectural/security boundaries when applicable;
3. run all checks required by the active phase before declaring the affected task complete;
4. report checks that could not be run and why.

Prefer deterministic fixtures over live public-network dependencies.

Do not claim a test, smoke path, runtime integration, or acceptance criterion passed unless it was actually executed successfully.

## Documentation Updates During Implementation

Keep documentation synchronized with repository reality without duplicating authority:

- update `docs/project/STATUS.md` when implementation reality materially changes;
- update `docs/project/DEVELOPMENT.md` when setup, run, test, smoke-test, or troubleshooting procedures change;
- update the active phase checklist/status only when its completion conditions are actually satisfied;
- create or update an ADR under `docs/project/adr/` when a significant accepted technical decision needs durable rationale;
- place optional explanatory notes or design sketches under `docs/human/`; never treat them as product requirements, current phase scope, or implementation truth unless explicitly promoted into the appropriate governing document.

Do not put planned behavior into `docs/project/STATUS.md` as though it already exists.

Do not put unverified or hypothetical commands into `docs/project/DEVELOPMENT.md` as though they work.

## Task Workflow

At task start:

1. read the applicable documents;
2. inspect relevant code/tests;
3. identify current implementation reality from `docs/project/STATUS.md` and the repository;
4. identify the applicable architectural invariants and phase acceptance criteria;
5. implement the smallest coherent compliant change.

During implementation:

- stay inside the authorized task and active phase scope;
- keep authorization and trust decisions server-side;
- keep security-sensitive decisions deterministic where practical;
- keep model-facing data structured and bounded;
- avoid hidden fallbacks;
- update tests with behavior;
- update operational/status documentation when the implementation changes them.

Before finishing:

1. review the diff for architectural or phase-scope violations;
2. run relevant automated checks;
3. verify no secrets, local databases, model files, caches, generated junk, or environment-specific artifacts were unintentionally added;
4. confirm no later-phase or forbidden model capability was accidentally exposed;
5. update `docs/project/STATUS.md` and `docs/project/DEVELOPMENT.md` where required;
6. summarize changes, tests run, checks not run, and known limitations.

## Stop Conditions

Stop the conflicting path and ask the user rather than guessing when:

- implementation would contradict `docs/project/Architecture.md`;
- a change would materially alter an architectural product semantic or trust boundary;
- substantial implementation is requested without the required approved phase contract;
- multiple plausible interpretations would create materially different product semantics;
- satisfying a task appears to require a dependency or deployment model outside the current architecture;
- satisfying a task appears to require giving Sampo's model-facing runtime a forbidden action capability.

Do not stop for routine implementation choices that Architecture or the active phase explicitly leaves open and that preserve all relevant requirements.

## Definition of Done

A task is done only when:

- the requested behavior is implemented;
- Architecture and active-phase requirements remain satisfied;
- relevant tests pass, or any checks that could not be run are explicitly reported;
- no forbidden model capability has been introduced;
- security/persistence implications relevant to the task are handled;
- `docs/project/STATUS.md` reflects the resulting implementation reality when materially changed;
- `docs/project/DEVELOPMENT.md` reflects any changed setup/run/test procedures;
- required phase/ADR documentation is updated where applicable; optional `docs/human/` notes are updated only when they remain useful to the user;
- the final report states significant implementation choices, tests run, and known limitations.

Core rule:

> **Codex may act to build Sampo. Sampo's model may only search, read, compare, reason, and explain within explicitly granted boundaries.**
