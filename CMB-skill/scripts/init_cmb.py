#!/usr/bin/env python3
"""
CMB Init - Initialize a CMB (Chicken Meat with Bone) project directory.

Creates a .cmb/ directory with a structured plan.json skeleton.

Usage:
    init_cmb.py [--dir <target-dir>] [--task <task-name>] [--mode {process,code,hybrid}]

Examples:
    init_cmb.py
    init_cmb.py --dir /path/to/project --task "Build user auth API"
    init_cmb.py --task "Refactor parser" --mode code
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

CMB_DIR = ".cmb"

VALID_MODES = ("process", "code", "hybrid")
DEFAULT_MODE = "hybrid"

PLAN_SKELETON = {
    "version": "1.1",
    "task": "",
    "description": "",
    "mode": DEFAULT_MODE,
    "created_at": "",
    "status": "planning",
    "steps": []
}

STEP_SKELETON = {
    "id": "step_001",
    "name": "",
    "type": "meat",
    "status": "pending",
    "input_schema": {
        "type": "object",
        "properties": {},
        "required": []
    },
    "output_schema": {
        "type": "object",
        "properties": {},
        "required": []
    },
    "bone_file": "step_001/output.json"
}


def init_cmb(target_dir: str = ".", task: str = "", description: str = "",
             mode: str = DEFAULT_MODE) -> Path:
    if mode not in VALID_MODES:
        print(f"ERROR: invalid mode '{mode}'. Must be one of: {', '.join(VALID_MODES)}")
        sys.exit(1)

    base = Path(target_dir).resolve()
    cmb_path = base / CMB_DIR

    if cmb_path.exists():
        print(f"CMB directory already exists: {cmb_path}")
        return cmb_path

    cmb_path.mkdir(parents=True)
    print(f"Created CMB directory: {cmb_path}")

    plan = dict(PLAN_SKELETON)
    plan["task"] = task
    plan["description"] = description
    plan["mode"] = mode
    plan["created_at"] = datetime.now().isoformat()

    plan_file = cmb_path / "plan.json"
    plan_file.write_text(json.dumps(plan, ensure_ascii=False, indent=2))
    print(f"Created plan: {plan_file}")
    print(f"Mode: {mode}")

    print(f"\nCMB project initialized at: {cmb_path}")
    print("Next: Use run_step.py to create and manage steps.")
    return cmb_path


def main():
    parser = argparse.ArgumentParser(description="Initialize a CMB project directory")
    parser.add_argument("--dir", default=".", help="Target directory (default: current dir)")
    parser.add_argument("--task", default="", help="Task name/title")
    parser.add_argument("--description", default="", help="Task description")
    parser.add_argument(
        "--mode",
        default=DEFAULT_MODE,
        choices=list(VALID_MODES),
        help=(
            "CMB application mode: "
            "'process' constrains the agent's reasoning workflow only; "
            "'code' constrains the structure of generated code (interface-first); "
            "'hybrid' (default) applies Process-CMB at the workflow level and "
            "Code-CMB inside any implementation step."
        ),
    )
    args = parser.parse_args()

    init_cmb(target_dir=args.dir, task=args.task, description=args.description, mode=args.mode)


if __name__ == "__main__":
    main()
