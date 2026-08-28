# Phase 01 — Workspace Foundation and Local Harness

**Contract status:** Approved — active implementation contract  
**Authority:** `docs/project/Architecture.md` remains canonical. This document refines Phase 1 only and may not weaken or contradict an invariant or requirement in `docs/project/Architecture.md`.  
**Roadmap position:** Phase 1 of 11  
**Starts from:** Documentation-only repository; no application implementation  
**Next phase:** Phase 2 — Personas, Conversations, and Model Controls

---

## 1. Phase Outcome

Phase 1 establishes the smallest trustworthy vertical slice of Sampo:

> A local Python/FastAPI web application with a Jinja2/Alpine.js UI shell that can send one ephemeral user prompt through an application-owned harness to a local `llama.cpp` runtime, stream the response back to the browser, cancel the active generation truthfully, and expose no model-facing host tools or action capabilities.

This phase exists to prove the product's core boundaries before durable Personas, conversations, knowledge, research, memory, or richer model controls are added.

The Phase 1 roadmap outcome is taken directly from `docs/project/Architecture.md` §30:

- Python/FastAPI application shell;
- Jinja2/Alpine.js UI foundation;
- loopback/local-web trust perimeter;
- backend boundary;
- application-owned harness;
- `llama.cpp` runtime adapter;
- streaming/cancellation lifecycle;
- explicit empty/narrow tool surface.

---

## 2. Architectural Rules This Phase Must Preserve

Phase 1 must establish these rules structurally rather than relying on prompts or model obedience.

### 2.1 Application-owned orchestration

The application owns the harness. No third-party agent framework becomes a product boundary or permanent orchestration dependency. The harness is responsible only for model-facing orchestration (`docs/project/Architecture.md` §§4.1, 6.3, 25.1).

### 2.2 Read-oriented capability boundary

The model-facing surface must not expose generic filesystem access, shell/process execution, code execution, Git/VCS, package installation, arbitrary network access, browser automation, IDE/Godot control, or dynamic tool/plugin loading (`docs/project/Architecture.md` §§4.2, 13, 27, 29).

Phase 1 has **zero model-callable tools throughout this phase**. The harness/tool boundary must exist, but the registered tool set remains empty. Any unexpected model tool request fails closed.

### 2.3 Local-only operation

The application and inference runtime are local-only. The configured runtime endpoint must resolve to the same machine through an approved loopback/local IPC boundary. No remote/cloud model fallback is permitted (`docs/project/Architecture.md` §§4.3, 20.4).

### 2.4 Stable backend boundary

The browser talks to the Sampo backend API. Browser code must not depend directly on `llama.cpp` transport details, and application code outside the runtime adapter must use application-owned request/event types (`docs/project/Architecture.md` §§5, 20.2).

### 2.5 Local web trust perimeter

The normal web server binds to loopback only. Required frontend assets are local. Browser-facing state-changing endpoints and streaming endpoints must reject unrelated origins/hosts. Untrusted output must be rendered as data rather than executable HTML (`docs/project/Architecture.md` §§4.10, 27, 28.14).

### 2.6 Truthful lifecycle and cancellation

A generation has an explicit lifecycle. Cancellation must reach the runtime and must stop further work for that turn. Runtime failure or cancellation must never be surfaced as normal completion (`docs/project/Architecture.md` §§8.6, 20.4, 28.13).

### 2.7 Lightweight default

Prefer one Sampo application process plus the local `llama.cpp` runtime. Do not introduce a message broker, workflow engine, vector database, container fleet, scheduler, extra model service, or heavyweight SPA framework (`docs/project/Architecture.md` §§4.9, 24).

---

## 3. In Scope

Phase 1 implements only the foundations required to prove the Phase 1 vertical slice.

### Application shell

- Python project/package setup.
- FastAPI application factory and startup path.
- Jinja2 templates.
- Alpine.js served locally by Sampo.
- Local CSS/static-asset pipeline simple enough to run without a frontend build system unless one is demonstrably necessary.
- Health/readiness information sufficient to distinguish Sampo health from local model-runtime availability.

### Local trust perimeter

- Loopback-only default binding.
- Trusted-host validation for the local service.
- Same-origin protection for browser-facing mutation/cancellation requests.
- A simple application-owned anti-CSRF mechanism for state-changing requests.
- No permissive CORS configuration.
- No remote assets, telemetry, analytics, crash uploads, or background outbound calls.

### Backend/runtime boundary

