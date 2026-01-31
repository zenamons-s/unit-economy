"""
Utilities for resolving database paths consistently across entrypoints.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def resolve_db_path(db_path: Optional[str] = None) -> Path:
    """Resolve the database path using env/secrets and repo-relative defaults."""

    candidate = db_path or os.getenv("DB_PATH")

    if not candidate:
        try:
            import streamlit as st  # type: ignore

            if "DB_PATH" in st.secrets:
                candidate = st.secrets["DB_PATH"]
        except Exception:
            candidate = None

    if not candidate:
        candidate = "database/saas_finance.db"

    path = Path(candidate)
    if not path.is_absolute():
        repo_root = Path(__file__).resolve().parents[1]
        path = repo_root / path

    return path
