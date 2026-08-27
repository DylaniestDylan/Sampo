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
**Phase 1 implementation status:** P01.01 and P01.02 complete; P01.03.01 is next.  
**Runnable application:** Yes — local API shell only.  
**Usable end-user functionality:** None yet.

Sampo is being designed exclusively for one trusted local end user on their own machine. No multi-user, LAN/public-hosting, remote-service, or enterprise deployment work exists or is currently required.

## What Exists

The project now contains its planning/development-governance documentation and initial Python project skeleton:

- `AGENTS.md` — repository-level development-agent instructions.
- `.gitignore` — excludes local environments, caches, secrets, databases, model files, logs, build output, and editor/OS artifacts.
- `pyproject.toml` — project metadata, bounded FastAPI/Uvicorn production dependencies, a separate HTTPX/pytest test dependency group, and pytest discovery configuration.
- `app/` — importable Python package with Phase 1 responsibility-boundary packages, a backend-owned FastAPI application factory, a process-only health route, validated loopback bind settings, and a runnable module entry point.
- `tests/` — deterministic package-import, application-factory, health-route, settings, and startup-composition tests.
- `docs/project/Architecture.md` — product architecture and roadmap.
- `docs/project/STATUS.md` — implementation-state record.
- `docs/project/DEVELOPMENT.md` — canonical operational guide.
- `docs/project/implementation/Phase-01-Workspace-Foundation-and-Local-Harness.md` — approved active Phase 1 implementation contract.
- `docs/human/` — reserved for non-authoritative human-facing notes/design material; no governing content lives there.

No ADRs exist yet because no significant implementation decision has required one.

A minimal FastAPI application factory and `GET /health` route exist. The route returns only `{"status": "ok"}` for Sampo process health; it does not report model-runtime availability. A typed `ApplicationSettings` object defaults `bind_host` to `127.0.0.1`, requires an explicit bind port, accepts numeric loopback addresses, and rejects wildcard, LAN/public, and hostname bind values. Running `python -m app` starts the local API shell on `127.0.0.1:8000`; no end-user application behavior exists yet.

## What Does Not Exist Yet

The following are **not implemented** yet:

- Jinja2 templates or local frontend assets;
- Alpine.js integration;
- localhost API/trust-perimeter middleware;
- application-owned harness implementation;
- `ModelRuntime` interface implementation;
- fake model runtime;
- `llama.cpp` adapter/integration;
- generation streaming or cancellation;
- model-callable tool registry;
- real-runtime smoke test;
- SQLite database or durable persistence;
- Personas or conversations;
- knowledge, retrieval, research, web research, memory, multimodal, or observation features.

Later-phase features are intentionally absent and should remain absent until their approved phase.

## Current Verification

The local API shell is runnable. The automated suite contains eleven foundation, health-route, settings, and startup test cases.

The initial `pyproject.toml` metadata has been checked with TOML-aware IDE inspection and `git diff --check`.

The P01.01.02 package/test directory structure has been checked for the required paths, absence of feature scaffolding, Python-file inspection errors, and whitespace errors.

The project-local PyCharm interpreter has been verified as Python 3.14.7 with `pip` available, matching `pyproject.toml`; the Phase 1 boundary packages import successfully with that interpreter.

The root ignore policy has been checked against representative local environment, cache, secret, database, model, log, and editor artifacts while preserving project source files.

The focused startup-composition test and complete configured suite were run with Python 3.14.7, FastAPI 0.141.1, Uvicorn 0.52.4, HTTPX 0.28.1, and pytest 9.1.1: **1 passed** and **11 passed**, respectively. The real local startup path was also exercised: Uvicorn bound to `127.0.0.1:8000`, `GET /health` returned HTTP 200 with `{"status":"ok"}`, and the process shut down cleanly. The verified environment-setup, run, health-check, and test commands are recorded in `docs/project/DEVELOPMENT.md`.

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