- Application-owned model request types.
- Application-owned stream event types.
- Application-owned runtime capability type.
- `ModelRuntime` protocol/interface.
- Test/fake runtime implementation.
- First `llama.cpp` runtime adapter.
- Local-only endpoint validation.
- Runtime availability/error mapping.
- Runtime cancellation.

### Minimal application-owned harness

- Minimal trusted application policy input.
- Bounded prompt/context assembly for the current ephemeral request.
- Runtime invocation through `ModelRuntime` only.
- Stream event forwarding/normalization.
- Explicit empty model-tool registry.
- Fail-closed handling of unexpected tool requests.
- Cancellation propagation.

### Ephemeral generation lifecycle

Phase 1 may keep active generation state in memory. It needs enough lifecycle state to prove streaming and cancellation:

- `created`;
- `streaming`;
- `completed`;
- `stopped`;
- `failed`.

Durable conversation/message persistence is Phase 2.

### Minimal browser interaction

- One prompt input.
- One submit action.
- Streamed assistant text.
- Visible current lifecycle state.
- Stop Generation while active.
- Visible runtime/configuration failure.
- Safe rendering of model output as inert text/data.

### Tests

- Unit tests for boundaries and lifecycle behavior.
- API tests for localhost trust controls.
- Harness tests against the fake runtime.
- Runtime-adapter tests with deterministic mocked transport.
- One opt-in smoke test against a real local `llama.cpp` runtime.

---

## 4. Explicitly Out of Scope

These features belong to later phases and should **not** be pulled into Phase 1 merely to make the demo feel more complete.

### Deferred to Phase 2

- Persona CRUD or Persona persistence.
- Multiple durable chats.
- Durable messages/history.
- Chat ownership/re-parenting rules in storage.
- Model presets.
- User-facing model selection/override UI.
- Generation/sampling control UI.
- Durable effective-configuration provenance.
- Edit-message and regenerate semantics.
- Durable emitted Thinking storage/UI.

### Deferred to Phase 3+

- Knowledge collections, sources, grants, ingestion, or indexes.
- SQLite FTS5 retrieval.
- Project resolution/version-aware retrieval.
- Research runs, research traces, citations, or tool loops.
- Web search/fetch.
- Persona memory.
- Image/vision attachments.
- Rider/Godot observations.

### Not part of the current architecture

Do not add generic model-facing host capabilities, autonomous actions, cloud LLM providers, plugin ecosystems that expand host authority, LAN/public deployment, background agents, telemetry, or paid-service dependencies.

---

## 5. Phase-Level Implementation Decisions

These are implementation choices for Phase 1, not changes to `docs/project/Architecture.md`.

### 5.1 Repository shape

Use the architecture's preferred responsibility boundaries, while creating only the packages Phase 1 needs immediately:

```text
/
├── AGENTS.md
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   ├── web/
│   │   ├── templates/
│   │   └── static/
│   ├── workspace/
│   ├── harness/
│   └── model_runtime/
├── tests/
└── docs/
    ├── project/
    │   ├── Architecture.md
    │   ├── STATUS.md
    │   ├── DEVELOPMENT.md
    │   ├── implementation/
    │   │   └── Phase-01-Workspace-Foundation-and-Local-Harness.md
    │   └── adr/
    └── human/
        ├── notes/
        └── designs/
```

Do not create empty future subsystem packages merely to mirror the end-state tree. Add `knowledge/`, `research/`, `memory/`, and `observations/` when their phases begin.

### 5.2 Configuration

Phase 1 configuration is local application configuration, not Persona/model-preset configuration.

It should cover only what Phase 1 needs, for example:

- Sampo bind host;
- Sampo bind port;
- `llama.cpp` local endpoint/process mode required by the chosen adapter;
- default Phase 1 model identifier if required by the runtime transport;
- practical request/stream timeout limits.

Configuration must fail visibly when invalid. A remote model endpoint is rejected rather than silently used.

### 5.3 Runtime contract

Application code should depend on a narrow interface conceptually equivalent to:

```
python
class ModelRuntime(Protocol):
    async def get_capabilities(self) -> RuntimeCapabilities: ...
    async def stream_chat(self, request: ModelRequest) -> AsyncIterator[ModelEvent]: ...
    async def abort(self, request_id: str) -> None: ...
```

Phase 1 does not need speculative multi-provider machinery. `llama.cpp` is the only production adapter.

### 5.4 Model request

The Phase 1 request should contain only application-owned fields required for the minimal vertical slice, such as:

- application request ID;
- current user text;
- minimal trusted application/system instruction;
- configured local model identity if required;
- bounded generation options required for a safe smoke path.

