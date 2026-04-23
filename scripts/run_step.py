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

Options:
    --dir   Project directory (default: current dir)

Examples:
    run_step.py create step_001 --name "Requirement Analysis"
    run_step.py write  step_001 --data '{"requirements": ["auth", "storage"]}'
    run_step.py read   step_001
    run_step.py list
    run_step.py status step_001 done
"""

import sys
import json
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


def main():
    parser = argparse.ArgumentParser(description="CMB Step Runner")
    parser.add_argument("command", choices=["create", "write", "read", "list", "status"])
    parser.add_argument("step_id", nargs="?", default=None)
    parser.add_argument("extra", nargs="?", default=None, help="Extra arg (e.g. status value)")
    parser.add_argument("--name", default="", help="Step name (for create)")
    parser.add_argument("--data", default=None, help="JSON data string (for write/create)")
    parser.add_argument("--dir", default=".", help="Project directory")

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


if __name__ == "__main__":
    main()
