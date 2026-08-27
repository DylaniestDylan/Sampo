# Architecture.md

## 1. Purpose and Authority

`docs/project/Architecture.md` is the canonical source of truth for the product-wide architecture and permanent architectural invariants of **Sampo**, the Personal AI Workspace.

The application is named **Sampo**, in reference to the Sampo of the Finnish national epic *Kalevala*. The name is product identity rather than an architectural metaphor or source of implementation requirements.

The product is a local-first AI workspace centered on reusable Personas, durable conversations, explicit knowledge access, controlled research, local model inference, user-controlled memory, and strictly read-oriented assistance.

Implementation documents may refine this architecture within their defined scope, but they may not contradict it. If implementation reality appears to require a contradiction, implementation must stop and the conflict must be presented to the user. The architecture changes only when the user explicitly approves an architectural change.

### 1.1 Documentation responsibilities and authority

Project documents are separated by the question they answer:

1. **`docs/project/Architecture.md` — “What am I building?”** Canonical product architecture, permanent invariants, major subsystem boundaries, end-state requirements, and roadmap.
2. **Approved implementation/phase contracts — “What am I building right now?”** Scoped implementation contracts defining prerequisites, concrete interfaces, tasks, tests, acceptance criteria, and handoff for one phase. The repository convention is to keep them under `docs/project/implementation/` as `Phase-XX-*.md`.
3. **`AGENTS.md` — “How must I work?”** Repository-level instructions for Codex: development permissions, workflow, phase discipline, change discipline, testing expectations, escalation rules, and definition of done.
4. **`docs/project/STATUS.md` — “What actually exists?”** Factual current implementation state and verification. It records reality; it does not define future product behavior.
5. **`docs/project/DEVELOPMENT.md` — “How do I operate/test it?”** Verified setup, run, test, smoke-test, and troubleshooting procedures for the implementation that actually exists.
6. **ADRs under `docs/project/adr/` — “Why was this choice made?”** Rationale and consequences for significant accepted technical decisions.
7. **`docs/human/` — human-facing notes, sketches, diagrams, and exploratory design material. These documents are non-authoritative unless their content is explicitly promoted into the appropriate governing project document.**
8. **Code and tests** — implementation evidence, not authority to contradict the governing documents.

Authority is domain-specific rather than one flat precedence ladder:

- `docs/project/Architecture.md` controls product semantics and permanent architectural constraints.
- The active approved phase contract controls current implementation scope and phase-specific decisions only where they remain compatible with `docs/project/Architecture.md`.
- `AGENTS.md` controls how Codex performs repository work; it cannot redefine Sampo product semantics.
- `docs/project/STATUS.md` and `docs/project/DEVELOPMENT.md` are descriptive. If they become stale, correct them to verified repository reality rather than changing Architecture or phase intent to match them.
- ADRs under `docs/project/adr/` explain accepted decisions and consequences; they do not silently override `docs/project/Architecture.md` or the active phase contract.
- `docs/human/` material and existing code/tests cannot create new product authority.

A `README.md`, if added, should orient the user and link to the canonical documents under `docs/project/` rather than duplicate architecture, phase scope, status, or operational commands. Human-oriented notes belong under `docs/human/` and must not be treated as governing requirements unless promoted into the appropriate canonical document.

A current user instruction may authorize a change to this architecture, but an implementation assistant must not infer that an invariant has been waived. Architectural changes require explicit user approval.

### 1.2 Requirement strength

Statements in this document use the following strength classes:

- **Invariant** — a permanent architectural rule. It must not be violated unless the user explicitly changes `docs/project/Architecture.md`.
- **Requirement** — behavior or capability that must be satisfied by the relevant completed phase or final application. Implementation may vary while preserving the requirement.
- **Preference** — the default technical direction. It may be changed when justified, provided no invariant or requirement is weakened and the deviation is reported.
- **Example** — illustrative only. It is not a required API, filename, layout, or implementation unless separately marked as a requirement.

---

### 1.3 Canonical terminology

To avoid implementation drift, this document uses the following terms consistently:

- **Sampo** — the canonical product/application name.
- **Workspace** — the complete local application and its durable user state.
- **Persona** — a reusable assistant identity/configuration containing instructions, model defaults, knowledge grants, enabled tools, web policy, memory policy, and behavior preferences.
- **Conversation / Chat** — a durable Persona-owned message history. This document uses the terms interchangeably unless a narrower technical distinction is explicitly stated.
- **Generation / Assistant response** — one model-produced response associated with a user turn, including its final text and any separately emitted Thinking content.
- **Turn** — one user request and the application/model activity performed to produce one assistant response.
- **Knowledge Collection** — a logical user-managed grouping of one or more registered knowledge sources.
- **Knowledge Source** — an explicitly registered local resource or imported document that can be ingested, indexed, and retrieved.
- **Project** — a specialized knowledge domain containing project-oriented sources and metadata; it is not a mandatory chat binding.
- **Grant** — an explicit application-stored authorization allowing a Persona to search/read a knowledge collection or logical subtree.
- **Tool** — a narrow application-owned model-callable read/research capability with a fixed schema.
- **Research Run** — bounded application/tool activity used to gather evidence for one turn.
- **Model Runtime** — the local inference service/process used to execute model requests; `llama.cpp` is the first supported runtime.
- **Model Preset** — reusable local-model identity plus request-scoped generation/sampling defaults that confer no permissions. Host/runtime loading settings are separate unless a future phase explicitly introduces a distinct runtime-profile concept.
- **Thinking** — reasoning content explicitly emitted by the selected local model/runtime separately from the final answer. It does not mean access to hidden internal reasoning.
- **Passive Observation** — read-only state supplied by a future IDE/engine adapter as evidence.

**Requirement:** Terminology in implementation/phase documents should preserve these meanings. A phase document may introduce narrower implementation terms but must not silently redefine the product entities above.

---

## 2. Product Goal

**Requirement:** Build **Sampo** as a fully local, self-hosted, free/open-source, lightweight web application that acts as the user's personal AI workspace.

**Invariant:** Sampo is exclusively a single-user, local-machine application for one trusted end user operating it on their own machine. Multi-user tenancy, account/role administration, remote hosting, and LAN/public exposure are outside the current product architecture.

**Scope assumption:** This workspace is a personal harness for one trusted user on their own local machine. It is not intended to provide adversarial multi-user isolation, hostile-local-user security, enterprise administration, or public-service hardening. Security controls in this architecture exist primarily to keep the model, retrieved content, web research, parsers, and browser-facing localhost service inside deliberately narrow boundaries.

The product is not fundamentally a Godot-specific assistant. Godot/GDScript and software-development tutoring are the first major use case and the first domain in which retrieval, project understanding, version awareness, documentation research, and debugging guidance must work well.

The application should support reusable AI Personas such as:

- a general assistant;
- a Godot/GDScript tutor;
- a code reviewer;
- a debugging assistant;
- future user-defined roles with different instructions, knowledge access, tools, model settings, and memory.

The workspace should behave like a reliable assistant, tutor, and research partner that can:

- understand the user's question and the active Persona's purpose;
- search permitted local knowledge when relevant;
- inspect permitted project knowledge and source code as read-only evidence;
- distinguish current implementation from design intent, planning, and accepted decisions;
- understand version-sensitive technical documentation;
- use controlled web research when current verification is useful or explicitly requested;
- understand images/screenshots when the selected local model supports vision;
- eventually consume passive observational context from development tools such as Rider and Godot;
- explain uncertainty and conflicting evidence;
- produce practical, step-by-step answers and instructional code as text;
- cite the sources actually consulted.

**Invariant:** The application is not a coding agent and must never become an autonomous development environment.

**Invariant:** The assistant may autonomously acquire and compare information inside explicitly granted read-only boundaries, but it may never autonomously act on the user's machine, project, IDE, engine, repositories, or external accounts.

The canonical behavioral example is a question such as:

> "My character jumps and takes damage. Why?"

For that type of request, the system should be capable of locating relevant project implementation, reading the documented intended mechanics, identifying the applicable Godot version, consulting authoritative technical documentation, performing web verification when justified, comparing the evidence, and then producing a practical debugging/fix procedure without modifying or executing anything.

---

## 3. Core Product Model

The primary user-facing entities are:

```text
Local llama.cpp Model / Model Preset
        │
        ▼
     Persona
        │
        ├── instructions / role
        ├── default model and generation settings
        ├── permitted knowledge
        ├── permitted tools
        ├── web-research policy / whitelist
        ├── memory policy
        └── response/research preferences
                │
                ▼
             Chats
                │
                ├── messages
                ├── attachments / images
                ├── optional model override
                └── research traces
```

Knowledge exists independently of chats and is organized in a user-facing hierarchy:

```text
Knowledge
│
├── Global
│   └── shared/general collections
│
├── Persona
│   └── persona-oriented collections
│
└── Project
    └── project-oriented collections
```

**Invariant:** A Project is a specialized knowledge domain, not a mandatory property of a chat.

**Invariant:** A Persona may own zero, one, or many durable chats. Personas are reusable identities/configurations, not single long-running conversation threads.

**Invariant:** A chat belongs to exactly one Persona. Opening an existing chat restores/activates the Persona that owns it.

**Requirement:** Knowledge access is granted explicitly to Personas. The existence of a collection under `Global`, `Persona`, or `Project` does not automatically make it visible to every Persona.

---

## 4. Permanent Architectural Invariants

### 4.1 Application-owned orchestration

**Invariant:** The application owns its conversational orchestration/harness layer.

No third-party agent framework is a permanent architectural dependency or product boundary.

The harness must provide only the model-facing orchestration required by the product, including:

- construction of model-facing context;
- streaming model interaction;
- bounded tool-call handling;
- application-owned tool selection exposure;
- research sequencing within authorized limits;
- tool-result interpretation;
- final-answer synthesis.

External projects may be studied as reference implementations, but they do not define the application's architecture.

### 4.2 Strictly read-oriented assistant behavior

**Invariant:** The user remains the actor who applies project, code, environment, or system changes.

The model-facing runtime may receive capabilities to:

- search permitted knowledge;
- read permitted knowledge;
- search indexed project code and project documentation;
- read bounded project context;
- inspect structured project/version metadata;
- perform controlled, whitelist-constrained web research;
- inspect user-supplied files and images;
- consume future application-owned passive observation data.

The model-facing runtime must never receive a generic capability to:

- create, edit, rename, move, or delete files;
- modify the user's project;
- invoke a shell, terminal, command runner, process, interpreter, compiler, REPL, or notebook;
- execute generated code or scripts;
- run project builds or tests;
- use Git or another VCS as an agent capability;
- install, update, remove, or mutate dependencies or system tooling;
- control Rider, Godot, another IDE, another application, or the desktop;
- perform arbitrary browser automation;
- perform unrestricted network access;
- create, install, discover, synthesize, or enable new host capabilities at model request.