Do not introduce Persona IDs, conversation IDs, knowledge scopes, memory, research policy, or attachments yet.

### 5.5 Stream events

Normalize runtime transport into a small application event vocabulary. At minimum:

- `generation.started`;
- `generation.delta`;
- `generation.completed`;
- `generation.stopped`;
- `generation.failed`.

The adapter may internally receive runtime-specific events, but those schemas must not leak through the rest of Sampo.

### 5.6 Tool surface

The Phase 1 tool registry is explicit and empty:

```text
registered model tools = []
```

If `llama.cpp`/the selected model emits a tool request anyway, the harness rejects it as unsupported and records/returns a bounded failure. It must not improvise an alternative capability.

### 5.7 Generation API

Use a small application-owned API. Concrete route names may be adjusted during implementation only if the same boundary and behavior are preserved.

Recommended contract:

```text
POST /api/generations
  input:  { "prompt": "..." }
  output: { "generation_id": "..." }

GET /api/generations/{generation_id}/events
  output: text/event-stream

POST /api/generations/{generation_id}/cancel
  output: current generation status

GET /api/generations/{generation_id}
  output: current generation status/error summary
```

The generation is ephemeral and process-local in Phase 1. The backend generation service owns a **bounded** in-memory event channel/buffer so model output cannot accumulate without limit between runtime production and SSE consumption. Refreshing/restarting Sampo may discard generation state. Durable generation/message records arrive in Phase 2.

### 5.8 Streaming

SSE is the default transport for server-to-browser generation events, consistent with `docs/project/Architecture.md` §24. WebSockets should not be introduced in Phase 1 unless an actual requirement cannot be satisfied with HTTP + SSE.

### 5.9 Browser security

Use a simple defense-in-depth local-web policy:

1. bind only to approved loopback interfaces;
2. accept only approved local `Host` values;
3. do not enable permissive CORS;
4. validate `Origin` on browser mutation/cancellation requests;
5. require an application-issued CSRF token on state-changing browser requests;
6. apply the same trust policy to streaming endpoints;
7. render model output with safe text/DOM APIs, never by inserting untrusted raw HTML.

The exact middleware/function names are implementation details. Tests define the contract.

---

## 6. Dependency Map

```text
P01.01 Project skeleton
   ↓
P01.02 FastAPI shell
   ↓
P01.03 Local web shell ─────────────┐
   ↓                                │
P01.04 Local trust perimeter        │
                                    │
P01.05 Runtime domain types         │
   ↓                                │
P01.06 ModelRuntime interface       │
   ↓                                │
P01.07 Fake runtime                 │
   ↓                                │
P01.08 llama.cpp adapter            │
   ↓                                │
P01.09 Empty tool boundary          │
   ↓                                │
P01.10 Minimal harness              │
   ↓                                │
P01.11 Generation lifecycle         │
   ↓                                │
P01.12 Generation API + SSE  ◀──────┘
   ↓
P01.13 Cancellation
   ↓
P01.14 Minimal browser chat slice
   ↓
P01.15 Failure + safe rendering
   ↓
P01.16 Boundary/security regression tests
   ↓
P01.17 Real llama.cpp smoke path
   ↓
P01.18 Phase acceptance + handoff
```

Each numbered work package below is deliberately split further into review-sized tasks.

---

## 7. Review-Sized Implementation To-Do List

### Review rule

Each checkbox should be implementable and reviewable as one small change. Prefer one observable behavior per change. Avoid combining infrastructure, UI, runtime integration, and security changes in the same review unless they are inseparable.

Execution batching does not merge checkbox scope. Multiple checkboxes may be executed sequentially within one Approved Phase Execution Mode run, but each checkbox remains an independently satisfiable, testable, and reviewable change unit. Completing one checkbox does not require ending the Codex execution session.
A task is complete only when its focused tests pass and the reviewer can explain what changed without needing to understand unfinished later tasks.

---

### P01.01 — Project skeleton

- [x] **P01.01.01 — Add `pyproject.toml` with the minimum Python project metadata.** Keep production dependencies limited to what the current task needs.
- [x] **P01.01.02 — Add the `app` package and `tests` directory.** No feature logic yet.
- [x] **P01.01.03 — Add responsibility-boundary packages needed by Phase 1:** `api`, `web`, `workspace`, `harness`, and `model_runtime`.
- [x] **P01.01.04 — Add the test runner configuration and one trivial import test.** This proves the package/test layout works before feature code is added.
- [x] **P01.01.05 — Update `docs/project/DEVELOPMENT.md` with the first verified Phase 1 setup/test commands.** Document only commands that have actually been executed successfully; do not duplicate them into another runbook.

