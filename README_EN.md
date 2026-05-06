# CMB-skill: Chicken Meat with Bone

> A structured, reproducible multi-step workflow pattern for AI Agents.

![CMB](ChickenMeatWithBone.png)

[中文版本](README.md)

---

## Philosophy

The greatest enemy of complex tasks is **cascading uncertainty**: vague output from one step amplifies deviation in the next, until the entire chain becomes impossible to debug or reproduce.

CMB's answer: use deterministic **Bone** to chain together non-deterministic **Meat**.

- **Meat** is the process of reasoning and decision-making — creativity and uncertainty are welcome here
- **Bone** is the structured artifact left behind after each reasoning step — it must be deterministic, readable, and transferable

The chain looks like this:

```
Meat → Bone → Meat → Bone → ...
```

Each Bone is the sole input to the next Meat. This makes the entire workflow pausable, inspectable, and resumable at any node.

---

## Three Principles

**1. Ambiguity First**
Before executing any step, surface all critical unknowns and confirm them explicitly. A blurry starting point leads to a chaotic ending.

**2. One Concern Per Step**
Each Meat does exactly one thing. Analysis is analysis. Design is design. Implementation is implementation. The finer the granularity, the more stable each step.

**3. Bone as Contract**
A Bone is not a byproduct of the process — it is the formal agreement between steps. Changing the structure of a Bone means every downstream step that depends on it must be revisited.

---

## Two Application Scenarios

The Meat/Bone discipline applies at two levels simultaneously:

- **Process-CMB (workflow domain)** — constrains the agent's **reasoning process**. Meat is each LLM step; Bone is a deterministic JSON artifact at `.cmb/<step_id>/output.json`.
- **Code-CMB (code domain)** — constrains the **structure of the code the agent produces**. Meat is volatile implementation (function bodies, branch logic, glue code, prompt strings). Bone is the stable contract layer in source: interfaces, types, schemas, protocol messages, pure-function boundaries, cross-module constants.

> **One-sentence heuristic**: **Bones are the things that, if you change them, drag others along. Meat is the things you can change freely without anyone else noticing.**

The three principles, re-projected into each domain:

| Principle | Process-CMB | Code-CMB |
|---|---|---|
| **Ambiguity First** | Resolve all blocking unknowns before planning steps | **Interface First**: pin types, signatures, schema, and error model before any implementation |
| **One Concern Per Step** | One Meat does one thing | **Single-Responsibility Slice**: one file/function = one concern; pure logic separated from IO/side effects |
| **Bone as Contract** | Changing a bone's schema requires reviewing every downstream step | **Interface as Contract**: changing a public interface/type/schema requires explicitly listing affected callers and updating them — never silently |

The recommended default is **Hybrid Mode**: drive the whole task with Process-CMB, and apply Code-CMB inside any step whose deliverable is code (such steps must include an explicit "interface-first" sub-step).

See `CMB-skill/references/cmb-workflow.md` (process domain) and `CMB-skill/references/cmb-code-mode.md` (code domain) for the full specs.

---

## License

[LICENSE](LICENSE)
