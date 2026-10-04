"""Centralized configuration."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path


def get_project_root() -> Path:
    """Return project root (folder containing pyproject.toml)."""
    current = Path(__file__).resolve()
    for parent in [current.parent, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return current.parents[2]


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure root logging once and return a namespaced logger."""
    resolved = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, resolved, logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    return logging.getLogger("data_governance")


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings."""

    project_root: Path
    database_path: Path
    log_level: str


def load_settings() -> Settings:
    """Load settings from environment with local defaults."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        pass
    else:
        root = get_project_root()
        env_file = root / ".env"
        if env_file.exists():
            load_dotenv(env_file)

    root = get_project_root()
    db = Path(os.getenv("DATABASE_PATH", "data/governance.db"))
    if not db.is_absolute():
        db = root / db
    return Settings(project_root=root, database_path=db, log_level=os.getenv("LOG_LEVEL", "INFO"))
