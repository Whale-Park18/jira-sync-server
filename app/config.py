import os


def _require(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise RuntimeError(f"환경변수 {key}가 설정되지 않았습니다.")
    return val


class Settings:
    def __init__(self) -> None:
        self.server_password: str = _require("SERVER_PASSWORD")
        self.secret_key: str = _require("SECRET_KEY")
        self.session_cookie_name: str = os.environ.get("SESSION_COOKIE_NAME", "session")
        self.session_max_age: int = int(os.environ.get("SESSION_MAX_AGE_SECONDS", "86400"))
        self.jira_sync_config: str = os.environ.get("JIRA_SYNC_CONFIG", "/config/sync_config.yaml")
        self.jira_sync_dotenv: str = os.environ.get("JIRA_SYNC_DOTENV", "/config/.env")
        self.jira_sync_cmd: list[str] = ["sync", "--config", self.jira_sync_config]
        self.state_file_path: str = os.environ.get("STATE_FILE_PATH", "/data/state.json")
        self.log_tail_lines: int = int(os.environ.get("LOG_TAIL_LINES", "50"))


settings = Settings()