**Review checkpoint:** repository imports cleanly; tests run; no application behavior exists yet.

---

### P01.02 — FastAPI application shell

- [x] **P01.02.01 — Add an application factory.** Construct FastAPI in one backend-owned location.
- [x] **P01.02.02 — Add `GET /health`.** Return only Sampo process health; do not yet claim the model runtime is healthy.
- [x] **P01.02.03 — Add a typed application settings object.** Start with bind host/port only.
- [x] **P01.02.04 — Default the bind host to loopback.** Add a focused configuration test.
- [x] **P01.02.05 — Reject unsupported non-loopback bind configuration.** Treat LAN/public exposure as outside the current architecture rather than as an undocumented option.
- [x] **P01.02.06 — Add a runnable local server startup path.** Use validated settings and verify Sampo process health over loopback.

**Review checkpoint:** Sampo can start locally and reports its own health without any model runtime.

---

### P01.03 — Jinja2/Alpine.js local web foundation

- [x] **P01.03.01 — Add Jinja2 template support and a minimal base template.** No chat behavior yet.
- [x] **P01.03.02 — Add `GET /` rendering the Sampo shell.** Keep the page intentionally sparse.
- [x] **P01.03.03 — Add local static-file serving.** Include one local CSS file.
- [x] **P01.03.04 — Vendor/serve Alpine.js locally.** Do not reference a CDN.
- [x] **P01.03.05 — Add a test proving the page references only local required assets.**

**Review checkpoint:** browser shell loads entirely from the local Sampo service with JavaScript disabled or enabled.

---

### P01.04 — Local web/API trust perimeter

- [x] **P01.04.01 — Add trusted-host validation for loopback/local hostnames.** Test allowed and rejected `Host` headers.
- [x] **P01.04.02 — Add same-origin validation helper for browser requests.** Keep it independent of generation code.
- [x] **P01.04.03 — Add an application-issued CSRF token to the rendered page.** Token is backend-owned and never model-facing.
- [x] **P01.04.04 — Add CSRF validation for state-changing `/api/*` requests.** Test missing/invalid/valid token cases.
- [x] **P01.04.05 — Confirm no permissive CORS middleware/configuration exists.** Add a regression test for unrelated origins.
- [ ] **P01.04.06 — Apply the same host/origin policy to SSE endpoints.** Add a focused streaming-origin test once the test endpoint exists; this checkbox may initially land as middleware coverage and be closed after P01.12.

**Review checkpoint:** an unrelated web origin cannot freely drive Sampo's browser-facing control plane.

---

### P01.05 — Runtime domain types

- [x] **P01.05.01 — Add `RuntimeCapabilities`.** Include only Phase 1 facts needed to describe text-chat/streaming support and runtime availability.
- [x] **P01.05.02 — Add `ModelRequest`.** Keep Persona/conversation/research fields out.
- [x] **P01.05.03 — Add application-owned model stream event types.** Start with started/delta/completed/stopped/failed.
- [x] **P01.05.04 — Add a bounded runtime error taxonomy.** Distinguish unavailable, invalid configuration, incompatible capability, cancelled, and runtime failure where practical.
- [x] **P01.05.05 — Unit-test construction/validation of these types.**

**Review checkpoint:** the rest of Sampo can describe model interaction without importing a `llama.cpp` transport schema.

---

### P01.06 — `ModelRuntime` boundary

- [x] **P01.06.01 — Define the `ModelRuntime` protocol/interface.** Include capabilities, streaming, and abort.
- [x] **P01.06.02 — Make runtime selection/injection occur at application composition time.** Do not use global transport state.
- [x] **P01.06.03 — Add a contract test scaffold that any runtime adapter can run against.**

**Review checkpoint:** harness/API code can depend on `ModelRuntime` without knowing about `llama.cpp` HTTP/process details.

---

### P01.07 — Deterministic fake runtime

- [x] **P01.07.01 — Add `FakeModelRuntime` that streams deterministic text chunks.**
- [x] **P01.07.02 — Add configurable fake-runtime delay/gating for cancellation tests.** Keep tests deterministic; do not use arbitrary long sleeps.
- [x] **P01.07.03 — Add fake-runtime failure injection.** Allow a test to produce a known runtime failure.
- [x] **P01.07.04 — Add fake-runtime abort tracking.** Tests must be able to prove `abort(request_id)` was called.
- [x] **P01.07.05 — Run the runtime contract tests against the fake runtime.**

**Review checkpoint:** the complete Phase 1 application can be developed/tested offline without `llama.cpp` running.

