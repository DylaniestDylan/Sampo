# DEVELOPMENT.md

## Purpose

`docs/project/DEVELOPMENT.md` is the canonical operational guide for **running, testing, and locally troubleshooting the Sampo implementation that actually exists**.

It is not an architecture specification and it is not a phase plan.

The documentation authority model is defined in `docs/project/Architecture.md` §1.1. This file owns operational procedures only.

Only document commands and procedures here once they actually work in the repository. Do not present planned commands as operational facts, and do not duplicate product requirements or phase scope here.

## Operating Context

Sampo is exclusively a **single-user local application** for one trusted user on their own machine.

Development and normal use therefore target the local machine and localhost/loopback interfaces. LAN/public deployment, remote hosting, multi-user operation, and enterprise administration are outside the current architecture.

Refer to `docs/project/Architecture.md` for the authoritative product and security requirements.

## Current Operational Availability

See `docs/project/STATUS.md` for the authoritative current implementation state.

The Phase 1 Python package skeleton, runnable FastAPI/Uvicorn browser generation slice, process-only health endpoint, numeric-loopback-validated bind/runtime settings, local-web trust controls, application-owned runtime boundary, deterministic fake runtime, production `llama.cpp` adapter, minimal application-owned harness, bounded ephemeral generation lifecycle, generation status/API/SSE/cancellation routes, and deterministic tests are available. The production startup path composes the adapter, harness, and backend generation service. The browser can submit one prompt, stream inert output, display truthful lifecycle/failure state, and stop the active generation.

## Prerequisites

The current verified development environment uses:

- Python 3.14.7, matching the minimum declared in `pyproject.toml`;
- pip 26.0.1;
- FastAPI 0.141.1 from the production dependency list;
- HTTPX 0.28.1 from the production dependency list;
- Jinja2 3.1.6 from the production dependency list;
- Uvicorn 0.52.4 from the production dependency list;
- pytest 9.1.1 from the `test` dependency group.

Commands below assume a Linux shell and are run from the repository root.

## Environment Setup

Create a project-local virtual environment and install the current production and test dependencies:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install "fastapi>=0.141,<0.142"
.venv/bin/python -m pip install "httpx>=0.28.1,<0.29"
.venv/bin/python -m pip install "jinja2>=3.1,<4"
.venv/bin/python -m pip install "uvicorn>=0.52,<0.53"
.venv/bin/python -m pip install --group test
```

Activating the virtual environment is optional because the documented commands invoke its interpreter explicitly. PyCharm can use `.venv/bin/python` as the project interpreter.

## Running Sampo

Start the local browser generation slice from the repository root:

```bash
.venv/bin/python -m app
```

The current startup path binds to `http://127.0.0.1:8000`. In another terminal, verify Sampo process health with:

```bash
curl --fail http://127.0.0.1:8000/health
```

The expected response is `{"status":"ok"}`. This reports only the Sampo process; it does not report model-runtime availability. Stop the server with Ctrl-C.


## Running the Local Model Runtime

**Current status:** The production adapter is implemented and deterministically tested, but the real-runtime launch/smoke path is intentionally deferred to P01.17.

The implemented backend configuration defaults to `http://127.0.0.1:8080` and model identity `local-model`. Runtime endpoints must use an explicit numeric loopback address and port; hostname, LAN, public, credential-bearing, and path-bearing URLs are rejected. No environment proxy or remote/cloud fallback is used.

When P01.17 verifies a working local `llama.cpp` runtime path, document here:

- the supported local runtime mode;
- the exact local startup/configuration procedure used by Sampo;
- how Sampo is pointed at the local runtime;
- how to verify runtime availability separately from Sampo process health;
- any model/runtime requirements needed for the Phase 1 smoke path.


## Running Automated Tests

The current suite contains deterministic package-import, application-factory, process-health, settings, startup-composition, local-web/browser-slice, safe-rendering, logging, trust-perimeter, runtime-domain, runtime-protocol, runtime-contract, fake-runtime, mocked `llama.cpp` adapter, application-owned harness, model-tool capability-boundary, generation-lifecycle, and generation-API/SSE/cancellation/failure tests. It does not require a model runtime or internet access once dependencies are installed.

Run the focused startup-composition test with:

```bash
.venv/bin/python -m pytest tests/test_startup.py
```

Run the focused `llama.cpp` adapter tests with:

```bash
.venv/bin/python -m pytest tests/test_llama_cpp_runtime.py
```

Run the focused model-tool capability-boundary tests with:

```bash
.venv/bin/python -m pytest tests/test_tool_boundary.py
```

Run the focused application-owned harness tests with:

```bash
.venv/bin/python -m pytest tests/test_harness.py
```

Run the focused ephemeral generation lifecycle tests with:

```bash
.venv/bin/python -m pytest tests/test_generation_lifecycle.py
```

Run the focused generation API/SSE tests with:

```bash
.venv/bin/python -m pytest tests/test_generation_api.py
```

Run the focused browser generation-slice tests with:

```bash
.venv/bin/python -m pytest tests/test_web_shell.py
```

Run the complete current suite with:

```bash
.venv/bin/python -m pytest
```

The startup-focused command reports one passing test, the adapter-focused command reports 24 passing tests, the tool-boundary-focused command reports 13 passing tests, the harness-focused command reports 20 passing tests, the lifecycle-focused command reports 13 passing tests, the generation-API/SSE/cancellation/failure-focused command reports 20 passing cases, the browser-slice-focused command reports 16 passing tests, and the complete suite reports 183. These commands remain verified with Python 3.14.7, FastAPI 0.141.1, Jinja2 3.1.6, Uvicorn 0.52.4, HTTPX 0.28.1, and pytest 9.1.1.


## Real `llama.cpp` Smoke Test

**Current status:** Not available yet.

Phase 1 requires an opt-in real-runtime smoke path. Once implemented, document the exact prerequisites and command/checklist here.

The smoke procedure should verify at minimum the behavior required by the active Phase 1 contract, including successful local streaming and truthful cancellation.

Keep the real-runtime smoke path separate from the default deterministic test suite.

## Troubleshooting

**Current status:** No implementation-specific troubleshooting guidance exists yet.

Add entries only for failures that can occur in the implemented system and have a verified diagnosis or recovery procedure. Avoid speculative troubleshooting for unimplemented features.

## Development Documentation Rule

Whenever implementation changes any supported setup, run, test, smoke-test, or troubleshooting procedure, update this file in the same task.

`docs/project/DEVELOPMENT.md` should answer:

> **How do I operate and test what actually exists right now?**

If the answer is not yet known or not yet implemented, state that explicitly rather than inventing a command.