Equivalent capabilities are forbidden even when exposed under different names.

**Invariant:** Security is based on capability absence and narrow application-owned interfaces, not model obedience or prompt instructions.

### 4.3 Fully local model and core application

**Invariant:** The application, durable state, knowledge indexes, Persona configuration, Persona memory, conversation history, research traces, UI, and LLM inference run locally on the user's machine.

**Invariant:** Remote/cloud LLM providers are outside the current architecture.

**Requirement:** The first supported inference runtime is `llama.cpp`.

**Invariant:** The standard application must not require a paid cloud service.

**Requirement:** Software dependencies and local services required by the standard application must be free/open-source. External public websites/content sources used only as research evidence are not required to be open-source, but the standard application must not depend on a paid research service or paid account to provide its core behavior.

**Invariant:** External network access is permitted only through explicitly designed application-owned research features such as the controlled web-research subsystem.

**Requirement:** The application remains usable without internet access except for features that explicitly require current online verification.

### 4.4 Persona identity and chat ownership

**Invariant:** A Persona may own zero, one, or many durable chats.

**Invariant:** Every durable chat belongs to exactly one Persona.

**Invariant:** Loading a chat must restore the owning Persona rather than applying whatever Persona happens to be currently selected elsewhere in the UI.

**Requirement:** A Persona defines a default local model, but a conversation may temporarily override that model without mutating the Persona's default configuration.

### 4.5 Explicit knowledge access

**Invariant:** Knowledge access is deny-by-default at the Persona boundary.

A Persona may search/read only knowledge collections or logical directories that the user has explicitly granted to it.

`Global` means globally organized/shared knowledge, not globally authorized knowledge.

**Invariant:** Retrieved content cannot grant access to additional knowledge.

### 4.6 User-controlled Persona memory

**Invariant:** Long-term memory belongs to a Persona.

**Invariant:** The model may propose a memory but may not silently create, approve, edit, or delete durable memory.

A proposed memory becomes durable only after explicit user approval.

**Requirement:** Persona memory can be enabled or disabled by the user and must be inspectable, editable, and deletable by the user.

### 4.7 Controlled web access

**Invariant:** Web research is constrained by user-configured Persona permissions and domain allowlists.

A Persona cannot search or fetch an unapproved domain merely because the model requests it.

The model cannot modify its own domain allowlist.

### 4.8 Provenance is mechanical

**Invariant:** Citations and research traces must derive from actual executed tool activity and source identifiers. The model may not invent provenance.

### 4.9 Lightweight by default

**Requirement:** The system should minimize:

- runtime memory consumption;
- idle CPU usage;
- disk footprint;
- background services;
- dependency count;
- process/container count;
- unnecessary indexing infrastructure;
- unnecessary model calls;
- unnecessary network requests.

**Preference:** Prefer the simplest local component that satisfies a measured requirement. Add architectural complexity only after evidence demonstrates a need.

### 4.10 Local trust perimeter and privacy

**Invariant:** The normal application web server binds to loopback/local-host interfaces by default and is designed for one local operator. Exposing the application to a LAN, the public internet, or multiple users requires an explicit future architecture change and security review.

**Invariant:** The standard application performs no analytics, telemetry, crash-report uploads, remote asset loading, or other background outbound communication. External network activity is limited to user-authorized web research described by this architecture.

**Requirement:** Browser-facing application endpoints must be protected against hostile cross-origin access to the local service. Exact implementation is phase-defined, but permissive CORS, unvalidated browser origins, and state-changing endpoints that can be invoked freely by unrelated web pages are not acceptable.

**Requirement:** Frontend scripts, styles, fonts, and other required application assets are served locally by the application rather than depending on third-party CDNs.

**Invariant:** Model output, retrieved documents, web content, attachment text, filenames, and other untrusted strings must be rendered as data. The frontend must escape/sanitize untrusted HTML/Markdown and must never execute scripts, event handlers, or active content merely because they appear in model/source text.

**Security assumption:** The current architecture trusts the user's local OS account and machine sufficiently to run the application and local model. It does not claim to protect local data from an attacker who already has equivalent same-user filesystem/process access or a compromised operating system. This does not weaken the application's obligation to isolate the model, protect backend secrets, and avoid unnecessary data exposure.

### 4.11 Bounded resource use and graceful failure

**Requirement:** Untrusted, unexpectedly large, or malformed inputs must not cause unbounded application memory, CPU, disk, model-context, database, or network consumption. Relevant subsystems must apply practical size, count, concurrency, and retention limits appropriate to their role.

**Requirement:** Resource failures such as model/runtime out-of-memory, insufficient disk space, oversized input, parser/indexing failure, or exhausted configured research/context limits must fail visibly and must not silently corrupt durable state, weaken authorization, or bypass configured limits.

**Preference:** Keep resource controls simple and local. The purpose is graceful behavior on one workstation, not cluster-style quotas or multi-tenant resource accounting.

---

## 5. High-Level Architecture

```text
┌────────────────────────────────────────────────────────────────────┐
│                         Local Browser UI                           │
│                                                                    │
│ Personas · Chats · Knowledge · Models · Memory · Settings · Trace │
└───────────────────────────────┬────────────────────────────────────┘
                                │ localhost
                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                       Application Backend                          │
│                                                                    │
│ Workspace / Persona management                                    │
│ Durable conversations / messages                                  │
│ Persona memory + approval flow                                    │
│ Knowledge grants / source management                              │
│ Ingestion / indexing / retrieval                                  │
│ Version metadata / resolution                                     │
│ Research coordination / budgets                                   │
│ Citation / provenance recording                                   │
│ Tool authorization / policy                                       │
│ Safe web gateway                                                   │
│ Passive-context adapters (future)                                 │
│ llama.cpp configuration / lifecycle                               │
│                                                                    │
│                 ┌──────────────────────────────┐                   │
│                 │ Application-owned Harness    │                   │
│                 │                              │                   │
│                 │ context assembly             │                   │
│                 │ model streaming              │                   │
│                 │ bounded tool loop            │                   │
│                 │ research sequencing          │                   │
│                 │ result interpretation        │                   │
│                 │ response synthesis           │                   │
│                 └───────────────┬──────────────┘                   │
└─────────────────────────────────┼───────────────────────────────────┘
                                  │
          ┌───────────────────────┼────────────────────────┐
          ▼                       ▼                        ▼
   Local Knowledge          Safe Web Research      Local llama.cpp
   + Project Sources        (whitelisted)          Model Runtime
          │
          ▼
 Passive Development Context (future, read-only observations only)
```

**Invariant:** The frontend communicates with the backend through a stable application API. It does not depend directly on model-runtime internals or harness internals.

**Invariant:** The backend owns capability, authorization, persistence, retrieval, network policy, and tool implementation.

---

## 6. Responsibility Boundaries

### 6.1 Frontend

The frontend is a client and presentation layer.

It owns user interaction for:

- Persona selection and management;
- conversation navigation;
- model selection/override controls;
- model runtime and generation/sampling settings;
- model-emitted reasoning/Thinking display and controls when supported;
- knowledge browsing and Persona grants;
- memory approval/edit/delete UI;
- research controls;
- attachment/image submission;
- source/citation display;
- detailed research-trace display;
- settings and local model configuration.

**Invariant:** Core authorization, research, retrieval, persistence enforcement, web policy, tool implementation, and model lifecycle logic belong in the backend.

### 6.2 Application backend

**Invariant:** The backend is the trusted application control plane.

It owns:

- Persona persistence and effective configuration;
- conversation persistence, editing, and regeneration;
- model/runtime configuration;
- model preset and generation/sampling configuration;
- persistence of permitted conversation-level model/generation overrides;
- model-emitted reasoning events/metadata when the selected model/runtime exposes them;
- Persona memory persistence and approval state;
- knowledge organization and access grants;
- source registration and metadata;
- document ingestion/indexing;
- retrieval/search implementation;
- version metadata and resolution;
- research-run lifecycle and budgets;
- research traces and provenance;
- authorization and policy enforcement;
- application-owned tool implementations;
- safe web research and actual network access;
- passive observation adapters when implemented;
- llama.cpp lifecycle and runtime interaction.

### 6.3 Application-owned harness

The harness is responsible only for model-facing orchestration needed to answer a request:

- assembling trusted Persona/system instructions;
- assembling bounded conversation context;
- presenting explicitly authorized tools;
- streaming messages to/from the selected local model;
- forwarding model-emitted reasoning/Thinking events separately from final-answer content when available;
- receiving structured model tool requests;
- sequencing bounded tool calls;
- returning tool results to the model;
- comparing/interpreting retrieved evidence;
- terminating the research loop within configured limits;
- producing the final response.

**Invariant:** The harness does not own durable Personas, conversations, memory, knowledge storage, authorization policy, indexes, network access, or hidden copies of backend state.

### 6.4 Local model runtime adapter

The model-runtime boundary translates application-owned requests/events into the concrete `llama.cpp` interface.

It should expose a narrow application-owned contract rather than allowing the rest of the product to depend on `llama.cpp` transport details.

Conceptually:

```text
ModelRuntime
  listModels()
  getCapabilities(model)
  streamChat(request)
  abort(requestId)
```

The exact interface is phase-defined.

### 6.5 Knowledge subsystem

The knowledge subsystem owns:

- logical knowledge hierarchy;
- collection/source identity;
- Persona grants;
- source metadata;
- parsing and normalization;
- indexing;
- retrieval;
- source/version/provenance metadata;
- project-specific source classification.

### 6.6 Research subsystem

The research subsystem owns durable run coordination and enforcement:

- automatic versus forced research mode;
- tool budgets and limits;
- permitted knowledge scopes;
- permitted web domains;
- result/provenance recording;
- safe network policy;
- failure reporting.

The harness may decide which authorized research step to request next, but the backend remains the enforcing authority.

### 6.7 Passive observation subsystem (future)

Future Rider/Godot awareness belongs behind application-owned, read-only observation adapters.

Observation adapters may expose structured state as evidence. They may not expose actions.

### 6.8 Trusted backend host operations versus model capabilities

The trusted application backend necessarily performs some host operations that the model is forbidden to perform directly. Examples include:

- reading files/resources inside explicitly registered knowledge-source boundaries;
- writing the application's own database, indexes, caches, configuration, and user-approved state;
- starting, stopping, or communicating with the configured local `llama.cpp` runtime;
- performing safe, allowlist-constrained outbound web requests for authorized research;
- opening local parser/indexing operations required by deterministic application workflows.

**Invariant:** A trusted backend capability does not imply a model-facing capability. The model receives only the narrow tool schemas explicitly authorized for the active Persona.

**Invariant:** Model-generated text, tool arguments, retrieved content, and web content may influence only validated inputs to those narrow backend operations. They may not become arbitrary process arguments, filesystem paths, network targets, configuration mutations, or executable code.

