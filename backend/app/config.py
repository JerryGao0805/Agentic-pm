from dataclasses import dataclass
import os


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "pm-backend")
    db_host: str = os.getenv("DB_HOST", "mysql")
    db_port: int = _int_env("DB_PORT", 3306)
    db_user: str = os.getenv("DB_USER", "pm_user")
    db_password: str = os.getenv("DB_PASSWORD", "pm_password")
    db_name: str = os.getenv("DB_NAME", "pm_db")


settings = Settings()