---

### P01.08 — First `llama.cpp` adapter

- [x] **P01.08.01 — Add Phase 1 runtime endpoint/model configuration.** Keep it backend-only.
- [x] **P01.08.02 — Validate that configured runtime transport is same-machine/loopback only.** Reject remote hosts explicitly.
- [x] **P01.08.03 — Implement runtime availability/capability probing through the adapter.** Normalize results into `RuntimeCapabilities`.
- [x] **P01.08.04 — Implement request translation from `ModelRequest` to the selected `llama.cpp` transport.** Keep translation inside the adapter.
- [x] **P01.08.05 — Implement streamed response translation into `ModelEvent` values.** Do not leak transport-specific chunks upward.
- [x] **P01.08.06 — Implement adapter abort/cancellation.** Tie cancellation to the Sampo request ID.
- [x] **P01.08.07 — Normalize runtime connection/HTTP/protocol errors into the Phase 1 error taxonomy.**
- [x] **P01.08.08 — Add mocked-transport tests for success, malformed stream, disconnect, and cancellation.**
- [x] **P01.08.09 — Add a test proving no remote/cloud fallback occurs after adapter failure.**

**Review checkpoint:** `llama.cpp` is isolated behind one production adapter and failures remain explicit.

---

### P01.09 — Explicit empty tool boundary

- [ ] **P01.09.01 — Add an application-owned tool registry abstraction with no registered tools.** Avoid generic callables that could become accidental host capabilities.
- [ ] **P01.09.02 — Make the harness receive the current tool descriptions from that registry.** Phase 1 result must be an empty tool list.
- [ ] **P01.09.03 — Add fail-closed handling for an unexpected model tool request.** No fallback to filesystem/network/process helpers.
- [ ] **P01.09.04 — Add a security regression test asserting the Phase 1 model-facing tool surface is empty.**
- [ ] **P01.09.05 — Add tests asserting forbidden generic capability names/types are not registered.** Cover filesystem, shell/process, code execution, Git, package install, arbitrary network/browser, dynamic plugins, and IDE/Godot control.

**Review checkpoint:** capability absence is a property of the application structure, not a prompt instruction.

---

### P01.10 — Minimal application-owned harness

- [ ] **P01.10.01 — Add a harness request type containing only the current Phase 1 user prompt/request ID.**
- [ ] **P01.10.02 — Add minimal trusted application policy text/configuration as a backend-owned input.** Do not pretend a Phase 1 Persona exists.
- [ ] **P01.10.03 — Add deterministic context assembly for application policy + current user prompt.** Enforce a simple input-size bound.
- [ ] **P01.10.04 — Invoke the injected `ModelRuntime`; do not call `llama.cpp` transport from the harness directly.**
- [ ] **P01.10.05 — Forward normalized streaming deltas to the caller.**
- [ ] **P01.10.06 — Translate runtime failure/cancellation into truthful terminal harness events.**
- [ ] **P01.10.07 — Add harness tests using only `FakeModelRuntime`.**

**Review checkpoint:** one prompt can traverse the application-owned harness without persistence, tools, research, or Persona state.

---

### P01.11 — Ephemeral generation lifecycle

- [ ] **P01.11.01 — Add a `GenerationState` model with explicit lifecycle statuses.**
- [ ] **P01.11.02 — Add an in-memory generation registry owned by the backend/workspace layer, not the harness.**
- [ ] **P01.11.03 — Generate opaque application-owned generation IDs.** Runtime IDs must not become browser capabilities directly.
- [ ] **P01.11.04 — Enforce valid lifecycle transitions.** Prevent terminal states from returning to streaming.
- [ ] **P01.11.05 — Store only bounded Phase 1 ephemeral status/error data.** Do not accidentally create a durable conversation model.
- [ ] **P01.11.06 — Add a bounded in-memory event channel/buffer for each active generation.** Define explicit behavior when the consumer cannot keep up; do not permit unbounded output accumulation.
- [ ] **P01.11.07 — Add lifecycle transition tests for completion, stop, and failure.**

**Review checkpoint:** Sampo—not the model runtime—owns the user-visible generation lifecycle.

---

### P01.12 — Generation API and SSE stream