**Requirement:** Deterministic application maintenance tasks such as indexing, cache cleanup, or database migration are not Persona autonomy and may run without model involvement. They must not create hidden model jobs, autonomous agents, or action capabilities.

---

## 7. Persona Model

**Requirement:** Persona is the primary user-facing configuration unit for assistant behavior.

A Persona should conceptually contain:

```text
identity
  id
  name
  avatar
  description / purpose

model
  default local model
  generation/sampling defaults
  optional reasoning defaults when supported

instructions
  system prompt / role

knowledge
  explicit grants to knowledge directories/collections

capabilities
  explicitly enabled read/research tools

web research
  enabled/disabled
  domain allowlist
  source-priority preferences

memory
  enabled/disabled
  approved Persona memories

behavior
  research preferences
  response/tutoring style
```

### 7.1 Persona purpose

A Persona's "job" means its intended role or specialty, not a scheduler or autonomous background task.

Examples:

- `Godot Tutor` — teaches Godot/GDScript and provides project-aware technical guidance;
- `Code Reviewer` — reviews supplied/permitted code and assists with debugging;
- `General Assistant` — general-purpose conversation without development-specific assumptions.

**Invariant:** A Persona is a configuration/identity for conversations, not an autonomous worker with independent execution authority.

### 7.2 Persona and model selection

**Requirement:** Each Persona has a preferred/default local model and may optionally inherit generation defaults from an application-owned model preset.

A **model preset** is a user-visible saved configuration associated with a local model. It exists to provide reusable model/generation defaults; it is not a Persona and cannot grant tools, knowledge, web access, memory, or other permissions.

**Requirement:** A user may override the effective model for a specific conversation without changing the Persona default.

A conversation-specific override should be durable as conversation state until the user clears or changes it.

**Requirement:** Generation/sampling settings use an explicit precedence model so effective values are predictable:

```text
llama.cpp / model defaults
        ↓
application model preset
        ↓
Persona defaults
        ↓
conversation overrides
```

A lower layer overrides only the settings it explicitly defines; unspecified settings inherit from the layer above.

**Requirement:** Editing a model preset affects future generations that inherit from it; historical assistant responses retain their recorded effective model/generation settings and are not retroactively rewritten.

**Invariant:** Model selection or generation-setting changes cannot expand the Persona's authorized tools, knowledge grants, web domains, or host capabilities.

### 7.3 Persona and knowledge

**Requirement:** Persona access to knowledge is explicit and user-configured.

A Persona may receive grants to multiple logical directories or subdirectories across the `Global`, `Persona`, and `Project` knowledge areas.

The same knowledge collection may be granted to multiple Personas.

### 7.4 Persona configuration lifecycle

**Requirement:** A Persona is a live configuration for future turns. Editing a Persona's instructions, model defaults, knowledge grants, enabled tools, web policy, memory policy, or behavior settings affects subsequent turns in all chats owned by that Persona unless a conversation-specific override explicitly applies.

**Requirement:** Each assistant response records or references a compact snapshot and/or stable hash of the effective Persona configuration that materially affected that generation. This should include enough information for practical diagnosis and provenance, such as the Persona identity, effective instructions/configuration identity, effective model/model preset, generation settings, and relevant enabled-capability/policy identities. The application does not need to maintain a separately navigable revision history for every Persona edit.

**Invariant:** Historical assistant responses are not rewritten when the Persona changes. Historical effective-configuration snapshots/hashes are provenance records only; they do not preserve old permissions as usable capabilities. All future tool/knowledge/web authorization is evaluated against current effective Persona policy.

**Requirement:** Opening an old chat restores the Persona identity and current effective Persona configuration for new turns. Historical generation snapshots/hashes describe how earlier responses were produced; they do not roll the Persona back or create a hidden historical Persona configuration.

---

## 8. Conversation and Context Model

### 8.1 Conversation ownership

**Invariant:** A Persona may own multiple independent conversations. Starting a new chat creates a new durable conversation under that Persona; it does not append to a single Persona-wide thread.

**Invariant:** Every conversation has one owning Persona.

The UI should group/nest conversation history beneath Personas.

Selecting an old conversation activates its owning Persona automatically.

Switching the globally selected Persona must not silently mutate an existing conversation into another Persona.

**Invariant:** An existing conversation is not re-parented to another Persona in place. If a future feature allows continuing material under a different Persona, it must create an explicit copy/new conversation with new ownership rather than mutating the original chat's identity.

### 8.2 Linear conversation history and regeneration

**Requirement:** Each conversation has one active linear message history. Conversation persistence supports:

- normal chronological messaging;
- editing an earlier user message;
- regenerating an assistant response.

**Requirement:** Editing an earlier user message truncates subsequent active conversation history before continuation from the edited point. Any later messages, research state, or derived context that no longer belongs to the active sequence must not remain active model context.

**Requirement:** Regenerating an assistant response replaces the active response for that turn. The architecture does not require retaining or navigating prior regenerated alternatives. An implementation may retain limited recovery/debug data if useful, but superseded responses must not silently remain active conversation context.

**Preference:** Keep conversation persistence linear rather than introducing a message tree/DAG unless a future measured product need justifies branching.

### 8.3 Multimodal conversation content

A conversation message may contain:

- text;
- user-supplied files;
- images/screenshots;
- references to permitted knowledge sources;
- future passive observation snapshots.

**Invariant:** Chat attachments do not silently become durable Knowledge Library sources. Importing material into the Knowledge Library requires an explicit user action.

### 8.4 Context assembly

**Requirement:** The backend/harness assembles model-facing context from bounded, classified inputs rather than blindly concatenating all available state.

Conceptual priority classes include:

1. application security/policy instructions;
2. Persona instructions/configuration;
3. current user request and required conversation state;
4. user-approved Persona memory relevant to the request;
5. retrieved permitted knowledge;
6. user-supplied attachments/images;
7. passive observation evidence when available;
8. web evidence when research uses it.

This ordering is not a literal prompt template. Exact prompt composition is phase-defined.

**Invariant:** Lower-trust evidence may affect factual reasoning but cannot override application policy, expand capability, or alter permissions.

### 8.5 Context-window management

**Requirement:** Durable conversation history and durable knowledge must remain separate from the limited model context window.

The application should select, truncate, summarize, or retrieve context deliberately so that long chats do not require sending the complete workspace state on every model call.

Any conversation summary used for model-facing context must remain subordinate to the raw durable conversation record and must not become a hidden source of project truth.

**Requirement:** Derived conversation summaries/context caches are traceable to the active message sequence or the message IDs/content hashes they summarize. Editing earlier history or regenerating a response must invalidate or bypass derived context based on superseded history so stale state cannot leak into the active conversation.

**Preference:** Prefer deterministic budgeting and retrieval before adding extra model calls solely for context management.

### 8.6 Turn lifecycle, cancellation, and historical metadata

**Requirement:** Every generated assistant response has an explicit lifecycle state such as `streaming`, `completed`, `stopped`, or `failed`. Interrupted/failed output must not be presented as though generation completed normally.

**Requirement:** Stop Generation must cancel the active model request and prevent additional research/tool steps for that turn. Cancellation must not leave a hidden model/tool loop continuing after the UI reports that the turn stopped.

**Requirement:** Partial output may be retained as a stopped/failed response when useful, but its incomplete status must remain visible.

**Requirement:** Each assistant response records sufficient generation metadata for diagnosis and provenance, including where applicable:

- Persona ID and effective Persona configuration snapshot/hash;
- effective model/model-preset identity;
- effective generation/sampling settings;
- reasoning mode/budget when applicable;
- model/runtime capability/version metadata relevant to the turn;
- associated research-run/citation identifiers;
- completion status and timing/token metrics when available.

**Invariant:** The application must not silently substitute a different model, Persona, knowledge scope, or tool policy when the configured resource is unavailable. It must report the incompatibility/unavailability and require an explicit user choice or valid configured fallback policy.

**Preference:** At most one assistant generation should actively mutate a given conversation at a time. Independent conversations may generate concurrently when the configured local runtime supports it reliably.

---

## 9. Knowledge Library and Access Model

### 9.1 User-facing hierarchy

**Requirement:** The Knowledge Library provides a user-facing organizational hierarchy with the top-level concepts:

```text
Global
Persona
Project
```

These are logical organization/access concepts. They need not correspond one-to-one with physical filesystem directories. Folder names, nesting, or a Persona-named directory do not create authorization by convention; grants remain explicit application state.

Possible example:

```text
Knowledge
│
├── Global
│   ├── Programming
│   └── Personal Notes
│
├── Persona
│   ├── Godot Tutor
│   │   ├── Godot Documentation
│   │   └── GDScript Reference
│   └── Code Reviewer
│       └── Coding Standards
│
└── Project
    ├── RPG
    │   ├── Source
    │   ├── Design
    │   ├── Architecture
    │   ├── Planning
    │   └── Decisions
    └── Other Game
```

### 9.2 Grants

**Invariant:** Persona grants are evaluated using stable collection/resource identifiers, not model-supplied arbitrary paths.

**Requirement:** The UI must make effective Persona access understandable to the user.

A Persona can be granted access to selected directories/collections and their intended descendants according to explicit application grant semantics.

The exact grant-inheritance UI and storage representation are phase-defined, but accidental access outside an explicit grant is forbidden.

### 9.3 Projects as knowledge

**Requirement:** Project knowledge is represented as a specialized knowledge domain rather than a chat-level mandatory binding.

A Project may contain:

- current source code;
- architecture documentation;
- design documentation;
- planning/roadmap material;
- accepted decisions;
- project configuration;
- engine/runtime metadata;
- other explicitly registered read-only project context.

A Persona may be granted access to zero, one, or many Project knowledge domains.

A generic question may therefore be answered without forcing unrelated Project material into context.

### 9.4 Project resolution during research

**Invariant:** A conversation does not require a permanently attached Project in order to use Project knowledge.

When a request is project-specific, the research subsystem should resolve the relevant Project knowledge domain from available evidence such as:

- an explicit project name or source reference in the user's request;
- conversation context that unambiguously identifies the project;
- user-supplied attachments that belong to a registered project;
- a uniquely relevant permitted Project knowledge domain;
- future passive Rider/Godot observations that identify the active project.

**Invariant:** If multiple permitted Projects remain plausibly relevant and the system cannot resolve the intended project safely, it must not silently merge or guess across projects. It should request disambiguation or clearly limit the answer to non-project-specific information.

**Requirement:** Generic questions that do not materially require Project context should not automatically search unrelated Project collections merely because the Persona has permission to them.

### 9.5 Source representation

**Requirement:** Physical folder layout is not itself authoritative. Sources carry explicit metadata describing authority, type, status, version, applicability, and provenance where relevant.

Example:

```yaml
source: godot
version: 4.6
authority: official
type: technical-documentation
status: current
```

Example:

```yaml
source: rpg-roadmap
authority: project
type: planning
status: proposed
```

### 9.6 Ingestion pipeline

