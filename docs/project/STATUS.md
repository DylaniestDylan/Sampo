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
**Phase 1 implementation status:** P01.01–P01.03, P01.04.01–P01.04.05, and P01.05–P01.09 complete. Initial middleware coverage for P01.04.06 exists; that checkbox remains open until the real SSE route is tested at P01.12. P01.10.01 is the next executable task.
**Runnable application:** Yes — local API and sparse local web shell.
**Usable end-user functionality:** None yet.

Sampo is being designed exclusively for one trusted local end user on their own machine. No multi-user, LAN/public-hosting, remote-service, or enterprise deployment work exists or is currently required.

## What Exists

The project now contains its planning/development-governance documentation and initial Python project skeleton:

- `AGENTS.md` — repository-level development-agent instructions.
- `.gitignore` — excludes local environments, caches, secrets, databases, model files, logs, build output, and editor/OS artifacts.
- `pyproject.toml` — project metadata, bounded FastAPI/HTTPX/Jinja2/Uvicorn production dependencies, a separate pytest test dependency group, and pytest discovery configuration.
- `app/` — importable Python package with Phase 1 responsibility-boundary packages, a backend-owned FastAPI application factory, a process-only health route, a sparse Jinja2 web shell, local CSS and Alpine.js assets, local-web trust middleware, application-owned runtime types/protocol, a deterministic fake runtime, a production `llama.cpp` adapter, an explicit empty model-tool boundary, validated loopback application/runtime settings, and a runnable module entry point.
- `tests/` — deterministic package-import, application-factory, health-route, settings, startup-composition, local-web, trust-perimeter, runtime-domain, runtime-protocol, runtime-contract, fake-runtime, mocked `llama.cpp` adapter, and tool-capability-boundary tests.
- `docs/project/Architecture.md` — product architecture and roadmap.
- `docs/project/STATUS.md` — implementation-state record.
- `docs/project/DEVELOPMENT.md` — canonical operational guide.
- `docs/project/implementation/Phase-01-Workspace-Foundation-and-Local-Harness.md` — approved active Phase 1 implementation contract.
- `docs/human/` — reserved for non-authoritative human-facing notes/design material; no governing content lives there.

No ADRs exist yet because no significant implementation decision has required one.

A minimal FastAPI application factory and `GET /health` route exist. The route returns only `{"status": "ok"}` for Sampo process health; it does not report model-runtime availability. `GET /` renders a sparse Jinja2 shell with a backend-issued CSRF token and only locally served CSS and vendored Alpine.js 3.16.3. Request middleware accepts only loopback/local hostnames, requires same-origin plus CSRF validation for state-changing `/api/*` requests, provides initial same-origin coverage for future `/api/*/events` streams, and has no permissive CORS behavior.

Application-owned `RuntimeCapabilities`, `ModelRequest`, normalized started/delta/completed/stopped/failed event values, a bounded unexpected-tool-request marker, and a bounded runtime error taxonomy exist without `llama.cpp` transport fields. The `ModelRuntime` protocol defines capability probing, streaming, and abort; runtime injection is application-composition state rather than global transport state. `FakeModelRuntime` provides deterministic chunks, an event gate, known-failure injection, and abort-call tracking, and passes the reusable runtime contract tests. A typed `ApplicationSettings` object defaults `bind_host` to `127.0.0.1`, requires an explicit bind port, accepts numeric loopback addresses, and rejects wildcard, LAN/public, and hostname bind values. Running `python -m app` starts the local shell on `127.0.0.1:8000`; no prompt-generation UI or end-user model behavior exists yet.

