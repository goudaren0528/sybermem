from argparse import Namespace
from pathlib import Path
import json
import re
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sybermem_cli.main import cmd_record_id

CANONICAL_ID = re.compile(r"^(change|decision|requirement|bug)-[0-9a-f]{32}$")


def test_cli_record_id_text_prints_canonical_id(capsys) -> None:
    exit_code = cmd_record_id(Namespace(type="change", format="text"))

    assert exit_code == 0
    printed = capsys.readouterr().out.strip()
    assert CANONICAL_ID.match(printed), printed
    assert printed.startswith("change-")


def test_cli_record_id_json_returns_id_and_type(capsys) -> None:
    exit_code = cmd_record_id(Namespace(type="bug", format="json"))

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["type"] == "bug"
    assert CANONICAL_ID.match(payload["record_id"])
    assert payload["record_id"].startswith("bug-")


def test_cli_record_id_is_unique_per_call(capsys) -> None:
    cmd_record_id(Namespace(type="decision", format="text"))
    first = capsys.readouterr().out.strip()
    cmd_record_id(Namespace(type="decision", format="text"))
    second = capsys.readouterr().out.strip()

    assert first != second