**Requirement:** Document ingestion is application-owned.

Conceptually:

```text
Source registration
    ↓
Resolve explicit knowledge scope
    ↓
Enumerate permitted files/resources
    ↓
Parse supported formats
    ↓
Extract metadata
    ↓
Normalize text
    ↓
Chunk when appropriate
    ↓
Compute content hash
    ↓
Store metadata
    ↓
Update search index
```

**Requirement:** Incremental indexing should avoid reprocessing unchanged content by using content hashes and/or trustworthy modification metadata.

### 9.7 Project code

Project source code may be indexed as read-only project evidence.

**Invariant:** Indexing source code does not grant execution, modification, shell, Git, or IDE-control capability.

### 9.8 Local source boundaries and ingestion safety

**Invariant:** The knowledge subsystem may enumerate/read local files only inside sources or roots explicitly registered by the user/application. It must not crawl unrelated directories, the user's home directory, other repositories, or arbitrary paths merely because they are reachable by the host process.

**Requirement:** Local source resolution must prevent boundary escape through relative traversal, absolute-path injection, symlink/junction/reparse-point tricks, or equivalent path aliasing. The concrete platform-safe path-resolution strategy is phase-defined and must be covered by tests.

**Invariant:** Local documents and attachments are treated as passive data. Ingestion/parsing must not execute macros, scripts, embedded binaries, document actions, project build logic, or code discovered inside a source.

**Requirement:** Parsers/importers must enforce supported-type and resource-size limits appropriate to the format, and unsupported/unsafe content must fail explicitly rather than being executed or silently interpreted through a more powerful fallback.

### 9.9 Source freshness and availability

**Requirement:** The knowledge subsystem tracks enough source state to distinguish current indexed content from deleted, changed, unavailable, or stale source material.

When a registered source changes, derived indexes/caches must eventually be updated or marked stale; the application must not silently present known-stale material as current project truth.

When an underlying source becomes unavailable, the UI/research layer should expose that state rather than treating an old cached copy as unquestionably current.

---

## 10. Knowledge Authority Model

**Requirement:** Retrieved information classes remain distinguishable rather than being collapsed into one undifferentiated context blob.

### 10.1 Current project facts

Information describing what a project currently contains or does, such as current architecture, mechanics, implementation state, configuration, source code, and engine version.

### 10.2 Project design

Information describing intended behavior and design goals.

### 10.3 Project planning

Future/proposed work that may not yet exist.

**Invariant:** Planning must not be silently treated as current project reality.

### 10.4 Project decisions

Accepted architectural or design decisions that constrain future recommendations.

### 10.5 Official technical documentation

Versioned authoritative documentation for Godot, GDScript, libraries, frameworks, or other relevant technologies.

### 10.6 Current authoritative web information

Information retrieved through controlled web research when local information may be stale, incomplete, version-sensitive, ambiguous, or conflicting.

### 10.7 User-approved Persona memory

Approved memory is authoritative only as user-approved personalization/context for that Persona. It must not silently override more appropriate project/documentation sources for technical facts.

### 10.8 General model knowledge

General model knowledge is the lowest-authority factual source for research questions. It may assist interpretation and explanation but must not silently supersede higher-authority project facts, user-approved decisions, or authoritative documentation.

### 10.9 Authority is claim-specific

**Requirement:** The system does not apply one universal source ranking to every kind of claim. Authority depends on what is being established:

- current project source/configuration is strongest evidence for what the project currently implements;
- accepted project decisions/design documentation are strongest evidence for intended/required project behavior;
- planning describes proposed future state and must not be treated as current implementation;
- official version-applicable technical documentation/source is strongest evidence for external API/engine behavior;
- current web evidence is used to verify freshness, resolve gaps, or surface changes/conflicts;
- Persona memory is personalization, not a substitute for project or technical authority;
- general model knowledge fills gaps only at the lowest factual authority.

**Requirement:** When relevant higher-authority sources disagree, the assistant should expose the disagreement and explain what each source establishes rather than silently choosing whichever text is easiest to retrieve.

---

## 11. Retrieval Architecture

**Preference:** Begin with SQLite for metadata and SQLite FTS5 for full-text retrieval.

Initial conceptual retrieval flow:

```text
Question
  ↓
Identify relevant Persona-authorized knowledge scopes
  ↓
Determine relevant source classes / versions
  ↓
Metadata / filename filtering
  ↓
SQLite FTS5 search
  ↓
Candidate chunks/documents
  ↓
Model or deterministic relevance evaluation
  ↓
Read nearby context when necessary
```

**Invariant:** Retrieval can search only the effective knowledge grants of the active Persona.

**Preference:** Do not introduce embeddings/vector search initially.

Embeddings or more complex retrieval may be considered only if measured retrieval tests demonstrate that metadata filtering and FTS5 are inadequate.

**Requirement:** Retrieval quality, source classification, metadata, provenance, authority, and version applicability are more important than retrieval-system complexity.

**Requirement:** Retrieval tests must include realistic project/documentation questions rather than only synthetic keyword matches.

**Invariant:** Persona authorization is re-evaluated at retrieval/read time. A previously produced result ID, cache entry, index row, conversation attachment reference, or research-trace identifier cannot be used as a capability token to bypass a later grant change.

**Requirement:** Grant revocation is forward-looking for source access: it blocks future search/read of the revoked source and invalidates hidden derived retrieval state. It does not silently rewrite already-visible historical user/assistant conversation text. Historical conversational prose may therefore still contain facts previously learned from that source, but it is treated as conversation history rather than fresh authorized source evidence. Raw historical tool payloads/excerpts from revoked sources must not be replayed automatically as fresh authorized evidence.

---

## 12. Research Behavior and Orchestration

### 12.1 Automatic research

**Requirement:** Normal conversation uses adaptive research behavior.

The Persona/harness should decide whether research materially improves reliability based on factors such as:

- project-specificity;
- version sensitivity;
- potentially stale model knowledge;
- uncertainty;
- source disagreement;
- missing local evidence;
- the Persona's role and research configuration.

The model should not perform expensive research mechanically for every trivial question when reliable local/model context is sufficient.

### 12.2 Forced research

**Requirement:** The UI provides an explicit manual Research control.

When the user forces research, the assistant must attempt source-driven research before answering even when it believes it already knows the answer.

Equivalent explicit user wording such as "research this" may also force research.

If no authorized source or tool is available, the assistant must state that research could not be completed rather than silently pretending it researched.

### 12.3 Core research workflow

Conceptually:

```text
User question
    ↓
Understand intent
    ↓
Resolve active Persona and effective capabilities
    ↓
Identify relevant authorized knowledge domains
    ↓
Determine project / engine / documentation versions when relevant
    ↓
Search permitted local documentation / knowledge
    ↓
Search permitted project knowledge when relevant
    ↓
Read high-relevance context
    ↓
Determine whether current web verification is necessary or forced
    ↓
Controlled whitelist-constrained web research when justified
    ↓
Compare evidence and versions
    ↓
Identify conflicts / uncertainty
    ↓
Develop Persona-appropriate explanation
    ↓
Practical instructional answer
    ↓
Light inline citations + detailed trace on demand
```

**Invariant:** There is no "take action on the project" step in this workflow.

### 12.4 Canonical debugging behavior

For a question such as:

> "My character jumps and takes damage."

A Godot-oriented Persona should be able to:

1. identify that the question is project-specific debugging;
2. search the permitted Project knowledge for player movement, jumping, health, damage, hitbox/hurtbox, collision, and related implementation;
3. read relevant project design/decision material describing when damage should occur;
4. resolve the project's Godot version when available;
5. consult relevant official Godot documentation;
6. perform web verification only when useful or forced and only on approved domains;
7. compare implementation, intended behavior, documentation, and version information;
8. explain the likely cause and uncertainty;
9. provide numbered debugging/fix steps and instructional code examples;
10. cite what was actually consulted.

### 12.5 Bounded runs and loop protection

**Invariant:** Research/model-tool activity for a turn is bounded. The harness may not continue calling tools indefinitely.

**Requirement:** Research runs support configurable limits appropriate to the enabled tools, such as:

- maximum tool-call count;
- maximum repeated/similar-call count;
- maximum fetched/read result volume or model-context budget;
- maximum web-search/fetch count;
- maximum run duration;
- model token/context limits.

**Requirement:** The harness detects obvious repeated tool-call loops or non-progressing research patterns and terminates them safely rather than relying solely on the model to notice the loop.

When a limit is reached, the assistant should use the evidence already obtained, state the limitation where relevant, and avoid fabricating missing research.

**Requirement:** User cancellation immediately closes the current research run to further model-requested tools.

---

## 13. Application Tool Boundary

**Invariant:** The model-facing runtime receives only explicitly registered, application-approved read/research tools with fixed schemas.

The conceptual initial research surface may resemble:

```text
knowledge.search()
knowledge.read()

web.search()
web.read()

observation.get_context()   # future, read-only
```

The exact names and schemas are phase-defined.

### 13.1 Authorization

Before executing a model-requested tool call, the backend must validate:

- the active Persona;
- whether the tool is enabled for that Persona;
- knowledge/resource grant scope;
- web allowlist scope when applicable;
- argument shape;
- research budgets/limits;
- resource identity.

### 13.2 Resource identity

**Invariant:** Model-facing tools use opaque IDs or structured selectors rather than arbitrary filesystem paths wherever resource identity can be represented safely.

Prefer conceptually:

```text
knowledge.read({ resource_id })
```

rather than:

```text
read({ path })
```

The backend resolves identifiers to explicitly registered resources.

### 13.3 Fail-closed behavior

**Invariant:** Unrecognized tool calls fail closed.

**Invariant:** Tool failure never falls back to generic filesystem, shell, process, code-execution, network, browser, plugin, or IDE capability.

**Invariant:** Model input, retrieved content, attachments, web content, and tool results cannot register new host tools or modify schemas/permissions.

### 13.4 Tool execution lifecycle

**Requirement:** Every tool invocation has a unique application-owned identity and a bounded lifecycle such as `requested`, `authorized`, `running`, `completed`, `rejected`, `failed`, or `cancelled`.

**Requirement:** Authorization is checked before execution, and completion/failure metadata is recorded mechanically for provenance.

**Invariant:** A cancelled, rejected, or failed tool call cannot be silently replaced with a broader tool or alternative host capability.

**Requirement:** Tool results returned to the model are bounded/normalized application data, not live host objects, open file handles, sockets, process handles, or other capability-bearing references.

---

## 14. Trust and Instruction Boundaries

### 14.1 Trusted runtime authority

Trusted runtime authority originates from application-controlled state and policy.

Examples include:

- application security policy;
- effective Persona configuration stored by the application;
- registered tool schemas;
- authorization results;
- structured knowledge grants;
- user-approved memory records;
- trusted runtime/model capability metadata.

Persona system prompts are user-controlled configuration applied by the trusted application, but they remain subordinate to permanent application security policy.