`LlamaCppModelRuntime` is the only production model adapter. It uses an adapter-internal HTTPX transport for the local `llama.cpp` health and OpenAI-compatible streaming-chat endpoints, translates only between transport-private payload/chunk shapes and application-owned runtime values, validates the nested streamed-response shapes before accessing them, maps expected transport and malformed-protocol failures into the Phase 1 runtime error taxonomy, and aborts active transport responses by Sampo request ID. A non-empty structured `delta.tool_calls` response becomes only a bounded application-owned marker containing the Sampo request ID; the adapter ends that stream without normal completion and does not retain tool names or arguments above the transport boundary. Both application settings and direct adapter construction reject non-numeric, non-loopback, credential-bearing, path-bearing, and remote/cloud runtime endpoints. HTTPX environment proxy settings are disabled for adapter calls, and failures do not retry or select another model/provider. This adapter is not yet wired into a harness, generation lifecycle, API, or browser flow; those remain later Phase 1 work.

The application-owned `ToolRegistry` has an immutable empty model-tool description set and no registration, invocation, dispatch, discovery, loading, or generic callable API. `HarnessToolBoundary` receives descriptions only from that registry and rejects the application-owned unexpected-tool marker with a static bounded `UnexpectedModelToolRequestError`; it does not receive or echo the requested capability or improvise a fallback. No prompt assembly, runtime invocation, stream forwarding, or other P01.10 behavior exists yet.

## What Does Not Exist Yet

The following are **not implemented** yet:

- application-owned harness implementation;
- harness/API/browser integration of the `llama.cpp` adapter;
- end-to-end generation lifecycle/API streaming or cancellation;
- any registered model-callable tools;
- real-runtime smoke test;
- SQLite database or durable persistence;
- Personas or conversations;
- knowledge, retrieval, research, web research, memory, multimodal, or observation features.

Later-phase features are intentionally absent and should remain absent until their approved phase.

## Current Verification

The local API/web shell is runnable. The automated suite contains 115 deterministic foundation, web-shell, trust-perimeter, runtime-domain, runtime-contract, mocked-runtime-adapter, tool-boundary, health-route, settings, and startup test cases.

The initial `pyproject.toml` metadata has been checked with TOML-aware IDE inspection and `git diff --check`.

The P01.01.02 package/test directory structure has been checked for the required paths, absence of feature scaffolding, Python-file inspection errors, and whitespace errors.

The project-local PyCharm interpreter has been verified as Python 3.14.7 with `pip` available, matching `pyproject.toml`; the Phase 1 boundary packages import successfully with that interpreter.

The root ignore policy has been checked against representative local environment, cache, secret, database, model, log, and editor artifacts while preserving project source files.

The P01.03 web-foundation checkpoint passed **14 tests**. The P01.04 trust-perimeter checkpoint passed **39 tests**. The focused P01.05–P01.07 runtime checks passed **27 tests**, and the complete deterministic suite passed **66 tests** with Python 3.14.7, FastAPI 0.141.1, Jinja2 3.1.6, Uvicorn 0.52.4, HTTPX 0.28.1, and pytest 9.1.1. The current real local startup path was exercised: Uvicorn bound to `127.0.0.1:8000`, `GET /` returned the Jinja2 shell with HTTP 200 and local asset references, and the process shut down cleanly. The process-only `GET /health` path remains covered by deterministic API tests. The verified environment-setup, run, health-check, and test commands are recorded in `docs/project/DEVELOPMENT.md`.

The repaired P01.08 adapter checkpoint passed **23 focused mocked-transport tests** covering the reusable runtime contract, capability probing, adapter-internal request/stream translation, malformed streams including a non-object nested `delta`, HTTP failure, disconnect, cancellation, direct remote-endpoint rejection, and no fallback/model substitution. The complete deterministic offline suite passed **101 tests** with the existing verified environment. No real `llama.cpp` process was required or used; the opt-in real-runtime proof remains P01.17.

The repaired P01.09 capability-boundary checkpoint passed **37 focused adapter and tool-boundary tests**. They prove the registry and harness-facing description surface are empty, a production `llama.cpp` structured tool request becomes a bounded application-owned marker rather than disappearing or completing normally, the harness-owned boundary rejects that marker with a static unsupported-tool failure, all contract-required forbidden capability families are absent, and no generic registration/invocation API exists. The complete deterministic offline suite passed **115 tests** with the existing verified environment.

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
