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
**Phase 1 implementation status:** P01.01–P01.16 complete, including the Phase 1 security/boundary regression review checkpoint. P01.17 is the next executable task.
**Runnable application:** Yes — local API and Phase 1 browser generation slice.
**Usable end-user functionality:** The browser can submit one ephemeral prompt, stream inert assistant text, display truthful terminal/failure state, and stop the active generation through the backend API when a configured local runtime is available.

Sampo is being designed exclusively for one trusted local end user on their own machine. No multi-user, LAN/public-hosting, remote-service, or enterprise deployment work exists or is currently required.

## What Exists

The project now contains its planning/development-governance documentation and initial Python project skeleton:

- `AGENTS.md` — repository-level development-agent instructions.
- `.gitignore` — excludes local environments, caches, secrets, databases, model files, logs, build output, and editor/OS artifacts.
- `pyproject.toml` — project metadata, bounded FastAPI/HTTPX/Jinja2/Uvicorn production dependencies, a separate pytest test dependency group, and pytest discovery configuration.
- `app/` — importable Python package with Phase 1 responsibility-boundary packages, a backend-owned FastAPI application factory, a process-only health route, a Jinja2/Alpine.js browser generation slice with local CSS/JavaScript assets, local-web trust middleware, application-owned runtime types/protocol, a deterministic fake runtime, a production `llama.cpp` adapter, a minimal application-owned harness, an explicit empty model-tool boundary, a bounded ephemeral generation lifecycle/service, application-owned generation/status/SSE/cancellation routes, validated loopback application/runtime settings, and a runnable module entry point.
- `tests/` — deterministic package-import, application-factory, health-route, settings, startup-composition, local-web/browser-slice, trust-perimeter, runtime-domain, runtime-protocol, runtime-contract, fake-runtime, mocked `llama.cpp` adapter, harness, tool-capability-boundary, generation-lifecycle, generation-API/SSE/cancellation, failure-truthfulness, safe-rendering, and logging tests.
- `docs/project/Architecture.md` — product architecture and roadmap.
- `docs/project/STATUS.md` — implementation-state record.
- `docs/project/DEVELOPMENT.md` — canonical operational guide.
- `docs/project/implementation/Phase-01-Workspace-Foundation-and-Local-Harness.md` — approved active Phase 1 implementation contract.
- `docs/human/` — reserved for non-authoritative human-facing notes/design material; no governing content lives there.

No ADRs exist yet because no significant implementation decision has required one.

A minimal FastAPI application factory and `GET /health` route exist. The route returns only `{"status": "ok"}` for Sampo process health; it does not report model-runtime availability. `GET /` renders the Phase 1 Jinja2 browser slice with a backend-issued CSRF token and only locally served CSS, narrow generation JavaScript, and vendored Alpine.js 3.16.3. Request middleware accepts only loopback/local hostnames, requires same-origin plus CSRF validation for state-changing `/api/*` requests, applies the same-origin policy to `/api/*/events` streams, and has no permissive CORS behavior.

Application-owned `RuntimeCapabilities`, `ModelRequest`, normalized started/delta/completed/stopped/failed event values, a bounded unexpected-tool-request marker, and a bounded runtime error taxonomy exist without `llama.cpp` transport fields. The `ModelRuntime` protocol defines capability probing, streaming, and abort; runtime injection is application-composition state rather than global transport state. `FakeModelRuntime` provides deterministic chunks, an event gate, known-failure injection, abort-call tracking, and mechanical gate release without a late chunk after abort, and passes the reusable runtime contract tests. A typed `ApplicationSettings` object defaults `bind_host` to `127.0.0.1`, requires an explicit bind port, accepts numeric loopback addresses, and rejects wildcard, LAN/public, and hostname bind values. Running `python -m app` starts the browser generation slice on `127.0.0.1:8000` with the configured local production runtime adapter.

`LlamaCppModelRuntime` is the only production model adapter. It uses an adapter-internal HTTPX transport for the local `llama.cpp` health and OpenAI-compatible streaming-chat endpoints, translates only between transport-private payload/chunk shapes and application-owned runtime values, validates the nested streamed-response shapes before accessing them, maps expected transport and malformed-protocol failures into the Phase 1 runtime error taxonomy, and aborts active transport responses by Sampo request ID. A non-empty structured `delta.tool_calls` response becomes only a bounded application-owned marker containing the Sampo request ID; the adapter ends that stream without normal completion and does not retain tool names or arguments above the transport boundary. Both application settings and direct adapter construction reject non-numeric, non-loopback, credential-bearing, path-bearing, and remote/cloud runtime endpoints. HTTPX environment proxy settings are disabled for adapter calls, and failures do not retry or select another model/provider. The runnable application composes the adapter with the application harness, ephemeral generation service, and browser generation slice.

