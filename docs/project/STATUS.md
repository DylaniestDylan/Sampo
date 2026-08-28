# STATUS.md

## Purpose

`docs/project/STATUS.md` is the canonical record of **what currently exists in the Sampo repository and what has actually been verified**.

It describes implementation reality only. It does not define future product behavior or replace architectural or phase requirements.

The documentation authority model is defined in `docs/project/Architecture.md` §1.1. This file is descriptive only: if it becomes stale, update it to match verified repository reality. Do not change Architecture or phase intent merely to make them agree with the current implementation.

## Current State

**Implementation state:** Phase 1 implementation in progress.  
**Current roadmap phase:** Phase 1 — Workspace Foundation and Local Harness.  
**Active phase contract:** `docs/project/implementation/Phase-01-Workspace-Foundation-and-Local-Harness.md`  
**Phase contract status:** Approved and active.  
**Phase 1 implementation status:** P01.01–P01.03, P01.04.01–P01.04.05, and P01.05–P01.07 complete. Initial middleware coverage for P01.04.06 exists; that checkbox remains open until the real SSE route is tested at P01.12. P01.08.01 is the next executable task.
**Runnable application:** Yes — local API and sparse local web shell.
**Usable end-user functionality:** None yet.

Sampo is being designed exclusively for one trusted local end user on their own machine. No multi-user, LAN/public-hosting, remote-service, or enterprise deployment work exists or is currently required.

## What Exists

The project now contains its planning/development-governance documentation and initial Python project skeleton:

- `AGENTS.md` — repository-level development-agent instructions.
- `.gitignore` — excludes local environments, caches, secrets, databases, model files, logs, build output, and editor/OS artifacts.
- `pyproject.toml` — project metadata, bounded FastAPI/Jinja2/Uvicorn production dependencies, a separate HTTPX/pytest test dependency group, and pytest discovery configuration.
- `app/` — importable Python package with Phase 1 responsibility-boundary packages, a backend-owned FastAPI application factory, a process-only health route, a sparse Jinja2 web shell, local CSS and Alpine.js assets, local-web trust middleware, application-owned runtime types/protocol, a deterministic fake runtime, validated loopback bind settings, and a runnable module entry point.
- `tests/` — deterministic package-import, application-factory, health-route, settings, startup-composition, local-web, trust-perimeter, runtime-domain, runtime-protocol, runtime-contract, and fake-runtime tests.
- `docs/project/Architecture.md` — product architecture and roadmap.
- `docs/project/STATUS.md` — implementation-state record.
- `docs/project/DEVELOPMENT.md` — canonical operational guide.
- `docs/project/implementation/Phase-01-Workspace-Foundation-and-Local-Harness.md` — approved active Phase 1 implementation contract.
- `docs/human/` — reserved for non-authoritative human-facing notes/design material; no governing content lives there.

No ADRs exist yet because no significant implementation decision has required one.

A minimal FastAPI application factory and `GET /health` route exist. The route returns only `{"status": "ok"}` for Sampo process health; it does not report model-runtime availability. `GET /` renders a sparse Jinja2 shell with a backend-issued CSRF token and only locally served CSS and vendored Alpine.js 3.16.3. Request middleware accepts only loopback/local hostnames, requires same-origin plus CSRF validation for state-changing `/api/*` requests, provides initial same-origin coverage for future `/api/*/events` streams, and has no permissive CORS behavior.

Application-owned `RuntimeCapabilities`, `ModelRequest`, normalized started/delta/completed/stopped/failed event values, and a bounded runtime error taxonomy exist without `llama.cpp` transport fields. The `ModelRuntime` protocol defines capability probing, streaming, and abort; runtime injection is application-composition state rather than global transport state. `FakeModelRuntime` provides deterministic chunks, an event gate, known-failure injection, and abort-call tracking, and passes the reusable runtime contract tests. A typed `ApplicationSettings` object defaults `bind_host` to `127.0.0.1`, requires an explicit bind port, accepts numeric loopback addresses, and rejects wildcard, LAN/public, and hostname bind values. Running `python -m app` starts the local shell on `127.0.0.1:8000`; no prompt-generation UI or end-user model behavior exists yet.

## What Does Not Exist Yet

The following are **not implemented** yet:

- application-owned harness implementation;
- `llama.cpp` adapter/integration;
- generation streaming or cancellation;
- model-callable tool registry;
- real-runtime smoke test;
- SQLite database or durable persistence;
- Personas or conversations;
- knowledge, retrieval, research, web research, memory, multimodal, or observation features.

Later-phase features are intentionally absent and should remain absent until their approved phase.

## Current Verification

The local API/web shell is runnable. The automated suite contains 66 deterministic foundation, web-shell, trust-perimeter, runtime-domain, runtime-contract, health-route, settings, and startup test cases.

The initial `pyproject.toml` metadata has been checked with TOML-aware IDE inspection and `git diff --check`.

The P01.01.02 package/test directory structure has been checked for the required paths, absence of feature scaffolding, Python-file inspection errors, and whitespace errors.

The project-local PyCharm interpreter has been verified as Python 3.14.7 with `pip` available, matching `pyproject.toml`; the Phase 1 boundary packages import successfully with that interpreter.

The root ignore policy has been checked against representative local environment, cache, secret, database, model, log, and editor artifacts while preserving project source files.

The P01.03 web-foundation checkpoint passed **14 tests**. The P01.04 trust-perimeter checkpoint passed **39 tests**. The focused P01.05–P01.07 runtime checks passed **27 tests**, and the complete deterministic suite passed **66 tests** with Python 3.14.7, FastAPI 0.141.1, Jinja2 3.1.6, Uvicorn 0.52.4, HTTPX 0.28.1, and pytest 9.1.1. The current real local startup path was exercised: Uvicorn bound to `127.0.0.1:8000`, `GET /` returned the Jinja2 shell with HTTP 200 and local asset references, and the process shut down cleanly. The process-only `GET /health` path remains covered by deterministic API tests. The verified environment-setup, run, health-check, and test commands are recorded in `docs/project/DEVELOPMENT.md`.

## Status Update Rules

Update this file when repository reality materially changes.

For each meaningful implementation increment:

1. record only behavior/files/capabilities that actually exist;
2. distinguish implemented behavior from planned behavior;
3. record relevant tests or verification that have actually been run;
4. remove stale claims immediately when implementation changes invalidate them;
5. do not mark a phase/task complete merely because code was written — required tests and acceptance criteria must also be satisfied;
6. keep future requirements in `docs/project/Architecture.md` or the active phase contract rather than copying them here.

At Phase 1 completion, this file should describe the resulting runnable local vertical slice and the checks that prove it exists.