- [ ] **P01.12.01 — Add `POST /api/generations`.** Validate prompt size and create one generation ID.
- [ ] **P01.12.02 — Start harness execution through a backend-owned generation service.** Keep orchestration out of the route function.
- [ ] **P01.12.03 — Add `GET /api/generations/{id}` for status/error summary.**
- [ ] **P01.12.04 — Add `GET /api/generations/{id}/events` using SSE.** Emit application-owned event names/data only.
- [ ] **P01.12.05 — Send a terminal SSE event for completed/stopped/failed states.** Do not make clients infer completion from socket closure alone.
- [ ] **P01.12.06 — Bound event payload size and reject/handle unknown generation IDs explicitly.**
- [ ] **P01.12.07 — Add API tests with `FakeModelRuntime` for a complete streamed generation.**
- [ ] **P01.12.08 — Define and test SSE disconnect behavior.** In Phase 1, losing the owning browser stream should cancel the still-active ephemeral generation rather than leaving hidden work running indefinitely.
- [ ] **P01.12.09 — Close P01.04.06 by testing host/origin policy on the real SSE route.**

**Review checkpoint:** the browser/API can observe a complete fake-runtime generation without any `llama.cpp` dependency.

---

### P01.13 — End-to-end cancellation

- [ ] **P01.13.01 — Add `POST /api/generations/{id}/cancel`.** Require the same local-web protections as other state changes.
- [ ] **P01.13.02 — Add a backend cancellation signal/token owned by the generation service.**
- [ ] **P01.13.03 — Propagate cancellation into the harness.**
- [ ] **P01.13.04 — Propagate cancellation from the harness to `ModelRuntime.abort(request_id)`.**
- [ ] **P01.13.05 — Mark the generation `stopped`, not `completed`, after successful cancellation.**
- [ ] **P01.13.06 — Prevent post-cancellation runtime chunks from being forwarded as active output.**
- [ ] **P01.13.07 — Make repeated cancellation idempotent/safely terminal.**
- [ ] **P01.13.08 — Add deterministic API-level cancellation tests using the fake-runtime gate.**
- [ ] **P01.13.09 — Add a test proving no hidden generation task continues after terminal stop.**

**Review checkpoint:** Stop Generation has a mechanically testable effect all the way down to the runtime boundary.

---

### P01.14 — Minimal browser chat slice

- [ ] **P01.14.01 — Add a prompt textarea and Send button to the Phase 1 page.**
- [ ] **P01.14.02 — Add a small Alpine component for generation UI state.** Keep transport code narrow.
- [ ] **P01.14.03 — Submit the prompt to the Sampo generation API with the CSRF token.**
- [ ] **P01.14.04 — Subscribe to the generation SSE stream.**
- [ ] **P01.14.05 — Append streamed text as inert text content.** Do not use unsafe raw-HTML insertion.
- [ ] **P01.14.06 — Display `streaming/completed/stopped/failed` status explicitly.**
- [ ] **P01.14.07 — Add Stop Generation while a generation is active.**
- [ ] **P01.14.08 — Disable or otherwise prevent overlapping sends in this Phase 1 single-generation UI.** Concurrency expansion can be considered with durable conversations later.

**Review checkpoint:** a human can exercise the full fake-runtime vertical slice in the browser and understand whether it completed, stopped, or failed.

---

### P01.15 — Failure truthfulness and safe rendering

- [ ] **P01.15.01 — Surface missing/unavailable local runtime as an explicit UI error.** Do not claim a model response was generated.
- [ ] **P01.15.02 — Surface incompatible runtime capability as an explicit error.**
- [ ] **P01.15.03 — Surface mid-stream runtime failure as `failed` while retaining already visible partial text as incomplete.**
- [ ] **P01.15.04 — Add hostile model-output fixture containing `<script>`, event handlers, and HTML.** Prove it renders inertly.
- [ ] **P01.15.05 — Add a hostile error-string/filename-like fixture if such strings are displayed.** Prove UI escaping is consistent for all untrusted runtime text.
- [ ] **P01.15.06 — Ensure operational logs do not log secrets and avoid raw prompt/output content by default.** Add focused tests where practical.

**Review checkpoint:** failure is visible and untrusted runtime/model text cannot become active browser content.

---

### P01.16 — Phase 1 security/boundary regression suite

- [ ] **P01.16.01 — Add a test proving default application configuration is loopback-only.**
- [ ] **P01.16.02 — Add a test proving a remote model-runtime URL/configuration is rejected.**
- [ ] **P01.16.03 — Add a test proving unrelated browser origins cannot invoke state-changing APIs.**
- [ ] **P01.16.04 — Add a test proving invalid local-web hosts are rejected.**
- [ ] **P01.16.05 — Add a test proving required frontend assets do not rely on third-party CDNs.**
- [ ] **P01.16.06 — Add a test proving model-facing tools remain empty.**
- [ ] **P01.16.07 — Add a test proving an unexpected tool request fails closed.**
- [ ] **P01.16.08 — Add a test proving runtime failure does not select a different/remote model automatically.**
- [ ] **P01.16.09 — Add a test proving cancellation produces `stopped` and terminates work.**
- [ ] **P01.16.10 — Add a test proving unsafe model HTML is not executed/rendered as trusted markup.**

