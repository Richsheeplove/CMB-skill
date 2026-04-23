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

## License

[LICENSE](LICENSE)
