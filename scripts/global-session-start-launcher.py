#!/usr/bin/env python3
"""Legacy entrypoint; delegate to the shared fail-open managed runtime."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from launch_hook import main

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "session_start_context", *sys.argv[1:]]
    raise SystemExit(main())
