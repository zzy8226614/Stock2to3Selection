from __future__ import annotations

import json
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


class JsonCacheService:
    DEFAULT_RETENTION_DAYS = 30
    RETENTION_ENV = "STOCK_CACHE_RETENTION_DAYS"

    def __init__(self, cache_dir: Path | None = None, retention_days: int | None = None) -> None:
        self.cache_dir = cache_dir or Path(__file__).resolve().parents[1] / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = self._resolve_retention_days(retention_days)
        self.cleanup_expired()

    def _path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace("\\", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def load(self, key: str) -> Any | None:
        path = self._path(key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save(self, key: str, payload: Any) -> None:
        path = self._path(key)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def cleanup_expired(self) -> int:
        if self.retention_days <= 0:
            return 0

        deleted = 0
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=self.retention_days)
        cutoff_timestamp = time.time() - self.retention_days * 24 * 60 * 60

        for path in self.cache_dir.glob("*.json"):
            try:
                cache_date = self._extract_date(path.stem)
                should_delete = cache_date < cutoff_date if cache_date is not None else path.stat().st_mtime < cutoff_timestamp
                if should_delete:
                    path.unlink(missing_ok=True)
                    deleted += 1
            except OSError:
                continue
        return deleted

    def _resolve_retention_days(self, retention_days: int | None) -> int:
        if retention_days is not None:
            return retention_days
        raw_value = os.getenv(self.RETENTION_ENV, str(self.DEFAULT_RETENTION_DAYS)).strip()
        try:
            return int(raw_value)
        except ValueError:
            return self.DEFAULT_RETENTION_DAYS

    def _extract_date(self, key: str) -> date | None:
        match = re.search(r"(20\d{6})", key)
        if not match:
            return None
        try:
            return datetime.strptime(match.group(1), "%Y%m%d").date()
        except ValueError:
            return None