The minimal `ApplicationHarness` accepts only an injected `ModelRuntime`, backend-owned `HarnessPolicy`, and existing `HarnessToolBoundary`. Its request contains only the Sampo request ID and current user prompt. Deterministic context assembly keeps policy and prompt separate and limits their combined text to 16,000 characters. The harness invokes the runtime through the application-owned protocol, forwards normalized stream events, maps runtime failure to `ModelFailed` and cancellation to `ModelStopped`, and maps the bounded unexpected-tool marker to a static failed event without normal completion. A backend-owned cancellation signal is passed into the harness per generation; the harness calls `ModelRuntime.abort()` with the internal request ID, prioritizes cancellation over a concurrently arriving runtime event, and stops forwarding runtime output. The runnable startup path composes this harness with `LlamaCppModelRuntime`; deterministic application/API tests inject `FakeModelRuntime` instead.

The workspace layer owns process-local `created`, `streaming`, `completed`, `stopped`, and `failed` generation state. Registration initially produces `created`, and backend execution transitions it to `streaming` when the generation task begins. Opaque browser generation IDs remain distinct from internal runtime request IDs; status/error retention is bounded; terminal transitions are one-way; and each generation has a fixed-capacity event channel. A full buffer fails the still-active generation with a bounded slow-consumer error and replaces buffered backlog with that terminal failure rather than accumulating output. The registry retains at most 128 ephemeral generations and evicts terminal entries when capacity is needed; it has no prompt, conversation, or durable persistence model.

`POST /api/generations` validates the Phase 1 prompt bound and starts execution through the backend-owned generation service. `GET /api/generations/{id}` returns only the application-owned status/error summary. `GET /api/generations/{id}/events` is a single-consumer SSE stream containing only bounded application-owned generation events and an explicit completed/stopped/failed terminal event. `POST /api/generations/{id}/cancel` uses the same trusted Host, same-origin, and CSRF protections as other browser mutations. It signals backend-owned cancellation, reaches runtime abort without exposing the internal runtime request ID, waits for terminal task shutdown, and returns `stopped`; repeat cancellation is safely terminal. Unknown IDs are explicit `404` responses. Closing the owning SSE iterator uses the same runtime-abort path rather than leaving hidden work active. The real SSE route enforces the same trusted Host and same-origin policy as the local control plane.

The browser slice has one bounded prompt textarea, Send and Stop Generation controls, and a small ephemeral Alpine component. It submits with the backend-issued CSRF token, subscribes only to the application-owned SSE route, prevents overlapping sends, and displays `streaming`, `completed`, `stopped`, and `failed` explicitly. Assistant output and error text bind only through `x-text`; no `x-html`, `innerHTML`, local/session storage, or browser-side persistence is used. Missing runtime, incompatible capability, mid-stream runtime failure, and stream disconnection are visible failures. Partial output remains visibly incomplete on failure. Application code has no prompt/output/secret logging path by default.

The application-owned `ToolRegistry` retains an immutable empty model-tool description set and no registration, invocation, dispatch, discovery, loading, or generic callable API. `HarnessToolBoundary` receives descriptions only from that registry and rejects the application-owned unexpected-tool marker with a static bounded `UnexpectedModelToolRequestError`; it does not receive or echo the requested capability or improvise a fallback.

## What Does Not Exist Yet

The following are **not implemented** yet:

- any registered model-callable tools;
- real-runtime smoke test;
- SQLite database or durable persistence;
- Personas or conversations;
- knowledge, retrieval, research, web research, memory, multimodal, or observation features.

Later-phase features are intentionally absent and should remain absent until their approved phase.

## Current Verification

The local API/browser slice is runnable. The automated suite contains 197 deterministic foundation, web-shell/browser-slice, safe-rendering, logging, trust-perimeter, runtime-domain, runtime-contract, mocked-runtime-adapter, harness, tool-boundary, generation-lifecycle, generation-API/SSE/cancellation/failure, health-route, settings, startup, and Phase 1 security-boundary test cases.

The initial `pyproject.toml` metadata has been checked with TOML-aware IDE inspection and `git diff --check`.

The P01.01.02 package/test directory structure has been checked for the required paths, absence of feature scaffolding, Python-file inspection errors, and whitespace errors.

The project-local PyCharm interpreter has been verified as Python 3.14.7 with `pip` available, matching `pyproject.toml`; the Phase 1 boundary packages import successfully with that interpreter.

The root ignore policy has been checked against representative local environment, cache, secret, database, model, log, and editor artifacts while preserving project source files.