### 14.2 User task instructions

User messages define the conversational task and desired answer, but they do not grant capabilities that the active Persona/application does not possess.

A user may ask the assistant to research, explain, compare, or generate instructional code text.

A user request cannot make a structurally absent action capability available.

### 14.3 Untrusted evidence

**Invariant:** The following are evidence/data, not runtime authority:

- project documentation;
- project planning;
- source-code comments;
- indexed files;
- imported documents;
- web pages;
- search snippets;
- retrieved text;
- user-supplied attachments/images;
- passive observation snapshots;
- model-generated text;
- third-party content returned by tools.

Untrusted evidence may affect the answer but cannot create permissions, rewrite Persona grants, modify web allowlists, or redefine tool policy.

### 14.4 Secrets and sensitive application configuration

**Invariant:** Credentials, API keys, local service secrets, private tokens, and other sensitive application configuration are never model-facing context and are never returned through research/tool results.

If a configured web-search/fetch integration requires credentials, they remain backend-only and must be redacted from operational logs, traces, and user-visible provenance.

**Invariant:** Retrieved content or model output cannot request or cause disclosure of backend secrets.

---

## 15. Version Awareness

**Requirement:** Version-awareness is a core research capability for version-sensitive domains.

For relevant questions, the system should be able to determine:

```text
What version is the project using?
What version does local documentation describe?
What version does web information describe?
Does relevant behavior differ between those versions?
```

Project version state should be structured rather than inferred only from directory names.

Conceptually:

```text
engine.name
engine.major
engine.minor
engine.patch
engine.channel
```

Documents should carry explicit version/applicability metadata where relevant.

Controlled web verification should be considered for claims that are:

- version-sensitive;
- potentially stale;
- missing locally;
- ambiguous;
- conflicting;
- dependent on current upstream behavior.

**Requirement:** Web research is a verification mechanism, not a substitute for higher-authority local/project documentation when such sources exist.

---

## 16. Safe Web Research

### 16.1 Persona allowlists

**Invariant:** A Persona may access the web only when web research is enabled for that Persona and the requested target is inside its user-configured domain allowlist.

The application must enforce allowlists independently of the model.

Domain grants may include specific domains/subdomains or application-defined domain patterns. Exact matching semantics are phase-defined and must be unambiguous in the UI.

**Invariant:** Redirects may not escape the effective allowlist.

### 16.2 Search policy

**Requirement:** Research should prioritize authoritative technical sources when available.

For Godot-related questions, this normally includes official Godot documentation, release notes, proposals, and the official Godot source/repository when relevant and explicitly allowed.

Community sources may be enabled by the user through the same domain-grant mechanism and should remain distinguishable from official sources.

Where practical, search should return controlled result IDs and metadata rather than handing arbitrary raw URLs to the model-facing runtime.

### 16.3 Fetch/read policy

**Invariant:** Web research uses an application-owned isolated HTTP/search client. It must not reuse the user's normal browser cookies, authenticated browser sessions, password-manager state, client certificates, or unrelated local proxy credentials as model-accessible web authority. Authenticated/private browsing of external accounts is outside the current architecture.

**Invariant:** The safe web fetcher must prevent web research from becoming an SSRF or unrestricted network-access primitive.

The backend must reject or tightly control:

- localhost and loopback;
- private/RFC1918 ranges;
- link-local ranges;
- file URLs;
- unsupported protocols;
- redirects into blocked address ranges;
- redirects outside the Persona allowlist;
- executable/binary downloads;
- oversized responses;
- unexpected MIME types.

### 16.4 Passive extraction

**Invariant:** Retrieved pages are handled as passive documents.

The web subsystem does not execute:

- JavaScript/page scripts;
- downloaded code;
- browser extensions;
- macros;
- embedded executables.

### 16.5 Prompt-injection resistance

**Invariant:** Remote content is untrusted evidence, never runtime instruction.

The fetch/extraction layer should:

1. label remote material as untrusted;
2. strip scripts, styles, forms, navigation clutter, and active content;
3. extract useful task-relevant text;
4. bound the amount of remote material entering model context;
5. preserve URL/domain/title/version provenance separately;
6. treat page text attempting to change policy, invoke tools, request secrets, or redefine the task as source content only;
7. retain enough provenance to support citations and the audit trail.

**Preference:** Use deterministic sanitization before considering an additional model-based security pipeline.

### 16.6 Search-result filtering, caching, and privacy

**Invariant:** Search snippets/results from domains outside the effective Persona allowlist must not be supplied to the model as research evidence. The allowlist constrains both search-result content and subsequent fetch/read targets.

If the application uses an external search-provider endpoint, that provider is backend infrastructure rather than a model-selected content source. Provider credentials/endpoints remain application configuration and do not expand the Persona's content-domain allowlist.

**Requirement:** Web-research network disclosure is minimized. The application should send only the query/URL and protocol metadata needed to perform the authorized search/fetch; it must not upload entire conversations, Persona memories, local documents, or unrelated project context to a search provider as a convenience.

**Requirement:** Cached web content retains source URL/domain/provenance and remains subject to the current Persona allowlist when reused. Revoking a domain must prevent cached content from that domain from being supplied as newly authorized research evidence.

**Requirement:** If network research is unavailable or fails, the answer must distinguish local/model reasoning from verification that could not be completed.

---

## 17. Persona Memory

### 17.1 Scope

**Invariant:** Durable long-term memory is scoped to the owning Persona.

A `Godot Tutor` memory set is separate from a `General Assistant` memory set unless the user explicitly creates equivalent memories in both. Approved memory is therefore reusable across that Persona's multiple chats when memory is enabled and the memory is relevant to the current request.

### 17.2 Intended content

Persona memory is primarily intended for durable user-approved personalization such as:

- learning preferences;
- explanation-depth preferences;
- coding/style preferences;
- recurring constraints;
- preferred workflows;
- stable user preferences relevant to the Persona.

**Preference:** Project-specific implementation facts should remain in Project knowledge rather than being duplicated into Persona memory.

### 17.3 Approval flow

The model may emit a structured memory suggestion.

Conceptually:

```text
Suggested memory
"Prefers explanations that show the Godot node hierarchy before code."

[Save] [Edit] [Dismiss]
```

**Invariant:** The suggestion is not durable memory until the user explicitly saves it.

### 17.4 User control

**Requirement:** The user can:

- enable/disable memory per Persona;
- review approved memories;
- edit approved memories;
- delete approved memories;
- approve/edit/dismiss proposed memories.

Disabling memory must prevent approved memories from being supplied as model context for that Persona until re-enabled.

**Requirement:** When Persona memory is disabled, existing approved memories remain user-visible/stored unless deleted, but they are not retrieved into model context and the application does not automatically solicit or persist new memory proposals. The user may still inspect/edit/delete the stored memory records manually.

### 17.5 Memory and permissions

**Invariant:** Memory content never grants tools, knowledge access, web access, or host capability.

---

## 18. Multimodal Input

**Requirement:** The workspace supports images/screenshots as conversation evidence when the active local model supports vision.

The initial architecture assumes the user's intended models provide vision capability; it does not require a separate fallback vision model.

Potential inputs include:

- screenshots of Godot scenes/inspectors;
- screenshots of Rider/editor state;
- error dialogs;
- diagrams;
- images attached for general assistance.

**Invariant:** Images are evidence and cannot create permissions.

**Requirement:** The model runtime reports capabilities sufficiently for the application to determine whether the selected model can satisfy the requested modality.

If an active model cannot support a required modality, the application must report the limitation rather than silently pretending the input was interpreted.

---

## 19. Passive IDE and Godot Awareness (Future)

### 19.1 Goal

**Requirement:** The architecture permits future local, free/open-source, read-only observation of development context as deeply as can be implemented reliably without turning the assistant into an actor.

Possible Rider/editor observations include:

- active file;
- selected text/cursor context;
- open tabs;
- project tree metadata;
- diagnostics/errors;
- relevant read-only source context;
- recent visible/editor state where a reliable local interface exists.

Possible Godot observations include:

- current scene;
- scene tree;
- selected node;
- inspector/property state;
- project settings;
- output/debugger messages;
- current engine version;
- other structured read-only state exposed reliably by local interfaces.

### 19.2 Permanent boundary

**Invariant:** Passive observation adapters may expose only observation/read operations.

They must not expose model-reachable equivalents of:

```text
editFile()
writeFile()
executeCommand()
runProject()
stopProject()
setProperty()
modifyScene()
clickUI()
controlIDE()
controlGodot()
```

**Invariant:** Observation depth may increase over time; action authority may not.

### 19.3 Provenance and freshness

Observation results should include source identity and freshness/timestamp metadata when practical so the model can distinguish current observed state from indexed or older project knowledge.

Observation data remains untrusted evidence rather than runtime authority.

---

## 20. Local Model Runtime and llama.cpp

### 20.1 First runtime

**Requirement:** `llama.cpp` is the first supported local inference runtime.

The application should support local models exposed through the selected `llama.cpp` integration without requiring cloud inference.

### 20.2 Runtime abstraction

**Requirement:** Model/runtime-specific protocol details are isolated behind an application-owned adapter.

The rest of the product should depend on application-owned model/request/event types rather than direct `llama.cpp` transport schemas.

The abstraction exists to protect application boundaries, not to introduce speculative multi-provider infrastructure.

### 20.3 Capability reporting

A model/runtime should expose or allow the application to determine relevant capabilities such as:

- text chat;
- streaming;
- context-window limits;
- vision/image support;
- structured/tool-call support or the harness compatibility needed to emulate it reliably;
- structured/model-emitted reasoning support when exposed by the model/template/runtime.

**Requirement:** Research/tool features must not silently operate on a model that cannot reliably participate in the required tool protocol.

If the selected model lacks a required capability, the application should clearly report the limitation or prevent the incompatible operation.

### 20.4 Local-only model policy

**Invariant:** The configured inference runtime/model endpoint runs on the same local machine as the workspace and is reached through a local process, loopback interface, or equivalent local IPC boundary. A LAN/remote inference host is outside the current architecture.

**Invariant:** Selecting/configuring a model must not route prompts, images, knowledge, memory, reasoning content, or project data to remote/cloud LLM services.

**Invariant:** If the selected local model is missing, fails to load, crashes, or lacks a required capability, the application must not silently fall back to another model or any remote service. The failure/required user choice must be surfaced explicitly.

**Requirement:** Runtime request cancellation and runtime failure propagate back to the owning turn so the conversation records a truthful stopped/failed state rather than hanging or claiming completion.

### 20.5 Model runtime settings

**Requirement:** The frontend exposes relevant local model/runtime configuration required to operate `llama.cpp` effectively.

Runtime settings are settings whose effect concerns model loading, server/runtime behavior, or resource use rather than one individual generation. Depending on the concrete `llama.cpp` integration, examples may include:

