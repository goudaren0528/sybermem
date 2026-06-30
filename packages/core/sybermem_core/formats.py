from __future__ import annotations

import json
from typing import Any


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)
