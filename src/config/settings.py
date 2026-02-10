import itertools
import threading

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini (comma-separated for round-robin)
    gemini_api_keys: str = ""
    gemini_model: str = "gemini-2.0-flash"
    temperature: float = 0.1
    top_p: float = 0.9

    # Jira
    jira_server: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "PROJ"

    # User identity (used so the assistant knows who "me" is)
    user_name: str = "Sherwin"

    # Google OAuth
    google_credentials_file: str = "credentials.json"
    google_token_file: str = "token.json"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"

    # SQLite
    sqlite_db_path: str = "./reminders.db"

    # Reranker
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # RAG
    retrieval_top_k: int = 10
    rerank_top_n: int = 5

    # Cache TTLs (seconds)
    retrieval_cache_ttl: int = 600
    response_cache_ttl: int = 300

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


class _KeyRotator:
    """Thread-safe round-robin API key rotator."""

    def __init__(self, keys_csv: str):
        keys = [k.strip() for k in keys_csv.split(",") if k.strip()]
        if not keys:
            raise ValueError("No Gemini API keys configured")
        self._cycle = itertools.cycle(keys)
        self._lock = threading.Lock()
        self.count = len(keys)

    def next(self) -> str:
        with self._lock:
            return next(self._cycle)


gemini_key_rotator = _KeyRotator(settings.gemini_api_keys)