**Review checkpoint:** the permanent safety boundaries relevant to Phase 1 have automated regression coverage before future capability surfaces are added.

---

### P01.17 — Real local `llama.cpp` smoke path

Keep this separate from the deterministic default test suite.

- [ ] **P01.17.01 — Document the exact supported Phase 1 `llama.cpp` launch/connection assumptions.** This is the concrete transport choice deferred by `docs/project/Architecture.md` §32.
- [ ] **P01.17.02 — Add an opt-in runtime connectivity smoke test.** Skip cleanly when no local runtime is configured.
- [ ] **P01.17.03 — Verify a real local prompt streams through the adapter and harness.**
- [ ] **P01.17.04 — Verify Stop Generation reaches the real local runtime path.** If the runtime transport cannot provide truthful cancellation, Phase 1 is not accepted until the integration is changed or the architectural conflict is presented to the user.
- [ ] **P01.17.05 — Verify disconnect/crash produces a visible failed generation with no fallback.**

**Review checkpoint:** the deterministic test architecture has been proven against the first real runtime without bypassing the adapter/harness boundaries.

---

### P01.18 — Documentation, cleanup, and handoff

- [ ] **P01.18.01 — Finalize `docs/project/DEVELOPMENT.md` with verified local run instructions for Sampo + local `llama.cpp`.** If a `README.md` exists, it should link to `docs/project/DEVELOPMENT.md` rather than duplicate the commands.
- [ ] **P01.18.02 — If a human-facing module-boundary explanation is useful, place it under `docs/human/notes/`.** It is explanatory and non-authoritative; do not duplicate or redefine `docs/project/Architecture.md` or the active phase contract.
- [ ] **P01.18.03 — Remove unused dependencies, dead scaffolding, and temporary debug endpoints.**
- [ ] **P01.18.04 — Run the complete deterministic test suite offline.** Internet access must not be required.
- [ ] **P01.18.05 — Run the real-runtime smoke checklist.**
- [ ] **P01.18.06 — Review every Phase 1 acceptance criterion below and record any accepted implementation deviation in the appropriate ADR and/or `docs/project/STATUS.md`.** No deviation may weaken an architectural invariant or requirement.
- [ ] **P01.18.07 — Do not begin substantial Phase 2 implementation until Phase 1 is accepted or the user explicitly authorizes overlap.**

---

## 8. Suggested Human Review Rhythm

For implementation work, use these checkpoints rather than reviewing the entire phase as one change:

1. **Foundation:** P01.01–P01.03
2. **Local trust perimeter:** P01.04
3. **Runtime abstractions:** P01.05–P01.07
4. **Real runtime adapter:** P01.08
5. **Capability boundary:** P01.09
6. **Harness:** P01.10
7. **Lifecycle/API:** P01.11–P01.12
8. **Cancellation:** P01.13
9. **Browser slice:** P01.14–P01.15
10. **Regression suite:** P01.16
11. **Real-runtime proof:** P01.17
12. **Phase closure:** P01.18

A review should normally stop at the checkpoint boundary if a concern is found. Avoid layering later work on top of a disputed boundary.

These are review boundaries, not mandatory Codex-session boundaries. An Approved Phase Execution Mode run may continue across multiple review checkpoints when the required checkpoint verification passes and no concern or stop condition is present.

---

## 9. Phase 1 Acceptance Criteria

Phase 1 is complete only when all of the following are true.

### Application and UI

- [ ] Sampo starts as a Python/FastAPI local web application from a clean checkout/environment using documented steps.
- [ ] The default server binding is loopback-only, and unsupported non-loopback configuration is rejected.
- [ ] `GET /` serves a Jinja2-based UI shell using Alpine.js and required assets hosted locally by Sampo.
- [ ] The Phase 1 UI can submit one ephemeral prompt, display streamed output, display terminal status, and stop an active generation.

### Backend and runtime boundaries

- [ ] Browser code communicates only with Sampo's application API, not directly with `llama.cpp`.
- [ ] Application code outside `app/model_runtime` does not depend on `llama.cpp` transport schemas.
- [ ] `llama.cpp` is the only production model-runtime adapter in Phase 1.
- [ ] Remote/cloud model endpoints are rejected and no cloud fallback exists.
- [ ] Runtime unavailability, incompatibility, malformed output, or crash is surfaced explicitly.

