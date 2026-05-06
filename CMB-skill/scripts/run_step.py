#!/usr/bin/env python3
"""
CMB Step Runner - Manage Bone artifacts in a CMB chain.

Reads/writes deterministic JSON bones for each Meat step.

Usage:
    run_step.py create <step_id> --name <name>         # Create a new step dir + input.json
    run_step.py write  <step_id> --data <json-string>  # Write output bone for a step
    run_step.py read   <step_id>                        # Read a step's output bone
    run_step.py list                                    # List all steps and status
    run_step.py status <step_id> <status>               # Update step status in plan.json
    run_step.py bind-code <step_id> --files <f1,f2,...> [--symbols <s1,s2,...>] [--note <text>]
                                                        # Register Code-Bones (source files /
                                                        # exported symbols) into the step's
                                                        # output.json under `code_bones`.

Options:
    --dir   Project directory (default: current dir)

Examples:
    run_step.py create step_001 --name "Requirement Analysis"
    run_step.py write  step_001 --data '{"requirements": ["auth", "storage"]}'
    run_step.py read   step_001
    run_step.py list
    run_step.py status step_001 done
    run_step.py bind-code step_002 --files src/auth/types.py,src/auth/schema.py \
                                   --symbols "AuthToken,LoginRequest" \
                                   --note "Interface-first contract for auth module"
"""

import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

CMB_DIR = ".cmb"


def load_plan(cmb_path: Path) -> dict:
    plan_file = cmb_path / "plan.json"
    if not plan_file.exists():
        print(f"ERROR: No plan.json found at {plan_file}. Run init_cmb.py first.")
        sys.exit(1)
    return json.loads(plan_file.read_text())


def save_plan(cmb_path: Path, plan: dict):
    plan_file = cmb_path / "plan.json"
    plan_file.write_text(json.dumps(plan, ensure_ascii=False, indent=2))


def get_cmb_path(base_dir: str) -> Path:
    cmb_path = Path(base_dir).resolve() / CMB_DIR
    if not cmb_path.exists():
        print(f"ERROR: CMB directory not found: {cmb_path}. Run init_cmb.py first.")
        sys.exit(1)
    return cmb_path


def cmd_create(cmb_path: Path, step_id: str, name: str, input_data: dict = None):
    step_dir = cmb_path / step_id
    step_dir.mkdir(exist_ok=True)

    input_file = step_dir / "input.json"
    payload = input_data or {}
    payload.setdefault("step_id", step_id)
    payload.setdefault("created_at", datetime.now().isoformat())
    input_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Created step dir: {step_dir}")
    print(f"Written input bone: {input_file}")

    plan = load_plan(cmb_path)
    existing_ids = [s["id"] for s in plan["steps"]]
    if step_id not in existing_ids:
        plan["steps"].append({
            "id": step_id,
            "name": name,
            "status": "pending",
            "input_bone": f"{step_id}/input.json",
            "output_bone": f"{step_id}/output.json"
        })
        save_plan(cmb_path, plan)
        print(f"Registered step '{step_id}' in plan.json")
    return str(input_file)


def cmd_write(cmb_path: Path, step_id: str, data: dict):
    step_dir = cmb_path / step_id
    step_dir.mkdir(exist_ok=True)

    output_file = step_dir / "output.json"
    data.setdefault("step_id", step_id)
    data.setdefault("written_at", datetime.now().isoformat())
    output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Written output bone: {output_file}")

    # Auto-mark step as done in plan
    plan = load_plan(cmb_path)
    for step in plan["steps"]:
        if step["id"] == step_id:
            step["status"] = "done"
    save_plan(cmb_path, plan)
    return str(output_file)


def cmd_read(cmb_path: Path, step_id: str) -> dict:
    output_file = cmb_path / step_id / "output.json"
    if not output_file.exists():
        print(f"ERROR: No output bone for step '{step_id}' at {output_file}")
        sys.exit(1)
    data = json.loads(output_file.read_text())
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def cmd_list(cmb_path: Path):
    plan = load_plan(cmb_path)
    print(f"Task: {plan.get('task', '(unnamed)')}")
    print(f"Status: {plan.get('status', 'unknown')}")
    print()
    steps = plan.get("steps", [])
    if not steps:
        print("No steps registered yet.")
        return
    for s in steps:
        status_icon = {"done": "[x]", "pending": "[ ]", "in_progress": "[~]"}.get(s["status"], "[?]")
        print(f"  {status_icon} {s['id']} - {s['name']} ({s['status']})")


def cmd_status(cmb_path: Path, step_id: str, status: str):
    plan = load_plan(cmb_path)
    updated = False
    for step in plan["steps"]:
        if step["id"] == step_id:
            step["status"] = status
            updated = True
    if not updated:
        print(f"ERROR: Step '{step_id}' not found in plan.json")
        sys.exit(1)
    save_plan(cmb_path, plan)
    print(f"Updated step '{step_id}' status to '{status}'")


