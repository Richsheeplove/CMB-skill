---
name: CMB-skill
description: "CMB (Chicken Meat with Bone / 骨肉相连) is a structured agent workflow skill for reproducible, chainable multi-step task execution. Use this skill when a user task requires multiple sequential reasoning steps where each step's output feeds the next, or when you need to ensure agent consistency and reproducibility across complex workflows. Triggers include: requests for structured multi-step plans, tasks needing deterministic handoffs between steps, any workflow where reproducibility and step-by-step traceability matter, or when the user explicitly mentions CMB, 骨肉相连, or step chaining."
---

# CMB Skill (骨肉相连)

## Overview

CMB structures complex tasks as a chain of **Meat** (LLM reasoning steps) and **Bone** (deterministic JSON artifacts written to `.cmb/`). Each Meat step reads the previous Bone, performs reasoning, and writes the next Bone. This makes every step reproducible, inspectable, and resumable.

**See full reference**: [references/cmb-workflow.md](references/cmb-workflow.md)

---

## Workflow

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

### Phase 1 — Initialize CMB Directory

Once requirements are confirmed, initialize the CMB directory:

```bash
python3 <skill_path>/scripts/init_cmb.py --task "<task name>" --description "<desc>"
```

Default location: `.cmb/` in the current project directory. If write permission is denied, use a temp path and note it.

### Phase 2 — Plan Steps

Design the step chain. Each step must have:
- A unique `step_id` (e.g. `step_001`, `step_002`)
- A clear `name`
- Defined input fields (what it reads from the previous Bone)
- Defined output fields (what it writes to its own Bone)

Register each step:
```bash
python3 <skill_path>/scripts/run_step.py create step_001 --name "Requirement Analysis"
python3 <skill_path>/scripts/run_step.py create step_002 --name "Next Step Name"
```

### Phase 3 — Execute Steps (Meat → Bone loop)

For each step:
1. **Meat**: Read the previous step's output bone (if any), perform the reasoning/analysis/generation
2. **Bone**: Write the structured output using run_step.py:

```bash
python3 <skill_path>/scripts/run_step.py write step_001 --data '<json output>'
```

3. Proceed to the next step, reading this bone as input

To inspect current state:
```bash
python3 <skill_path>/scripts/run_step.py list
python3 <skill_path>/scripts/run_step.py read step_001
```

---

## Bone Output Rules

Every Bone (`output.json`) must be:
- **Valid JSON** — no prose, no markdown
- **Self-contained** — includes all data needed by the next step
- **Typed** — use arrays for lists, strings for text, booleans for flags
- Written via `run_step.py write` (auto-adds `step_id` and `written_at`)

Prefer flat structures; nest only when grouping is semantically necessary.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/init_cmb.py` | Initialize `.cmb/` directory and `plan.json` |
| `scripts/run_step.py` | Create steps, write/read bones, list status |

To find the skill's script path:
```bash
find ~/.comate/skills/cmb-skill/scripts -name "*.py"
```

---

## Step Design Heuristics

- **One concern per step**: don't combine analysis + implementation in one Meat
- **Bones are contracts**: if a step's output schema changes, update downstream steps
- **Ambiguity before action**: any uncertainty that affects implementation should be resolved in Phase 0, not discovered mid-chain
- **Resumability**: because bones are files, the chain can be resumed from any step by re-running from that step's Meat