### Harness

- [ ] The application-owned harness assembles a bounded Phase 1 request and invokes the runtime only through `ModelRuntime`.
- [ ] The Phase 1 registered model-tool surface is explicitly empty.
- [ ] Unexpected model tool requests fail closed with no broader fallback capability.
- [ ] No generic model-facing filesystem, shell/process, code execution, Git, package-management, arbitrary-network, browser, plugin, IDE, or Godot capability exists.

### Streaming and cancellation

- [ ] Model output streams from fake runtime → adapter boundary → harness → backend API → browser using application-owned event types.
- [ ] A generation ends in exactly one truthful terminal state: `completed`, `stopped`, or `failed`.
- [ ] Stop Generation propagates to the owning runtime request.
- [ ] No further active generation output/tool work continues after Sampo reports the generation stopped.
- [ ] Partial output from a stopped/failed generation remains visibly incomplete rather than being presented as normal completion.

### Local web security/privacy

- [ ] Host validation and origin/CSRF-equivalent controls prevent unrelated browser origins from freely invoking the local control plane.
- [ ] Streaming endpoints follow the same local trust policy as other browser-facing API endpoints.
- [ ] Required frontend scripts/styles/assets do not depend on remote CDNs.
- [ ] Model/runtime strings are rendered as untrusted data and cannot execute active HTML/JavaScript.
- [ ] Phase 1 includes no telemetry, analytics, crash-report upload, or unrelated background outbound network behavior.

### Testability

- [ ] The default automated test suite runs deterministically without internet access and without a real model runtime.
- [ ] The fake runtime covers normal streaming, failure, and cancellation.
- [ ] The `llama.cpp` adapter has mocked transport tests.
- [ ] An opt-in smoke path demonstrates successful streaming and cancellation against a real local `llama.cpp` runtime.
- [ ] Security/capability-absence tests relevant to Phase 1 are present and passing.

### Scope discipline

- [ ] Phase 1 does not contain premature Persona, durable conversation, knowledge, retrieval, research, web-research, memory, multimodal, or observation implementations.
- [ ] Any implementation decision that appears to require weakening an architectural invariant has been stopped and presented to the user rather than silently encoded in this phase.

---

## 10. Definition of Done for Each Small Task

A checkbox in Section 7 is done when:

1. the change implements one narrow behavior or boundary;
2. focused automated tests exist where the behavior is testable;
3. the relevant tests pass;
4. no unrelated refactor or future-phase feature is bundled into the same change;
5. public/internal interfaces introduced by the task are small enough to explain during review;
6. errors fail visibly rather than silently broadening capability or substituting behavior;
7. `docs/project/Architecture.md` remains satisfied.

---

## 11. Phase 2 Handoff

Phase 1 deliberately leaves the application with an ephemeral single-generation experience. That is acceptable.

Phase 2 can then build durable user-facing product semantics on top of already-proven boundaries:

- Persona persistence/configuration;
- multiple Persona-owned conversations;
- durable message/generation records;
- effective model/model-preset and generation-setting provenance;
- model presets and per-conversation overrides;
- emitted Thinking presentation/persistence when supported;
- linear message editing and regeneration.

The Phase 2 implementation should reuse the Phase 1 runtime, harness, lifecycle, cancellation, local-web security, and API boundary rather than bypassing them.

---

## 12. Architecture Traceability Map

| Phase 1 concern | Primary `docs/project/Architecture.md` sections |
| --- | --- |
| Application-owned harness | §§4.1, 6.3 |
| Read-only/capability absence | §§4.2, 13, 27, 28.1, 29 |
| Local-only model/runtime | §§4.3, 20.1–20.4 |
| Frontend/backend separation | §§5, 6.1–6.2 |
| Runtime abstraction | §§6.4, 20.2–20.4 |
| Turn lifecycle/cancellation | §8.6, §20.4, §28.13 |
| Local web trust perimeter | §4.10, §27, §28.14 |
| Lightweight stack | §§4.9, 24 |
| Repository boundaries | §25 |
| Phase sequencing/outcome | §30 |
| Deferred implementation choices | §32 |

---

## 13. Phase Contract Rule

If implementation reality reveals that this Phase 1 contract cannot be completed without contradicting `docs/project/Architecture.md`, stop that implementation path and present the conflict for explicit architectural approval. Do not solve the conflict by silently broadening runtime authority, adding a cloud fallback, exposing host capabilities, weakening localhost protections, or importing later-phase semantics into Phase 1.
