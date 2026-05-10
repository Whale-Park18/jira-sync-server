import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path("/app/data/state.json")
_lock = asyncio.Lock()

_SYNC_SCRIPT = os.environ.get("JIRA_SYNC_SCRIPT", "/jira-sync/sync.py")
_SYNC_CONFIG = os.environ.get("JIRA_SYNC_CONFIG", "/jira-sync/sync_config.yaml")

_PASS_THROUGH_VARS = [
    "JIRA_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_DB_QUERY",
    "NOTION_API_KEY",
    "NOTION_DATA_SOURCE_ID",
]


def _read_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_sync_time": None, "status": None, "message": None, "is_syncing": False}


def _write_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False))


async def get_status() -> dict:
    state = _read_state()
    state["is_syncing"] = _lock.locked()
    return state


async def run_sync() -> None:
    if _lock.locked():
        return

    async with _lock:
        state = _read_state()
        state["is_syncing"] = True
        _write_state(state)

        env = {**os.environ}
        for var in _PASS_THROUGH_VARS:
            val = os.environ.get(var)
            if val:
                env[var] = val

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                _SYNC_SCRIPT,
                "--config",
                _SYNC_CONFIG,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode(errors="replace").strip()
            last_lines = "\n".join(output.splitlines()[-5:]) if output else ""

            new_state = {
                "last_sync_time": datetime.now(timezone.utc).isoformat(),
                "status": "success" if proc.returncode == 0 else "error",
                "message": last_lines,
                "is_syncing": False,
            }
        except Exception as exc:
            new_state = {
                "last_sync_time": datetime.now(timezone.utc).isoformat(),
                "status": "error",
                "message": str(exc),
                "is_syncing": False,
            }

        _write_state(new_state)
