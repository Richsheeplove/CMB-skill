---
name: CMB-skill
description: "CMB (Chicken Meat with Bone / 骨肉相连) is a structured agent skill that applies Meat/Bone discipline to two scenarios: (A) Process-CMB constrains the agent's reasoning workflow (reproducible, chainable multi-step execution with deterministic JSON bones in `.cmb/`); (B) Code-CMB constrains the structure of generated/modified code (interface-first contracts as Code-Bones, single-responsibility implementation as Meat). Use this skill when a task requires multi-step reasoning that must be reproducible, when you need deterministic handoffs between steps, when generating or refactoring code that must respect stable contracts, or when reviewing code for separation between stable contracts (bones) and volatile implementations (meat). Triggers include: requests for structured multi-step plans, deterministic step chaining, code generation, refactoring, adding a feature, implementing X, reviewing code structure, designing an interface/schema/API, or any explicit mention of CMB, 骨肉相连, Meat/Bone, or step chaining."
---

# CMB Skill (骨肉相连)

## Overview

CMB applies a single discipline — **Meat (volatile reasoning) vs Bone (stable contract)** — to two scenarios:

- **Process Mode (Process-CMB)** — constrains the *agent's reasoning workflow*. Meat is each LLM step; Bone is a deterministic JSON artifact written to `.cmb/<step_id>/output.json`. This is the original CMB.
- **Code Mode (Code-CMB)** — constrains the *structure of code the agent produces*. Meat is volatile implementation (business logic, algorithm bodies, prompt text, glue code). Bone is the stable contract layer in source: interfaces/types, schemas, protocol messages, pure-function modules, exported constants. Bones are *changed deliberately*; meat is changed freely.
- **Hybrid Mode (default)** — Process-CMB at the task level; whenever a step's job is to write or modify code, Code-CMB applies inside that step's Meat.

Both modes share the same three principles, re-projected into their domain:

| Principle | Process-CMB | Code-CMB |
|---|---|---|
| **Ambiguity First** | Resolve all blocking unknowns before planning steps | **Interface First**: write the contract Bone (types, signatures, schema, error model) *before* any implementation |
| **One Concern Per Step** | One Meat does one thing | **Single-Responsibility Slice**: one file/function = one concern; pure logic separated from IO/side-effects |
| **Bone as Contract** | Changing a bone's schema requires reviewing every downstream step | **Interface as Contract**: changing a public interface/type/schema requires explicitly listing affected callers and updating them — never silently |

**See full references**:
- [references/cmb-workflow.md](references/cmb-workflow.md) — Process-CMB details, bone schema, lifecycle, example chain
- [references/cmb-code-mode.md](references/cmb-code-mode.md) — Code-CMB: Code-Bone definition, bone/meat judgment checklist, example chain

---

## Workflow

### Phase -1 — Mode Selection

Before anything else, decide which mode applies:

- **Process Mode** — task is "complete a workflow / analysis / decision"; deliverable is a conclusion, plan, or list of artifacts.
- **Code Mode** — task is "produce or modify code"; deliverable is the code itself.
- **Hybrid Mode (default, recommended)** — anything non-trivial: use Process-CMB to decompose the task; whenever a step writes code, apply Code-CMB inside that step's Meat.

**Trigger heuristic**: if the user's request contains any of "write code / modify code / refactor / add a feature / implement X / build module Y / fix bug in Z / 写代码 / 改代码 / 重构 / 加功能 / 实现", default to **Hybrid Mode**, and the step plan **must include an interface-first step** (a step whose Bone is the code contract, not the implementation).

Record the chosen mode at init time:

```bash
python3 <skill_path>/scripts/init_cmb.py --task "<task name>" --description "<desc>" --mode hybrid
```

`--mode` accepts `process`, `code`, or `hybrid` (default). The choice is written to `.cmb/plan.json` under the `mode` key.

### Phase 0 — Requirement Gathering (First Meat)

Before creating any steps:
1. Analyze the user's request deeply
2. Identify all key ambiguities that would change execution
3. Present ambiguities using the option-based format (see below)
4. **Do not proceed until all critical ambiguities are resolved**

**Ambiguity presentation format** — always include a custom/free-input option:

```
Q1: Which framework should be used?
  a) React
  b) Vue
  c) Angular
  d) Other (please specify)
```

Use `ask_user_question` tool when available; otherwise present as numbered/lettered options in text.

In **Code Mode / Hybrid Mode**, ambiguities to surface include not only product requirements but also contract-shaping decisions: target language and version, public API surface, error model, sync vs async, data schema, and which existing modules will be touched.

### Phase 1 — Initialize CMB Directory

Once requirements are confirmed, initialize the CMB directory:

