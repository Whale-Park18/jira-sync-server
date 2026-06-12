import asyncio
import json
import os
import re
import tempfile
from asyncio.subprocess import PIPE, STDOUT
from datetime import datetime, timezone

from dotenv import dotenv_values

from app.config import settings

_DEFAULT_STATE = {
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "last_lines": [],
    "exit_code": None,
}

_LOG_LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+ \| (\w+)\s*\| \S+ - (?:\[([A-Z][A-Z0-9]*-\d+)\] )?(.+)$"
)


def _format_log_line(raw_line: str) -> str | None:
    match = _LOG_LINE_RE.match(raw_line)
    if not match:
        return None
    timestamp, level, issue_key, message = match.groups()
    if issue_key and message.startswith("Notion"):
        return f"{timestamp} {issue_key} {message}"
    if level == "ERROR":
        return f"{timestamp} [오류] {message}"
    return None


class SyncRunner:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._state: dict = self._load_state()
        if self._state["status"] == "running":
            self._state["status"] = "error"
            self._state["last_lines"].append("[서버 재시작으로 인해 동기화가 중단되었습니다]")
            self._save_state()

    def _load_state(self) -> dict:
        try:
            with open(settings.state_file_path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return dict(_DEFAULT_STATE)

    def _save_state(self) -> None:
        path = settings.state_file_path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(self._state, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            os.unlink(tmp_path)
            raise

    def get_status(self) -> dict:
        return dict(self._state)

    def is_running(self) -> bool:
        return self._state["status"] == "running"

    async def run_sync(self) -> None:
        async with self._lock:
            self._state = {
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
                "last_lines": [],
                "exit_code": None,
            }
            self._save_state()

            tmp_dir = tempfile.mkdtemp(prefix="jira-sync-run-")
            try:
                jira_env = dotenv_values(settings.jira_sync_dotenv)
                proc = await asyncio.create_subprocess_exec(
                    *settings.jira_sync_cmd,
                    cwd=tmp_dir,
                    stdout=PIPE,
                    stderr=STDOUT,
                    env={**jira_env, **os.environ, "PYTHONUNBUFFERED": "1"},
                )

                async for raw_line in proc.stdout:
                    line = raw_line.decode(errors="replace").rstrip()
                    formatted = _format_log_line(line)
                    if formatted is None:
                        continue
                    last_lines = self._state["last_lines"]
                    last_lines.append(formatted)
                    if len(last_lines) > settings.log_tail_lines:
                        last_lines.pop(0)
                    self._save_state()

                await proc.wait()

                self._state["status"] = "success" if proc.returncode == 0 else "error"
                self._state["exit_code"] = proc.returncode
                self._state["finished_at"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                self._state["status"] = "error"
                self._state["finished_at"] = datetime.now(timezone.utc).isoformat()
                self._state["last_lines"].append(f"[오류] {e}")
            finally:
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
                self._save_state()


sync_runner = SyncRunner()
