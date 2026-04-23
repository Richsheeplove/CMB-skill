# CMB-skill: Chicken Meat with Bone

> A structured, reproducible, and chainable multi-step workflow skill for AI Agents.

[中文版本](README.md)

---

## What is CMB?

CMB (Chicken Meat with Bone / 骨肉相连) decomposes complex tasks into alternating **Meat** and **Bone** units:

| Unit | Role | Description |
|------|------|-------------|
| **Meat** | LLM reasoning step | The agent analyzes, decides, or generates. Input and output are structured JSON. |
| **Bone** | Deterministic artifact | A JSON file written to `.cmb/<step_id>/output.json`. The stable handoff between steps. |

Chain pattern:

```
Meat(step_001) → Bone(step_001/output.json)
                          ↓
Meat(step_002) → Bone(step_002/output.json)
                          ↓
                         ...
```

Each Bone is the deterministic input for the next Meat, making every step inspectable, pausable, and resumable from any point.

---

## Core Design Principles

1. **Ambiguity first**: Before planning any steps, resolve all critical unknowns with the user via option lists that always include a free-input option
2. **One concern per step**: Each Meat handles a single concern; never mix analysis with implementation
3. **Bones are contracts**: When a Bone's output schema changes, downstream steps must be updated accordingly
4. **Local-first**: When write permission is available, Bones are written to the project's local `.cmb/` directory

---

## Workflow

### Phase 0 — Requirement Gathering (First Meat)

Before creating any steps, resolve all ambiguities that would affect execution. Always provide option lists with a free-input fallback:

```
Q1: Which framework should be used?
  a) React
  b) Vue
  c) Angular
  d) Other (please specify)
```

Once all critical questions are resolved, write the confirmed requirements as the first Bone.

### Phase 1 — Initialize CMB Directory

```bash
python3 scripts/init_cmb.py --task "Task name" --description "Task description"
```

Creates the `.cmb/` structure in the current project directory:

```
.cmb/
├── plan.json          # Global plan and step registry
├── step_001/
│   ├── input.json     # Input bone
│   └── output.json    # Output bone
└── step_002/
    ├── input.json
    └── output.json
```

### Phase 2 — Plan the Step Chain

Define each step with a unique `step_id`, name, input fields, and output fields, then register:

```bash
python3 scripts/run_step.py create step_001 --name "Requirement Analysis"
python3 scripts/run_step.py create step_002 --name "Solution Design"
```

### Phase 3 — Execute the Meat → Bone Loop

```bash
# Write a step's output Bone
python3 scripts/run_step.py write step_001 --data '{"requirements": ["JWT auth", "PostgreSQL"]}'

# Read a step's Bone
python3 scripts/run_step.py read step_001

# View all step statuses
python3 scripts/run_step.py list
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/init_cmb.py` | Initialize the `.cmb/` directory and `plan.json` |
| `scripts/run_step.py` | Create steps, write/read Bones, check status |

### init_cmb.py usage

```bash
python3 scripts/init_cmb.py [--dir <directory>] [--task <task-name>] [--description <desc>]
```

### run_step.py usage

```bash
python3 scripts/run_step.py create <step_id> --name <name> [--data <json>]
python3 scripts/run_step.py write  <step_id> --data <json>
python3 scripts/run_step.py read   <step_id>
python3 scripts/run_step.py list
python3 scripts/run_step.py status <step_id> <status>
```

---

## Bone Format Spec

Every output Bone (`output.json`) must:

- Be valid JSON — no prose or markdown
- Be self-contained: include all data the next step needs
- Be written via `run_step.py write` (auto-injects `step_id` and `written_at`)

```json
{
  "step_id": "step_001",
  "written_at": "2026-04-23T10:00:00",
  "confirmed_requirements": ["JWT auth", "React frontend"],
  "constraints": ["No third-party UI libraries"],
  "open_questions": []
}
```

---

## Full Example

Scenario: "Build me a REST API for a todo app"

**step_001 output Bone (Requirement Analysis)**
```json
{
  "step_id": "step_001",
  "task": "Build Todo REST API",
  "confirmed_requirements": ["Python/FastAPI", "PostgreSQL", "JWT auth"],
  "open_questions": []
}
```

**step_002 output Bone (API Design)**
```json
{
  "step_id": "step_002",
  "endpoints": [
    {"method": "POST", "path": "/todos", "description": "Create todo"},
    {"method": "GET",  "path": "/todos", "description": "List todos"}
  ]
}
```

**step_003 output Bone (Implementation)**
```json
{
  "step_id": "step_003",
  "files_written": ["main.py", "models.py", "routers/todos.py"],
  "status": "complete"
}
```

---

## Using as a Comate Skill

Place the contents of this repository under `~/.comate/skills/cmb-skill/` (personal) or `.comate/skills/cmb-skill/` (project-level). Comate will automatically activate this skill when it detects multi-step complex tasks.

For full workflow specifications, see [references/cmb-workflow.md](references/cmb-workflow.md).

---

## License

[LICENSE](LICENSE)
