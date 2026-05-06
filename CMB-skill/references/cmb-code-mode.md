# CMB Code Mode Reference (Code-CMB)

Code-CMB applies the same Meat/Bone discipline as [Process-CMB](cmb-workflow.md), but to the **structure of code the agent produces**, not just to its reasoning workflow.

> In Process-CMB, the Bone is a JSON file in `.cmb/`.
> In Code-CMB, the Bone is **code** — the part of the source tree that callers depend on and that does not change casually.

## Table of Contents
1. [Mental Model](#mental-model)
2. [What Counts as a Code-Bone](#what-counts-as-a-code-bone)
3. [Three Principles, Re-projected](#three-principles-re-projected)
4. [Bone / Meat Judgment Checklist](#bone--meat-judgment-checklist)
5. [Registering Code-Bones](#registering-code-bones)
6. [Example Chain: Add a Feature to an Existing Module](#example-chain-add-a-feature-to-an-existing-module)
7. [Anti-patterns](#anti-patterns)

---

## Mental Model

> **Bones are the things that, if you change them, drag others along.**
> **Meat is the things you can change freely without anyone else noticing.**

That is the entire heuristic. Every concrete rule below is a consequence of this one sentence.

| | Code-Bone (stable contract) | Code-Meat (volatile implementation) |
|---|---|---|
| Examples | Public interfaces, exported types, data schemas, protocol messages, error enums, configuration keys, pure-function module boundaries, constants used across modules | Function bodies, private helpers, branch logic, prompt strings, log messages, glue code, internal caches |
| Change cost | High — every caller is affected | Low — local |
| Side effects | None at the boundary | May perform IO, network, time, randomness |
| Tested via | Contract / interface tests | Behavior tests |
| Allowed to change without coordination? | **No** | Yes |

---

## What Counts as a Code-Bone

A piece of code is a Code-Bone if **at least one** of the following is true:

1. It is **imported / depended on by another module** (public interfaces, exported types, schema definitions).
2. It defines a **wire-level shape** (HTTP request/response, message payloads, file formats, DB columns, config keys).
3. It defines an **error model** that callers must distinguish (error classes, status codes, result enums).
4. It is a **pure function with a stable signature** that others may compose against.
5. It is a **named constant or enum** referenced from multiple call sites.

Conversely, code is Meat if **all** of the following are true:

- Only the enclosing module reads it.
- Replacing its body — keeping its name and signature — would not require any other file to change.
- It may legitimately depend on time, IO, randomness, or external state.

The physical location of a Code-Bone is **not** prescribed by CMB. Use whatever convention the project already uses (`types.py`, `schemas/`, `*.proto`, `*.d.ts`, `interfaces/`, etc.). What matters is that the bone is *named, stable, and registered*.

---

## Three Principles, Re-projected

### 1. Ambiguity First → **Interface First**

Before writing implementation, write the contract: types, function signatures, data schema, error model, module boundaries. Confirm the contract (with the user, or by writing it down explicitly) *before* a single implementation Meat begins.

> **Hard rule**: in Code Mode (and in any code-producing step of Hybrid Mode), entering an implementation step **without a Code-Bone already on disk and registered** is forbidden.

### 2. One Concern Per Step → **Single-Responsibility Slice**

Each file/function/module owns one concern. In particular:

- **Pure logic must be separated from side effects.** Compute-shaped code (parsing, transformation, decision logic) lives in functions that do not read clocks, files, network, randomness, or globals. IO lives in thin adapters. The boundary between them is a Code-Bone.
- One Meat step writes implementation for one concern. Don't smuggle two refactors into one step.

### 3. Bone as Contract → **Interface as Contract**

Changing a Code-Bone (signature, type, schema, error variant, config key) is a *contract change*, not a refactor. The agent must:

- Explicitly list every downstream caller affected.
- Update them in the same step (or plan an explicit migration step).
- Record the change in the producing step's `output.json` (re-run `bind-code` so the new content `hash` is captured).
- Never change a Code-Bone silently as a side effect of "improving" an implementation.

---

## Bone / Meat Judgment Checklist

When deciding whether a piece of code should be treated as a Bone, ask:

- [ ] Does anything outside this file/module import or reference this symbol?
- [ ] Would changing its name, signature, or shape force changes elsewhere?
- [ ] Does it cross a process / network / persistence boundary?
- [ ] Is it part of an error model that callers branch on?
- [ ] Is it a constant or enum with cross-module meaning?
- [ ] Is it expected to remain stable across releases?

If **any** answer is yes, treat it as a Code-Bone: place it in a stable location, keep it free of side effects, and register it via `bind-code`.

When deciding whether code is safe to treat as Meat, confirm:

- [ ] No other module imports it.
- [ ] Its body can be rewritten without changing its signature.
- [ ] Tests that pass against the contract would still pass after the rewrite.

---

## Registering Code-Bones

Code-Bones live in the source tree, but they must be **referenced from the producing step's Process-Bone** so the chain stays auditable. Use:

```bash
python3 <skill_path>/scripts/run_step.py bind-code <step_id> \
    --files <comma-separated-paths> \
    [--symbols <comma-separated-exported-symbols>] \
    [--note <short description>]
```

This appends to `.cmb/<step_id>/output.json` under `code_bones`:

```json
{
  "code_bones": [
    {
      "registered_at": "...",
      "note": "Interface-first contract for auth module",
      "items": [
        {
          "path": "src/auth/types.py",
          "exists": true,
          "hash": "9e26bf369911",
          "symbols": ["AuthToken", "LoginRequest"]
        }
      ]
    }
  ]
}
```

Rules:
- `path` is relative to the project root (the parent of `.cmb/`).
- `hash` is a short sha256 prefix of the file contents at registration time.
- A later step that finds a *different* hash for the same path is observing a contract change and must apply the "Bone as Contract" rule.
- Re-running `bind-code` appends a new entry; previous registrations are kept as history.

---

## Example Chain: Add a Feature to an Existing Module

Scenario: "Add token refresh to the auth module."

**Step 001 — Requirement Analysis (Process Meat)**
- Resolve ambiguities: refresh strategy (sliding vs absolute), token format, error semantics.
- Process-Bone (`step_001/output.json`):
  ```json
  {
    "step_id": "step_001",
    "confirmed_requirements": [
      "Sliding refresh window",
      "Reject expired refresh tokens with TokenExpired"
    ],
    "open_questions": []
  }
  ```

**Step 002 — Interface / Type / Schema Bone (Code-Bone, no implementation)**
- Add/modify only signatures, types, errors, schemas. No function bodies.
- Files written: `src/auth/types.py` (adds `RefreshRequest`, `RefreshResponse`, `TokenExpired`), `src/auth/api.py` (declares `refresh_token(req: RefreshRequest) -> RefreshResponse` with `pass`).
- Register:
  ```bash
  run_step.py bind-code step_002 \
      --files src/auth/types.py,src/auth/api.py \
      --symbols "RefreshRequest,RefreshResponse,TokenExpired,refresh_token" \
      --note "Refresh-token contract"
  ```
- Process-Bone (`step_002/output.json`) now contains a `code_bones` entry pointing at the contract files with their hashes.

**Step 003 — Implementation (Code Meat)**
- Read `step_002/output.json`. Treat the listed files/symbols as immutable contract.
- Fill in the body of `refresh_token` and any pure helpers. Side effects (clock, store) go through adapters, not through the contract.
- If implementing requires changing a Code-Bone, **stop**: the contract step was incomplete. Go back to step_002, update it, and re-`bind-code` so the new hash is recorded.
- Process-Bone (`step_003/output.json`):
  ```json
  {
    "step_id": "step_003",
    "files_modified": ["src/auth/api.py", "src/auth/store.py"],
    "contract_unchanged": true
  }
  ```

**Step 004 — Tests against the Interface (Code-Bone)**
- Tests target the symbols registered in step_002, not the internals of step_003.
- A test file is itself a Code-Bone if it codifies the contract (e.g. `test_auth_contract.py`); register it via `bind-code` if so.

This is the canonical Code-CMB shape: **clarify → contract → implement → verify-the-contract**, with each transition gated by a Process-Bone that records, among other things, which Code-Bones now exist and what they hash to.

---

## Anti-patterns

- **Implementation-first**: writing the function body before the signature is settled. Forbidden in Code Mode.
- **Silent contract change**: editing a registered Code-Bone (signature, type, schema) as part of an "implementation" step without re-running `bind-code` and revisiting callers.
- **Side-effect leakage**: a function declared as pure that secretly reads the clock or environment. The contract becomes untestable without integration plumbing.
- **God-step**: one step that "designs and implements" something. Split into Code-Bone step + Meat step.
- **Untracked Code-Bones**: source files that are obviously contracts (schema, types) but never registered with `bind-code`. Future steps cannot detect drift.
