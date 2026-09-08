from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any

import requests


class GCOError(RuntimeError):
    """An endpoint did not return a usable response."""


@dataclass
class RateLimiter:
    """Thread-safe global minimum interval between request starts."""
    requests_per_second: float = 1.0
    _next_allowed: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def acquire(self) -> None:
        if self.requests_per_second <= 0:
            return
        interval = 1 / self.requests_per_second
        with self._lock:
            now = time.monotonic()
            delay = max(0.0, self._next_allowed - now)
            self._next_allowed = max(now, self._next_allowed) + interval
        if delay:
            time.sleep(delay)


class GCOClient:
    def __init__(self, year: int, *, requests_per_second: float = 1.0,
                 timeout: float = 60, retries: int = 4, session: requests.Session | None = None):
        self.year = year
        self.timeout = timeout
        self.retries = retries
        self.base_url = f"https://gco.iarc.fr/gateway_prod/api/globocan/v3/{year}"
        self.limiter = RateLimiter(requests_per_second)
        self.session = session or requests.Session()
        self.session.headers.update({
            "User-Agent": "globocan-fetch/0.1 (research client; contact: repository issues)",
            "Accept": "application/json",
            "Referer": "https://gco.iarc.who.int/today/en/dataviz/tables",
        })

    def _get_json(self, path: str, params: dict[str, str] | None = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_error: Exception | None = None
        for attempt in range(self.retries):
            self.limiter.acquire()
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                retry_after = response.headers.get("Retry-After")
                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    wait = float(retry_after) if retry_after and retry_after.isdigit() else min(60, 2 ** attempt)
                    time.sleep(wait + random.random() * 0.25)
                    last_error = GCOError(f"HTTP {response.status_code} for {url}")
                    continue
                raise GCOError(f"HTTP {response.status_code} for {url}: {response.text[:200]}")
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < self.retries - 1:
                    time.sleep(min(60, 2 ** attempt) + random.random() * 0.25)
        raise GCOError(f"Failed after {self.retries} attempts: {url}") from last_error

    def populations(self) -> list[dict]:
        data = self._get_json("meta/populations/all/")
        if not isinstance(data, list):
            raise GCOError("Population metadata is not a list")
        return data

    def cancers(self) -> list[dict]:
        data = self._get_json("meta/cancers/all/")
        if not isinstance(data, list):
            raise GCOError("Cancer metadata is not a list")
        return data

    def rates(self, metric: int, sex: int, cancer: int, age_start: int, age_end: int) -> dict:
        data = self._get_json(
            f"data/rate/{metric}/{sex}/all/{cancer}/",
            {"ages_group": f"{age_start}_{age_end}"},
        )
        if not isinstance(data, dict) or not isinstance(data.get("dataset", []), list):
            raise GCOError("Rate response has no list-valued 'dataset'")
        return data
