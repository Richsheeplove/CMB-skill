# CMB Workflow Reference

CMB (Chicken Meat with Bone / 骨肉相连) is a structured execution pattern for reproducible, chainable agent workflows.

## Table of Contents
1. [Core Concepts](#core-concepts)
2. [Bone Schema](#bone-schema)
3. [Step Lifecycle](#step-lifecycle)
4. [Requirement Gathering Pattern](#requirement-gathering-pattern)
5. [Example: Full Chain](#example-full-chain)
6. [Directory Layout](#directory-layout)

---

## Core Concepts

| Term | Role | Description |
|------|------|-------------|
| **Meat** | LLM reasoning | A step where the agent analyzes, decides, or generates. Input and output are structured JSON. |
| **Bone** | Deterministic artifact | A JSON file written to `.cmb/<step_id>/output.json`. It is the stable handoff between steps. |

Chain pattern:
```
Meat(step_001) → Bone(step_001/output.json)
                 ↓ (next Meat reads this file)
Meat(step_002) → Bone(step_002/output.json)
                 ↓
...
```

---

## Bone Schema

Every bone file (`output.json`) must conform to:

```json
{
  "step_id": "step_001",
  "written_at": "<ISO8601 timestamp>",
  "<domain_fields>": "..."
}
```

`step_id` and `written_at` are injected automatically by `run_step.py write`.

Input bones (`input.json`) follow the same structure, plus:
```json
{
  "step_id": "step_001",
  "created_at": "<ISO8601 timestamp>",
  "<user_input_fields>": "..."
}
```

---

## Step Lifecycle

```
pending → in_progress → done
               ↓
          (on error) → blocked
```

Each step:
1. Agent reads previous step's `output.json` (the incoming Bone)
2. Agent performs Meat reasoning
3. Agent calls `run_step.py write <step_id> --data '<json>'` to write the Bone
4. Next step proceeds

---

## Requirement Gathering Pattern

Before planning steps, the agent must resolve all ambiguities. Use this pattern:

### Ambiguity Item Structure
```json
{
  "id": "q1",
  "question": "Which authentication method should be used?",
  "options": [
    {"id": "a", "label": "Email + Password"},
    {"id": "b", "label": "OAuth (Google/GitHub)"},
    {"id": "c", "label": "Both"},
    {"id": "custom", "label": "Other (please specify)"}
  ],
  "required": true
}
```

**Rules:**
- Always include a "custom / Other" option so users can provide free-form input
- Present no more than 5 questions at once; batch if more exist
- Do not proceed to step planning until all `required: true` ambiguities are resolved
- Write resolved requirements as the first Bone (`step_001/output.json`)

### Confirmed Requirements Bone (`step_001/output.json`)
```json
{
  "step_id": "step_001",
  "written_at": "...",
  "task": "Build login page",
  "confirmed_requirements": [
    "Email + Password authentication",
    "OAuth via Google"
  ],
  "constraints": ["Must use React", "No external auth libraries"],
  "open_questions": []
}
```

---

## Example: Full Chain

### Scenario: "Build me a REST API for a todo app"

**Step 001 — Requirement Analysis (Meat)**
- Input: user's raw request
- Ambiguities to resolve: language/framework, DB, auth needed?
- Output Bone:
```json
{
  "step_id": "step_001",
  "task": "Build REST API for todo app",
  "confirmed_requirements": ["Python/FastAPI", "PostgreSQL", "JWT auth"],
  "open_questions": []
}
```

**Step 002 — API Design (Meat)**
- Input Bone: step_001/output.json
- Agent designs endpoints
- Output Bone:
```json
{
  "step_id": "step_002",
  "endpoints": [
    {"method": "POST", "path": "/todos", "description": "Create todo"},
    {"method": "GET",  "path": "/todos", "description": "List todos"}
  ]
}
```

**Step 003 — Implementation (Meat)**
- Input Bone: step_002/output.json
- Agent writes code files
- Output Bone:
```json
{
  "step_id": "step_003",
  "files_written": ["main.py", "models.py", "routers/todos.py"],
  "status": "complete"
}
```

---

## Directory Layout

```
<project>/
└── .cmb/
    ├── plan.json             # Overall plan, step registry
    ├── step_001/
    │   ├── input.json        # Input bone (initial data or user input)
    │   └── output.json       # Output bone (result of this Meat step)
    ├── step_002/
    │   ├── input.json
    │   └── output.json
    └── ...
```

`plan.json` structure:
```json
{
  "version": "1.0",
  "task": "...",
  "description": "...",
  "created_at": "...",
  "status": "planning | running | done",
  "steps": [
    {
      "id": "step_001",
      "name": "Requirement Analysis",
      "status": "done | pending | in_progress | blocked",
      "input_bone": "step_001/input.json",
      "output_bone": "step_001/output.json"
    }
  ]
}
```