- context-size/runtime context configuration;
- CPU thread configuration;
- GPU offload/layer configuration;
- batch-related configuration;
- model loading/runtime options;
- other supported local-runtime parameters that materially affect performance or capability.

**Requirement:** Settings that require a model/runtime reload or restart must be represented distinctly from request-scoped generation settings. The UI must not imply that a restart-required setting has taken effect when it has not.

**Preference:** Expose safe/common runtime settings directly and place rarely needed or model-specific settings under an advanced section rather than overwhelming the default settings surface.

**Invariant:** Host/runtime loading settings do not participate in the model-preset → Persona → conversation sampling inheritance chain. They are backend/runtime configuration and may require reload/restart. A Persona or conversation may select a model/preset, but changing a Persona must not silently mutate host-level CPU/GPU/thread/process settings.

### 20.6 Generation and sampling parameters

**Requirement:** The frontend exposes generation/sampling parameters supported by the active `llama.cpp` model/runtime.

The exact supported set is capability/version dependent, but the settings model should accommodate parameters such as:

- temperature;
- `top_p`;
- `top_k`;
- `min_p`;
- repeat penalty;
- repeat-window / repeat-last-N settings;
- presence penalty;
- frequency penalty;
- seed;
- maximum generated tokens;
- supported advanced samplers or sampler-chain settings where useful.

**Requirement:** Unsupported parameters are hidden, disabled, or clearly marked unsupported rather than silently accepted and ignored.

**Requirement:** Generation settings can be defined as model-preset defaults, overridden by Persona defaults, and overridden again for an individual conversation according to the precedence rules in Section 7.2.

**Requirement:** Conversation-level generation overrides must not mutate the Persona or model preset from which they inherited.

### 20.7 Model-emitted reasoning / Thinking

**Requirement:** When the selected local model/template/runtime explicitly emits reasoning content separately from the final answer, the application preserves and presents that emitted content as an optional **Thinking** stream.

This feature is intended to help the user inspect the model's visible reasoning behavior, diagnose looping/repetition, and understand when a reasoning-capable model is spending excessive effort before answering.

The UI should support, when the runtime/model provides the necessary information:

- live streaming of emitted reasoning content;
- a clickable Thinking indicator/icon that expands or collapses a `Thinking` section associated with the assistant turn;
- continuing access to Stop Generation while Thinking is streaming;
- visible elapsed reasoning/generation time;
- visible reasoning token count or equivalent usage metric when available;
- reasoning mode controls such as `Auto / On / Off` when supported;
- reasoning budget controls when supported by the model/runtime;
- durable preservation of emitted reasoning with the generated assistant response, subject to normal conversation deletion/retention behavior;
- clear association of Thinking with the exact assistant response/model configuration that emitted it, including after response regeneration.

**Invariant:** The application displays only reasoning content actually emitted by the local model/runtime. It must not fabricate, reconstruct, or claim access to otherwise-hidden internal reasoning.

**Invariant:** Model-emitted reasoning is model output, not evidence or authority. It must not be presented as a citation, research source, provenance record, or verified fact.

**Requirement:** If a model does not emit a separate reasoning channel/content form, the UI must not imply that hidden reasoning is available.

### 20.8 Model artifact identity and provenance

**Requirement:** A registered local model has a stable application identity that is distinct from its mutable filename, path, or display name.

**Requirement:** Where practical, model registration records enough artifact metadata to identify what was actually used, including a content hash and basic format/model metadata such as size, model family/architecture, and quantization when available. Historical assistant responses should retain or reference this stable artifact identity.

**Invariant:** A model artifact, its filename, embedded metadata, chat template, or other model-supplied content cannot grant tools, knowledge access, web access, memory authority, or host capability.

### 20.9 Model qualification

Declared model/runtime capability and demonstrated application compatibility are distinct. A model may technically expose a tool-call or vision interface while still being unreliable for the workspace's workflows.

**Requirement:** The application may maintain lightweight qualification results for important capabilities such as basic chat, structured tool use, bounded research, vision, or project-oriented evaluation. Research/tool features must not be represented as reliable merely because the runtime declares a compatible format.

**Preference:** Qualification should use a small repeatable local test suite rather than a heavyweight benchmarking system. Exact qualification criteria and whether results are user-visible are phase-defined.

---

## 21. Research Transparency, Citations, and Audit Trail

**Requirement:** Research activity is recorded mechanically from actual application/tool activity rather than reconstructed afterward by the model.

A research run should be able to record structured events including:

```text
research_run_id
conversation_id
persona_id
research_mode
research_step
model_id
tool_name
query
knowledge_scope / source ID
source authority
source version
source revision / content hash when available
web domain / result ID when applicable
result status
timestamp
```

### 21.1 Inline citations

**Requirement:** Final answers use lightweight inline citations/references when sources materially support claims.

**Invariant:** A citation may be attached only to a claim actually supported by the cited executed source/tool result. The model may not use a citation decoratively to make an inference appear sourced.

**Requirement:** Material inference, uncertainty, assumptions, and source disagreement should be identified as such rather than disguised as directly sourced fact.

Inline presentation should remain readable and should not overwhelm normal conversation.

### 21.2 Detailed trace

**Requirement:** The UI provides a detailed research/source trace on demand.

The trace may display:

- consulted sources;
- search queries;
- source authority/type;
- source/document IDs;
- version information;
- unavailable or rejected sources;
- source disagreements;
- tool failures;
- research timing/status.

**Invariant:** The research trace must not fabricate or reconstruct hidden chain-of-thought. Model-emitted `Thinking` content, when available, is a separate assistant-output surface governed by Section 20.7 and is not part of research provenance.

**Invariant:** Displayed citations/provenance must derive from actual executed activity and must not be fabricated by the model.

**Requirement:** Provenance identifies the source revision/content actually consulted where practical. If a local file or web page later changes, an old citation must not silently appear to prove that the newly changed content was what the model originally read.

---

## 22. Local Web Application and UX Model

**Requirement:** The frontend is a locally hosted web application inspired by the interaction model of OpenWebUI/ChatGPT while remaining specific to this product's Persona/knowledge/research model.

### 22.1 Primary navigation

Minimum end-state areas include:

- Personas;
- Persona-nested chat history;
- Knowledge Library;
- local Models;
- Persona Memory;
- Settings;
- research/source traces;
- model/runtime and generation settings.

### 22.2 Persona management

**Requirement:** The UI provides a first-class Persona editor for creating, inspecting, editing, archiving, and deleting Personas within the lifecycle rules of this architecture.

The Persona editor should expose at minimum:

- name, avatar, description/purpose;
- system prompt/instructions;
- default local model/model preset;
- Persona generation/sampling defaults;
- enabled application-owned tools;
- explicit knowledge grants;
- automatic/forced research preferences;
- web-research enablement and domain allowlist;
- memory enablement and approved-memory management;
- response/tutoring style and other Persona behavior settings.

**Requirement:** The UI should make permission-bearing settings visually distinguishable from stylistic/model-generation settings so changing temperature, avatar, or response style cannot be confused with granting tools/knowledge/web access.

### 22.3 Persona/chat interaction

The intended flow is:

```text
Choose Persona
    ↓
Create one of many Chats, or open an existing Chat
    ↓
Conversation remains owned by that Persona
```

A Persona may have many independent chats visible beneath it in history/navigation. Opening an old chat automatically activates its owning Persona.

### 22.4 Chat controls

The chat experience should support:

- streaming responses;
- separate/collapsible streamed `Thinking` content when explicitly emitted by the model;
- Stop Generation during answer or Thinking generation;
- reasoning/generation timing and token metrics when available;
- active Persona visibility;
- effective model visibility and per-conversation override;
- manual Research control;
- file/image attachments;
- edit message;
- regenerate response;
- light inline citations;
- source/research panel on demand.

### 22.5 Knowledge management

The UI should allow the user to:

- browse the `Global / Persona / Project` hierarchy;
- add/remove knowledge sources;
- inspect indexing status;
- inspect source metadata;
- grant/revoke Persona access to directories/collections;
- understand the effective access of a Persona.

### 22.6 Memory management

The UI should expose Persona memory as explicit user-controlled state rather than hidden assistant memory.

### 22.7 Model and generation settings

**Requirement:** The frontend provides a dedicated model/settings surface that distinguishes:

- model/runtime settings that affect `llama.cpp` loading, resource use, or server behavior;
- generation/sampling settings that may be changed per model preset, Persona, or conversation;
- reasoning controls and budgets when supported by the selected model/runtime.

**Requirement:** The UI displays the effective setting source/inheritance clearly enough that the user can tell whether a value comes from the model preset, Persona, or conversation override.

**Preference:** Common sampling controls such as temperature, `top_p`, `top_k`, repetition controls, and response-token limits should be readily accessible, while more specialized sampler/runtime options may be placed under an Advanced section.

---

## 23. Persistence and Data Lifecycle

### 23.1 Durable local state

**Requirement:** Durable application state is stored locally and includes at minimum:

- Personas;
- Persona settings;
- conversations/messages;
- conversation attachments and attachment metadata retained by the application;
- conversation model overrides;
- model presets and supported runtime/generation configuration;
- Persona and conversation generation/sampling overrides;
- model-emitted reasoning/Thinking content and associated metrics when retained with a response;
- Persona memory proposals and approved memories;
- knowledge-source metadata;
- knowledge grants;
- indexes;
- research traces;
- model/runtime configuration.

### 23.2 User control and deletion

**Requirement:** The user must be able to remove durable user-facing state such as:

- conversations;
- Personas;
- approved memories;
- knowledge sources/collections;
- research traces where retention controls are provided.

Storage mechanics, confirmation UX, and optional archive presentation are phase-defined. The semantic deletion/ownership rules in Sections 23.3-23.6 are architectural requirements, and deletion must not leave hidden model-facing copies that continue to influence future answers.

### 23.3 Derived state

Indexes, caches, summaries, and other derived representations must remain traceable to durable source records and must be invalidated or updated when the underlying source/grant is removed or changed.

**Invariant:** Revoking a Persona's knowledge access must prevent that Persona from searching/reading the revoked source in future research, including through stale indexes/caches. Historical visible conversation output is not silently rewritten by grant revocation.

### 23.4 Ownership-aware deletion and archival

Durable ownership relationships must not be broken silently.

**Requirement:** Deleting a conversation removes or invalidates its owned messages, attachments stored by the application, derived summaries/context caches, emitted Thinking records, conversation-owned generation metadata, and conversation-owned research runs/traces so they cannot influence future model context.

**Requirement:** Because chats belong to exactly one Persona and are not re-parented implicitly, deleting a Persona that still owns chats/memories must require an explicit user decision such as cancelling deletion or cascading removal of the owned state. Archiving/disabling a Persona may be offered as a non-destructive alternative.

**Requirement:** Deleting a knowledge source/collection invalidates its derived chunks/indexes and any grants to the deleted resource. Historical citations may remain as records that the source once existed, but they must clearly resolve as deleted/unavailable rather than granting access.