def _short_hash(file_path: Path) -> str:
    """Return a short sha256 prefix for file content; '' if file is missing."""
    if not file_path.exists() or not file_path.is_file():
        return ""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:12]


def cmd_bind_code(cmb_path: Path, step_id: str, files: list, symbols: list,
                  note: str = ""):
    """Register Code-Bones (source files / exported symbols) into the step's output.json.

    Code-Bones are the *source-level* stable contracts (interfaces, types, schemas,
    pure-function modules, constants) produced or modified during this step. They are
    referenced by path + optional exported symbols + a content hash so downstream steps
    can detect contract drift.

    Files are resolved relative to the project root (the parent of the .cmb/ directory).
    Missing files are still recorded (with an empty hash) so the agent can flag them.

    The `symbols` list is shared across all `files` in a single call — it documents the
    set of exported symbols this registration is about. To attach different symbol sets
    to different files, run `bind-code` once per file group.
    """
    step_dir = cmb_path / step_id
    step_dir.mkdir(exist_ok=True)
    output_file = step_dir / "output.json"

    if output_file.exists():
        data = json.loads(output_file.read_text())
    else:
        data = {}

    project_root = cmb_path.parent
    entries = []
    for f in files:
        f = f.strip()
        if not f:
            continue
        abs_path = (project_root / f).resolve()
        entry = {
            "path": f,
            "exists": abs_path.exists(),
            "hash": _short_hash(abs_path),
        }
        if symbols:
            entry["symbols"] = [s.strip() for s in symbols if s.strip()]
        entries.append(entry)

    code_bones_block = {
        "registered_at": datetime.now().isoformat(),
        "items": entries,
    }
    if note:
        code_bones_block["note"] = note

    # Append rather than overwrite so multiple bind-code calls accumulate history.
    existing = data.get("code_bones")
    if isinstance(existing, list):
        existing.append(code_bones_block)
        data["code_bones"] = existing
    elif isinstance(existing, dict):
        data["code_bones"] = [existing, code_bones_block]
    else:
        data["code_bones"] = [code_bones_block]

    data.setdefault("step_id", step_id)
    data.setdefault("written_at", datetime.now().isoformat())
    output_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"Registered {len(entries)} code bone(s) into: {output_file}")
    for e in entries:
        marker = "" if e["exists"] else "  (MISSING)"
        print(f"  - {e['path']} [{e['hash'] or '----'}]{marker}")
    return str(output_file)


def main():
    parser = argparse.ArgumentParser(description="CMB Step Runner")
    parser.add_argument(
        "command",
        choices=["create", "write", "read", "list", "status", "bind-code"],
    )
    parser.add_argument("step_id", nargs="?", default=None)
    parser.add_argument("extra", nargs="?", default=None, help="Extra arg (e.g. status value)")
    parser.add_argument("--name", default="", help="Step name (for create)")
    parser.add_argument("--data", default=None, help="JSON data string (for write/create)")
    parser.add_argument("--dir", default=".", help="Project directory")
    parser.add_argument("--files", default=None,
                        help="Comma-separated source file paths (for bind-code)")
    parser.add_argument("--symbols", default=None,
                        help="Comma-separated exported symbol names (for bind-code)")
    parser.add_argument("--note", default="",
                        help="Optional note describing the contract (for bind-code)")

    args = parser.parse_args()
    cmb_path = get_cmb_path(args.dir)

    if args.command == "create":
        if not args.step_id:
            print("ERROR: step_id required for create")
            sys.exit(1)
        input_data = json.loads(args.data) if args.data else {}
        cmd_create(cmb_path, args.step_id, args.name, input_data)

    elif args.command == "write":
        if not args.step_id or not args.data:
            print("ERROR: step_id and --data required for write")
            sys.exit(1)
        data = json.loads(args.data)
        cmd_write(cmb_path, args.step_id, data)

    elif args.command == "read":
        if not args.step_id:
            print("ERROR: step_id required for read")
            sys.exit(1)
        cmd_read(cmb_path, args.step_id)

    elif args.command == "list":
        cmd_list(cmb_path)

    elif args.command == "status":
        if not args.step_id or not args.extra:
            print("ERROR: step_id and status value required")
            sys.exit(1)
        cmd_status(cmb_path, args.step_id, args.extra)

    elif args.command == "bind-code":
        if not args.step_id or not args.files:
            print("ERROR: step_id and --files required for bind-code")
            sys.exit(1)
        files = [f for f in args.files.split(",") if f.strip()]
        symbols = [s for s in (args.symbols or "").split(",") if s.strip()]
        cmd_bind_code(cmb_path, args.step_id, files, symbols, note=args.note)


if __name__ == "__main__":
    main()
