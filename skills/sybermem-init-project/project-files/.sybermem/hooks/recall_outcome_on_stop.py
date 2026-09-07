#!/usr/bin/env python3
from pathlib import Path
import runpy

# Keep the two distributed Claude templates identical in behavior.
runpy.run_path(str(Path(__file__).resolve().parents[5] / "packages" / "claude-skills" / "sybermem-init-project" / "project-files" / ".sybermem" / "hooks" / "recall_outcome_on_stop.py"), run_name="__main__")