**Requirement:** Removing a model/model preset that is referenced by a Persona or conversation must not cause silent substitution. The application must expose the broken/unavailable reference and require an explicit replacement or removal of the override.

### 23.5 Operational logging and privacy

**Requirement:** Operational/debug logs are separate from user-facing research traces and should minimize raw prompt, memory, document, attachment, and model-output content by default. Secrets must never be logged.

**Invariant:** Operational logs remain local and cannot be uploaded as telemetry/crash reports by the standard application.

### 23.6 Schema evolution and user data durability

**Requirement:** Changes to durable data schemas use explicit local migrations. Application upgrades must not silently discard or reset Personas, conversations, memories, knowledge metadata, grants, or research records merely because the schema changed.

**Requirement:** Failed migrations must fail visibly and preserve recoverability of the prior durable data as far as practical; exact backup/rollback mechanics are phase-defined.

**Requirement:** Backup/export/import, when implemented, is user-initiated and local by default. Exported data must preserve enough identity/provenance to avoid silently merging incompatible Personas, knowledge sources, or conversations on import.

### 23.7 Crash consistency and interrupted operations

**Requirement:** Security-, ownership-, and durability-sensitive state changes should be committed transactionally where practical. A crash, cancellation, or process termination must not leave partially applied grants, revocations, deletions, memory approvals, ownership changes, or generation/research records in a state that silently broadens future access or misrepresents completion.

**Requirement:** On restart after an interrupted state-changing operation, ambiguous partial state fails visibly or conservatively rather than being treated as successfully completed.

**Preference:** SQLite transactions and simple application state machines are preferred over additional infrastructure for satisfying this requirement.

---

## 24. Technology Direction

The following are preferences or initial implementation requirements rather than permanent vendor commitments unless separately marked.

**Requirement:** The initial application stack uses Python with FastAPI for the backend/API layer, Jinja2 for server-rendered templates, and Alpine.js for lightweight client-side interactivity.

**Preference:** The frontend should remain server-rendered/lightweight rather than adopting a full single-page application framework unless measured UI complexity demonstrates that the simpler approach has become a maintainability constraint.

**Preference:** Use Server-Sent Events (SSE) for unidirectional token/reasoning/tool-event streaming where practical; use WebSockets only where genuine bidirectional real-time behavior requires them.

```text
Harness/orchestration: application-owned lightweight Python runtime
Backend/API:           Python / FastAPI
Templates:             Jinja2
Frontend behavior:     Alpine.js + HTML/CSS
Streaming:             SSE primarily; WebSocket when justified
Database:              SQLite
Full-text search:      SQLite FTS5
Embeddings:            not initially
LLM runtime:           llama.cpp first, local only
Documents:             local resources behind backend ingestion/services
Knowledge model:       logical Global / Persona / Project hierarchy
Project context:       indexed read-only knowledge with typed metadata
Persona memory:        local, user-approved, Persona-scoped
Web research:          backend-owned whitelist-constrained search/fetch/extraction
Multimodal:            active local model vision capability
IDE/engine awareness:  future local read-only observation adapters
```

**Preference:** One application process plus the local `llama.cpp` model runtime is preferable to a distributed collection of services unless measured requirements justify additional processes.

**Requirement:** Required application software dependencies and local runtime services remain free/open-source, consistent with Section 4.3.

**Preference:** Avoid introducing a separate vector database, message broker, workflow engine, scheduler, container fleet, additional model service, or heavyweight client framework without measured need.

**Requirement:** Technology choices must not weaken the stable backend API, Persona authorization, knowledge boundaries, or read-only security invariants. A future frontend/backend technology change is allowed if it preserves those contracts and is explicitly approved where required by project policy.

---

## 25. Repository Boundary

**Requirement:** Product responsibilities remain separated enough that the UI, application control plane, harness, model-runtime adapter, knowledge subsystem, and research subsystem can evolve without being conflated.

Because the initial stack is intentionally lightweight, these boundaries may live inside one Python application/package tree rather than requiring separate services or independently published packages.

A preferred repository shape is conceptually:

```text
/AGENTS.md
/pyproject.toml
/app
  /api
  /web
    /templates
    /static
  /workspace
  /harness
  /model_runtime
  /knowledge
  /research
  /memory
  /observations
/tests
/docs
  /project
    /Architecture.md
    /STATUS.md
    /DEVELOPMENT.md
    /implementation
    /adr
  /human
    /notes
    /designs
```

The exact path layout is a preference. The responsibility boundaries are the requirement.

### 25.1 No vendored agent-framework requirement

**Invariant:** The repository does not require a maintained Pi fork or another third-party agent-framework fork as part of the product architecture.

A third-party library may later be introduced as an ordinary reviewed dependency if it satisfies a concrete need and does not become an uncontrolled capability boundary, but the product architecture must remain application-owned.

---

## 26. Reference Implementations and Inspirations

The following projects are explicitly recognized as design inspirations/reference implementations. They may be studied for proven ideas, interaction patterns, and implementation techniques without inheriting their product boundaries.

**Invariant:** These references are non-normative. They are not product specifications, architectural authorities, or required dependencies. Requirements in this file take precedence over upstream behavior. Future upstream changes do not alter this architecture automatically.

### 26.1 OpenWebUI

Reference repository: <https://github.com/open-webui/open-webui>

Primary inspiration: **AI workspace/interface and Persona-like configuration UX.**

Use as a reference for:

- chat/navigation interaction patterns;
- model/Persona-style configuration UX;
- knowledge-management UX;
- attachment handling;
- model selection and sampling controls;
- visible model-emitted reasoning/Thinking interaction patterns;
- conversation editing/regeneration/branching;
- settings and source presentation.

It is not an architectural dependency.

### 26.2 OpenLumara by Rose22

Reference repository: <https://github.com/Rose22/openlumara>

Primary inspiration: **lightweight, local-first AI/agent framework design.**

Use as a reference for:

- lightweight/local-first architecture;
- modular capability boundaries;
- local model integration patterns;
- Persona/character-like session restoration patterns where useful.

It is not an architectural dependency.

### 26.3 Pi / pi.dev

Reference repository: <https://github.com/earendil-works/pi>

Primary inspiration: **harness/toolkit and model-tool orchestration mechanics.**

Use as a reference for:

- model/tool orchestration loops;
- streaming agent/runtime events;
- tool-call handling;
- transient context management;
- bounded model/tool interaction patterns.

It is not an architectural dependency and is not the application backend.

---

## 27. Security Model

The architecture explicitly considers:

- model-generated command execution;
- model-generated file modification;
- arbitrary local-file access;
- path traversal through knowledge/research tools;
- Persona grant bypass;
- stale indexes leaking revoked knowledge;
- malicious web prompt injection;
- SSRF/private-network access;
- redirects escaping web allowlists;
- active or malicious downloaded content;
- dynamic tool/plugin mechanisms reintroducing execution;
- hostile project/source text being confused with trusted instructions;
- memory content being confused with permissions;
- passive IDE/engine observation becoming control capability;
- incompatible model capabilities causing fabricated research behavior;
- malicious web pages attempting to invoke the localhost API through cross-origin requests or DNS-rebinding-style attacks;
- local source path/symlink escape;
- untrusted document/parser content attempting code execution;
- silent model fallback or continued hidden execution after cancellation;
- backend credentials leaking into prompts, logs, traces, or citations;
- model/source/web content causing frontend script/HTML execution.

Defense layers are:

```text
Layer 1 — Capability absence
No generic execution, modification, shell, Git, browser automation, or IDE control exists in the model-facing runtime.

Layer 2 — Explicit Persona capability surface
Only tools enabled for the active Persona are model-visible.

Layer 3 — Explicit knowledge grants
Only knowledge granted to the active Persona is addressable.

Layer 4 — Backend authorization and policy
Arguments, resource identity, budgets, grants, and tool permissions are validated before execution.

Layer 5 — Safe web gateway
Domain allowlists, network targets, redirects, MIME, size, and extraction are controlled.

Layer 6 — Context/trust separation
Retrieved content, attachments, observation data, and web text are evidence, not runtime authority.

Layer 7 — User-approved memory
The model cannot silently persist long-term memory or use memory to create permissions.

Layer 8 — Provenance and audit
Research/citation records come from executed activity.

Layer 9 — Local web/API trust perimeter
Loopback binding, origin/request protections, local assets, and deny-by-default cross-origin behavior protect the localhost control plane.

Layer 10 — Automated regression tests
Security and capability boundaries are continuously tested.
```

---

## 28. Permanent Test Principles

Testing exists at every relevant layer.

### 28.1 Security/capability absence

Tests must prove that the model-facing runtime cannot obtain or invoke generic host-control capability, including equivalent aliases or indirect routes.

At minimum, test absence of equivalents to:

```text
filesystem read/write/edit/delete by arbitrary path
shell / terminal / exec / process spawn
code execution / eval / interpreter
Git/VCS
package installation
arbitrary network fetch/browser automation
dynamic tool/plugin loading
IDE or Godot control
```

### 28.2 Persona isolation

Maintain tests that verify:

- a Persona can search granted knowledge;
- a Persona cannot search ungranted knowledge;
- `Global` knowledge is not automatically visible;
- revoking a grant prevents future retrieval;
- tool/web permissions remain Persona-scoped;
- loading a chat restores its owning Persona;
- one Persona can own multiple independent chats without cross-chat message leakage.

### 28.3 Conversation behavior

Test:

- durable chat ownership;
- editing an earlier user message truncates later active history and does not leave superseded messages in model context;
- regenerating an assistant response replaces the active response for that turn without leaving stale response/context state active;
- per-conversation model overrides do not mutate Persona defaults;
- per-conversation generation overrides do not mutate Persona/model-preset defaults;
- effective generation-setting precedence is deterministic;
- historical assistant responses retain the effective Persona configuration snapshot/hash and model/settings metadata used to generate them while new turns use current Persona policy;
- edits/regeneration do not reuse derived summaries/context caches based on superseded history.

### 28.4 Retrieval

Maintain deterministic test corpora that verify:

- relevant documents are found;
- knowledge-grant filtering works;
- metadata filtering works;
- wrong-version material is excluded or clearly identified;
- project/design/planning/decision distinctions survive retrieval;
- nearby context can be read after search;
- irrelevant knowledge areas do not dominate results;
- provenance retains the source revision/content identity actually retrieved when available.

### 28.5 Research behavior

Repeatable scenarios should cover:

- model-only/general answer where research is unnecessary;
- automatic local-documentation research;
- project-context research;
- project plus documentation;
- forced research;
- version conflict;
- web verification;
- source disagreement;
- insufficient evidence;
- tool failure without capability escalation.

The canonical Godot debugging scenario should include a project question equivalent to:

> "My character jumps and takes damage."

### 28.6 Web safety

Use deterministic hostile fixtures to test sanitizer and injection defenses without depending on the public internet.