```bash
python3 <skill_path>/scripts/init_cmb.py --task "<task name>" --description "<desc>" --mode <process|code|hybrid>
```

Default location: `.cmb/` in the current project directory. Default mode: `hybrid`. If write permission is denied, use a temp path and note it.

### Phase 2 — Plan Steps

Design the step chain. Each step must have:
- A unique `step_id` (e.g. `step_001`, `step_002`)
- A clear `name`
- Defined input fields (what it reads from the previous Bone)
- Defined output fields (what it writes to its own Bone)

In **Code Mode / Hybrid Mode**, the plan **must** contain at least one step whose purpose is to produce the Code-Bone (interfaces / types / schema) *before* any implementation step. A typical Code-CMB chain looks like:

```
step_001 Requirement Analysis
step_002 Interface / Type / Schema Bone     ← Code-Bone, no implementation
step_003 Implementation (Meat)               ← fills in behavior under fixed contract
step_004 Tests against Interface             ← verifies the contract, not the implementation
```

Register each step:
```bash
python3 <skill_path>/scripts/run_step.py create step_001 --name "Requirement Analysis"
python3 <skill_path>/scripts/run_step.py create step_002 --name "Interface Contract"
```

### Phase 3 — Execute Steps (Meat → Bone loop)

For each step:
1. **Meat**: Read the previous step's output bone (if any), perform the reasoning/analysis/generation
2. **Bone**: Write the structured output using run_step.py:

```bash
python3 <skill_path>/scripts/run_step.py write step_001 --data '<json output>'
```

3. If this step produced or modified source-level Code-Bones (interface/type/schema files, pure-function modules, exported constants), register them so downstream steps can detect contract drift:

```bash
python3 <skill_path>/scripts/run_step.py bind-code step_002 \
    --files src/auth/types.py,src/auth/schema.py \
    --symbols "AuthToken,LoginRequest" \
    --note "Interface-first contract for auth module"
```

`bind-code` appends an entry to the step's `output.json` under `code_bones` with `path`, `exists`, content `hash`, and optional `symbols` and `note`.

4. Proceed to the next step, reading this bone as input

To inspect current state:
```bash
python3 <skill_path>/scripts/run_step.py list
python3 <skill_path>/scripts/run_step.py read step_001
```

---

## Hard Rule for Code Mode

**Code Mode (and Hybrid Mode for any code-producing step) forbids entering an implementation Meat without first having a Code-Bone written.**

That is: the Code-Bone (interface / type / schema / module-boundary file) must exist on disk and be registered via `bind-code` before any step whose deliverable is implementation logic. This is the code-domain equivalent of "Ambiguity First" — implementing under an undecided contract is the same failure mode as reasoning under an unresolved ambiguity.

If the contract genuinely cannot be fixed in advance (rare), say so explicitly in the prior step's Bone (`open_questions`) and resolve it before proceeding.

---

## Bone Output Rules

### Process-Bone (`.cmb/<step_id>/output.json`)

Every Process-Bone must be:
- **Valid JSON** — no prose, no markdown
- **Self-contained** — includes all data needed by the next step
- **Typed** — use arrays for lists, strings for text, booleans for flags
- Written via `run_step.py write` (auto-adds `step_id` and `written_at`)

Prefer flat structures; nest only when grouping is semantically necessary.

### Code-Bone (source files)

Code-Bones live in the source tree, not in `.cmb/`. They must be:
- **Stable** — changed only deliberately, not as a side effect of implementing something else
- **Minimal** — contain only what callers need to depend on (signatures, types, schema, errors), not implementation
- **Side-effect-free** at the boundary — IO, network, randomness, time must not leak through the contract
- **Registered** — referenced from the producing step's `output.json` via `bind-code`

See [references/cmb-code-mode.md](references/cmb-code-mode.md) for the full bone/meat judgment checklist.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/init_cmb.py` | Initialize `.cmb/` directory and `plan.json`; supports `--mode {process,code,hybrid}` |
| `scripts/run_step.py` | Create steps, write/read bones, list status; `bind-code` registers source-level Code-Bones |

To find the skill's script path:
```bash
find ~/.agent/skills/cmb-skill/scripts -name "*.py"
find ~/.claude/skills/cmb-skill/scripts -name "*.py"
```

---

## Step Design Heuristics

- **One concern per step**: don't combine analysis + implementation in one Meat
- **Interface before implementation** (Code Mode): the contract step is non-negotiable
- **Bones are contracts**: if a step's output schema *or* a registered Code-Bone changes, downstream steps and callers must be revisited
- **Ambiguity before action**: any uncertainty that affects implementation should be resolved in Phase 0, not discovered mid-chain
- **Resumability**: because bones are files (JSON for process, source for code), the chain can be resumed from any step by re-running from that step's Meat