The P01.03 web-foundation checkpoint passed **14 tests**. The P01.04 trust-perimeter checkpoint passed **39 tests**. The focused P01.05–P01.07 runtime checks passed **27 tests**, and the complete deterministic suite passed **66 tests** with Python 3.14.7, FastAPI 0.141.1, Jinja2 3.1.6, Uvicorn 0.52.4, HTTPX 0.28.1, and pytest 9.1.1. The current real local startup path was exercised: Uvicorn bound to `127.0.0.1:8000`, `GET /` returned the Jinja2 shell with HTTP 200 and local asset references, and the process shut down cleanly. The process-only `GET /health` path remains covered by deterministic API tests. The verified environment-setup, run, health-check, and test commands are recorded in `docs/project/DEVELOPMENT.md`.

The repaired P01.08 adapter checkpoint passed **23 focused mocked-transport tests** covering the reusable runtime contract, capability probing, adapter-internal request/stream translation, malformed streams including a non-object nested `delta`, HTTP failure, disconnect, cancellation, direct remote-endpoint rejection, and no fallback/model substitution. The complete deterministic offline suite passed **101 tests** with the existing verified environment. No real `llama.cpp` process was required or used; the opt-in real-runtime proof remains P01.17.

The repaired P01.09 capability-boundary checkpoint passed **37 focused adapter and tool-boundary tests**. They prove the registry and harness-facing description surface are empty, a production `llama.cpp` structured tool request becomes a bounded application-owned marker rather than disappearing or completing normally, the harness-owned boundary rejects that marker with a static unsupported-tool failure, all contract-required forbidden capability families are absent, and no generic registration/invocation API exists. The complete deterministic offline suite passed **115 tests** with the existing verified environment.

The P01.10 application-owned-harness checkpoint passed **42 focused harness, fake-runtime, runtime-protocol, and tool-boundary tests**. They prove one bounded prompt traverses only the injected `ModelRuntime`, policy remains separate from the user prompt, normalized streaming reaches the caller, runtime failure/cancellation become truthful terminal events, and unexpected tool requests remain fail-closed with an empty registry. The complete deterministic offline suite passed **134 tests** with the existing verified environment.

The repaired P01.11–P01.12 Lifecycle/API checkpoint passed **72 focused lifecycle, generation-API/SSE, local-web-security, harness, and startup tests**. The focused verification proves registration begins in `created`, backend execution transitions it to `streaming`, bounded ephemeral lifecycle/retention, opaque browser IDs distinct from runtime request IDs, valid terminal transitions and terminal-state protections, explicit slow-consumer failure, bounded event/SSE payloads, explicit unknown-ID handling, completed/stopped/failed terminal SSE events, owning-stream disconnect cleanup, the real SSE route's Host/origin policy, production startup composition, and the complete `FakeModelRuntime` → harness → backend generation service/API → application-owned SSE path. The complete deterministic offline suite passed **161 tests** with Python 3.14.7 and required no real `llama.cpp` process or internet access.

The P01.13 end-to-end cancellation checkpoint passed **45 focused fake-runtime, harness, and generation-API/SSE tests**. They prove the cancel route's trusted Host, same-origin, and CSRF controls; service-owned cancellation signaling; propagation through the harness to `ModelRuntime.abort()` using an internal request ID distinct from the browser generation ID; truthful `stopped` terminal state; suppression of a gate-released late runtime chunk and normal completion; safely repeated cancellation; owning-SSE disconnect runtime abort; and removal of the backend generation task after terminal stop. The complete deterministic offline suite passed **166 tests** with Python 3.14.7 and required no real `llama.cpp` process or internet access.

The P01.14–P01.15 browser-slice checkpoint passed **96 focused web-shell, generation-API/SSE, local-web-security, template, startup, harness, and tool-boundary tests**. They prove the local Alpine generation state, CSRF-protected prompt submission and cancellation, application-owned SSE subscription, explicit lifecycle states, overlap prevention, truthful unavailable/incompatible/mid-stream failures, partial-output retention, inert hostile model/error text, and default log exclusion of representative CSRF/prompt/output secrets. The focused web-shell suite passed **16 tests**, the focused generation API/SSE suite passed **20 tests**, and JavaScript syntax validation passed with Node.js 24.13.0. The complete deterministic offline suite passed **183 tests** with Python 3.14.7 and required no real `llama.cpp` process or internet access.

The P01.16 security/boundary regression checkpoint passed **15 focused tests** covering all ten permanent Phase 1 proofs, including the production adapter's explicit no-retry/no-remote-fallback case. The complete deterministic offline suite passed **197 tests** with Python 3.14.7 and required no real `llama.cpp` process or internet access. PyCharm inspection reported no errors or warnings in the new regression module apart from one weak duplicate-code observation, and `git diff --check` passed.

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