Test allowlist enforcement and redirect handling explicitly. Verify that web research cannot inherit authenticated browser cookies/sessions or other unrelated browser authority.

### 28.7 Memory

Test that:

- model suggestions are not durable without approval;
- approved memory is Persona-scoped;
- disabled memory is not supplied to the model;
- deleted memory stops affecting future context;
- memory cannot expand permissions.

### 28.8 Model capabilities and generation settings

Test that incompatible model capabilities are surfaced explicitly rather than producing false claims of image interpretation or research/tool execution. Verify that the configured model runtime remains local/same-machine under the current architecture.

Test that:

- unsupported generation parameters are not silently treated as effective;
- restart/reload-required runtime settings are distinguishable from request-scoped sampling settings;
- model-preset → Persona → conversation setting precedence behaves deterministically;
- changing a conversation override does not mutate inherited defaults.

### 28.9 Model-emitted reasoning / Thinking

Where the selected test model/runtime exposes separate reasoning content, test that:

- emitted reasoning streams separately from final-answer content;
- the user can expand/collapse it;
- Stop Generation remains functional while it is streaming;
- available timing/token metrics correspond to actual runtime events;
- the displayed reasoning is associated with the correct generated assistant response, including after regeneration;
- models without a reasoning channel do not produce a fake Thinking surface;
- reasoning content is not treated as research provenance or a citation.

### 28.10 Multimodal

Where supported by the selected test model/runtime, verify that image attachments enter model context without becoming silent durable knowledge or permissions.

### 28.11 Passive observation adapters

When implemented, adapters require tests proving read-only behavior and absence of command/write/control equivalents.

### 28.12 Local source and parser safety

Test that:

- registered source boundaries cannot be escaped through traversal or platform path aliases;
- symlink/junction/reparse-point behavior cannot expose unregistered resources;
- unsupported/hostile document content is treated as passive data and cannot execute;
- source deletion/change invalidates or marks derived retrieval state appropriately.

### 28.13 Cancellation, budgets, and failure truthfulness

Test that:

- Stop Generation cancels the owning runtime request and research/tool loop;
- cancelled/failed turns remain visibly incomplete rather than becoming completed responses;
- research/tool-call budgets terminate non-progressing loops;
- repeated tool-call loops cannot continue indefinitely;
- runtime/model failure does not trigger silent model or capability fallback.

### 28.14 Local web/API trust perimeter

Test that the default server binds only to the intended local interface and that unrelated browser origins cannot freely invoke state-changing application APIs. CORS/origin/CSRF-equivalent protections and streaming endpoints must follow the same local trust policy.

Test that model output, Markdown, retrieved HTML/text, filenames, and source/web content cannot execute arbitrary script/active HTML in the application UI.

### 28.15 Persistence and deletion

Test that deletions/revocations invalidate model-facing derived state, that Persona/chat ownership rules are preserved, and that schema migrations do not silently destroy durable user data.

### 28.16 Resource failure and crash consistency

Test representative failure paths such as oversized inputs, model/runtime resource failure, insufficient disk space, interrupted indexing, and process termination around state-changing operations. Verify that failures remain visible, durable state remains recoverable, and authorization does not broaden because an operation stopped halfway through.

### 28.17 Model identity and qualification

Test that replacing or renaming a model file does not silently change the recorded artifact identity of historical generations. For models used with research/tool workflows, maintain a small repeatable compatibility corpus that distinguishes declared protocol capability from demonstrated application behavior.

---

## 29. Explicit Non-Goals

The following are outside the current product architecture:

- autonomous coding;
- source-code modification by the application model;
- autonomous file creation/edit/delete;
- command or process execution by the application model;
- automated project build/test execution by the application model;
- Git/VCS automation;
- package installation by the application model;
- general-purpose filesystem access exposed to the model;
- autonomous/general browser operation;
- unrestricted network access;
- authenticated/private web browsing that reuses the user's browser sessions or external-account credentials;
- general desktop control;
- Rider/IDE control;
- Godot/engine control;
- arbitrary plugin ecosystems with host permissions;
- general MCP/plugin attachment that grants model-reachable host authority outside the application-owned tool boundary;
- model-created tools or executable extensions;
- remote/cloud LLM providers;
- cloud-first architecture;
- paid-service dependencies in the standard application;
- autonomous background agents or task schedulers as part of Persona behavior;
- interpreting a Persona's "job"/purpose as a scheduled background job;
- large distributed infrastructure;
- vector databases before demonstrated retrieval need;
- automatic multi-model/agent delegation without a separately approved architecture change;
- multi-user tenancy or account/role administration;
- LAN/public hosting as a supported default deployment mode;
- analytics/telemetry/crash-report uploads or remote UI asset/CDN dependencies in the standard application.

Changing one of these non-goals into product scope requires explicit architectural approval.

---

## 30. Implementation Roadmap Summary

The roadmap below defines architectural sequencing direction. Concrete phase contracts should be written separately before implementation of each phase.

Implementation begins at **Phase 1** from a documentation-only repository with no application implementation; no architecture-reset or legacy-code cleanup phase is required.

Phases are sequential by default. A later phase should not be substantially implemented until the current phase's acceptance criteria are satisfied unless the user explicitly authorizes overlap.

| Phase | Name | Primary outcome |
| --- | --- | --- |
| 1 | Workspace Foundation and Local Harness | Python/FastAPI application shell, Jinja2/Alpine.js UI foundation, loopback/local-web trust perimeter, backend boundary, application-owned harness, llama.cpp runtime adapter, streaming/cancellation lifecycle, explicit empty/narrow tool surface. |
| 2 | Personas, Conversations, and Model Controls | Persona persistence/configuration, multiple Persona-owned chats, per-generation effective-configuration provenance, model presets/defaults/overrides, generation/sampling controls, emitted Thinking UI, linear editing/regeneration. |
| 3 | Knowledge Library and Access Grants | Global/Persona/Project hierarchy, explicit local source boundaries, source registration, explicit Persona grants, safe passive ingestion/index foundations. |
| 4 | Retrieval and Source-Aware Project Knowledge | SQLite/FTS5 retrieval, project/source classification, relevant-context reading, version metadata foundations. |
| 5 | Research Orchestration and Provenance | Automatic/forced research behavior, bounded/cancellable tool loop with loop guards, research traces, light citations. |
| 6 | Safe Web Research | Persona domain allowlists, safe search/fetch/extraction, web provenance, injection/SSRF protections. |
| 7 | Persona Memory | Proposal/approval flow, Persona-scoped memory, memory toggle/management, memory retrieval. |
| 8 | Multimodal Conversations | Vision/image attachments and model capability enforcement. |
| 9 | Workspace UX Completion | OpenWebUI-inspired management surfaces, detailed trace UI, knowledge/memory/model/settings polish. |
| 10 | Passive Rider/Godot Awareness | Optional free/local read-only observation adapters with strict capability-absence tests. |
| 11 | Hardening and Resource Optimization | Security regression coverage, retrieval/model-qualification evaluation, graceful resource/crash failure handling, resource profiling, packaging/readiness. |

Phase documents refine this architecture. They do not supersede it.

---

## 31. Desired End State

The final product should feel like:

> **A private personal AI workspace where the user can create reusable Personas over local models, give each Persona explicit access to selected knowledge and research capabilities, maintain user-approved Persona memory, keep multiple durable Persona-owned conversations, tune local model/generation behavior, inspect model-emitted Thinking when available, and receive source-aware, version-aware, project-aware explanations without giving the assistant the ability to act on the user's machine.**

For Godot/software-development work, the defining experience should be:

> **A senior technical tutor and debugging partner that can inspect permitted project knowledge, understand design intent versus current implementation, consult the applicable Godot/GDScript documentation, verify current information on explicitly approved web domains when necessary, understand relevant screenshots, and then give a practical step-by-step answer tailored to the actual project.**

The system should be:

```text
local-hosted
privacy-friendly
free/open-source by default
lightweight
Persona-centered
modular
auditable
source-aware
version-aware
multimodal
read-oriented
non-autonomous
controllable
user-memory-controlled
```

Its defining safety property is:

> **The assistant can autonomously search, read, compare, and explain within explicitly granted read-only boundaries, but it cannot execute, modify, control, or autonomously act on the user's machine, project, IDE, engine, repositories, or external services.**

---

## 32. Intentionally Deferred Implementation Details

The following details are intentionally left to implementation-phase design because the current product decisions constrain their behavior without requiring one exact mechanism:

- exact Persona knowledge-grant inheritance representation and UI, provided access remains explicit, understandable, and fail-closed;
- exact effective Persona configuration snapshot/hash representation for historical assistant responses, provided it is sufficient for practical provenance without requiring a separately navigable Persona revision history;
- exact `llama.cpp` transport/API mode, model-loading lifecycle integration, tool-call encoding, and reasoning-content extraction mode, provided the application-owned runtime boundary remains stable;
- exact local-model artifact metadata fields/hash strategy and lightweight qualification criteria, provided stable artifact identity and truthful capability/compatibility reporting remain satisfied;
- exact set of advanced `llama.cpp` runtime/sampling controls exposed in each UI tier, provided capability detection and inheritance remain explicit;
- exact web search provider or search-engine integration, provided the standard path requires no paid research service/account and preserves the domain-allowlist, privacy, and safe-fetch requirements;
- exact supported document/file-format parser set;
- exact source-classification workflow (for example user-assigned metadata, deterministic rules, or user-approved model suggestions), provided source authority/type/status are not silently fabricated;
- exact FTS5 schema, ranking formula, chunk sizes, and relevance heuristics;
- exact linear conversation/message storage schema and edit/regeneration replacement semantics, provided superseded history cannot leak into active model context;
- exact memory-relevance/ranking mechanism;
- exact local protocol used for future Rider/Godot passive observations;
- exact backup/export/import UX, archive presentation, and retention controls, provided the ownership/deletion semantics in Section 23 remain true;
- exact localhost API protection mechanism (for example origin/CSRF/session-token details), provided the trust-perimeter requirements remain satisfied;
- exact turn/tool lifecycle database schema, transactional boundaries, and concurrency implementation, provided cancellation/status/provenance and crash-consistency semantics remain satisfied;
- exact practical resource limits/backpressure values for uploads, parsing, indexing, generation, research, and derived-state retention;
- exact packaging/distribution format;
- criteria for escalating from Jinja2/Alpine.js to a heavier client framework if measured frontend complexity eventually justifies it.

These details may evolve without changing `docs/project/Architecture.md` so long as the invariants and requirements above remain satisfied.

**Invariant:** “Implementation detail” is not a loophole for changing product semantics. Any decision that materially changes Persona/chat ownership, authorization, trust boundaries, data-retention semantics, local-only behavior, model autonomy, knowledge authority, web privacy, or another invariant/requirement in this file requires an explicit architecture change rather than being hidden inside a phase document.
