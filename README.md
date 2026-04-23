# CMB-skill：骨肉相连

> **Chicken Meat with Bone** — 一种面向 AI Agent 的结构化、可复现、可链接的多步骤工作流技能。

[English Version](README_EN.md)

---

## 什么是 CMB？

CMB（骨肉相连）将复杂任务拆解为交替的 **Meat（肉）** 和 **Bone（骨）** 单元：

| 单元 | 角色 | 说明 |
|------|------|------|
| **Meat** | LLM 推理步骤 | Agent 分析、决策或生成内容，输入输出均为结构化 JSON |
| **Bone** | 确定性产物 | 写入 `.cmb/<step_id>/output.json` 的 JSON 文件，是步骤间的稳定交接物 |

链式结构：

```
Meat(step_001) → Bone(step_001/output.json)
                          ↓
Meat(step_002) → Bone(step_002/output.json)
                          ↓
                         ...
```

每个 Bone 是下一个 Meat 的确定性输入，保证整条链路可检视、可暂停、可从任意步骤恢复。

---

## 核心设计原则

1. **歧义先行**：在规划任何步骤之前，先通过带选项（含自定义输入）的方式与用户确认所有关键疑问
2. **一步一事**：每个 Meat 只处理一个关注点，不混用分析与实现
3. **Bone 即契约**：Bone 的输出结构变更时，下游步骤必须同步更新
4. **本地优先**：有写权限时，优先将 Bone 写入项目本地 `.cmb/` 目录

---

## 工作流

### Phase 0 — 需求确认（首块 Meat）

在创建任何步骤之前，先解决所有影响执行的歧义。必须提供选项列表 + "其他（请自定义）"，支持用户自由输入：

```
Q1：应使用哪个框架？
  a) React
  b) Vue
  c) Angular
  d) 其他（请说明）
```

所有关键疑问解决后，将确认结果写入第一个 Bone。

### Phase 1 — 初始化 CMB 目录

```bash
python3 scripts/init_cmb.py --task "任务名称" --description "任务描述"
```

在当前项目目录下创建 `.cmb/` 结构：

```
.cmb/
├── plan.json          # 全局计划与步骤注册表
├── step_001/
│   ├── input.json     # 输入 Bone
│   └── output.json    # 输出 Bone
└── step_002/
    ├── input.json
    └── output.json
```

### Phase 2 — 规划步骤链

为每个步骤定义：唯一 `step_id`、名称、输入字段、输出字段，并注册：

```bash
python3 scripts/run_step.py create step_001 --name "需求分析"
python3 scripts/run_step.py create step_002 --name "方案设计"
```

### Phase 3 — 执行 Meat → Bone 循环

```bash
# 写入某步骤的输出 Bone
python3 scripts/run_step.py write step_001 --data '{"requirements": ["JWT 认证", "PostgreSQL"]}'

# 读取某步骤的 Bone
python3 scripts/run_step.py read step_001

# 查看全部步骤状态
python3 scripts/run_step.py list
```

---

## 脚本说明

| 脚本 | 功能 |
|------|------|
| `scripts/init_cmb.py` | 初始化 `.cmb/` 目录和 `plan.json` |
| `scripts/run_step.py` | 创建步骤、写入/读取 Bone、查看状态 |

### init_cmb.py 用法

```bash
python3 scripts/init_cmb.py [--dir <目录>] [--task <任务名>] [--description <描述>]
```

### run_step.py 用法

```bash
python3 scripts/run_step.py create <step_id> --name <步骤名> [--data <json>]
python3 scripts/run_step.py write  <step_id> --data <json>
python3 scripts/run_step.py read   <step_id>
python3 scripts/run_step.py list
python3 scripts/run_step.py status <step_id> <状态>
```

---

## Bone 格式规范

每个输出 Bone（`output.json`）必须：

- 是合法 JSON，无散文或 Markdown
- 自包含：包含下一步骤所需的全部数据
- 由 `run_step.py write` 写入（自动注入 `step_id` 和 `written_at`）

```json
{
  "step_id": "step_001",
  "written_at": "2026-04-23T10:00:00",
  "confirmed_requirements": ["JWT 认证", "React 前端"],
  "constraints": ["不使用第三方 UI 库"],
  "open_questions": []
}
```

---

## 完整示例

场景："帮我构建一个 Todo 应用的 REST API"

**step_001 输出 Bone（需求分析）**
```json
{
  "step_id": "step_001",
  "task": "构建 Todo REST API",
  "confirmed_requirements": ["Python/FastAPI", "PostgreSQL", "JWT 认证"],
  "open_questions": []
}
```

**step_002 输出 Bone（接口设计）**
```json
{
  "step_id": "step_002",
  "endpoints": [
    {"method": "POST", "path": "/todos", "description": "创建 Todo"},
    {"method": "GET",  "path": "/todos", "description": "列出 Todo"}
  ]
}
```

**step_003 输出 Bone（代码实现）**
```json
{
  "step_id": "step_003",
  "files_written": ["main.py", "models.py", "routers/todos.py"],
  "status": "complete"
}
```

---

## 作为 Comate Skill 使用

将本仓库内容放置于 `~/.comate/skills/cmb-skill/` 或项目的 `.comate/skills/cmb-skill/` 下，Comate 将在检测到多步骤复杂任务时自动激活此技能。

详细工作流规范见 [references/cmb-workflow.md](references/cmb-workflow.md)。

---

## License

[LICENSE](LICENSE)
