from __future__ import annotations

import os


PROXY_ENV_KEYS = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)

BAD_PROXY_TOKENS = (
    "127.0.0.1:9",
    "localhost:9",
    "[::1]:9",
)


def sanitize_proxy_environment() -> dict[str, str]:
    """Remove inherited dead proxy settings that break local market-data fetches."""
    removed: dict[str, str] = {}
    for key in PROXY_ENV_KEYS:
        value = os.environ.get(key)
        if value and any(token in value for token in BAD_PROXY_TOKENS):
            removed[key] = value
            os.environ.pop(key, None)

    no_proxy_values = ["127.0.0.1", "localhost", "::1", "10.0.28.54"]
    existing_no_proxy = os.environ.get("NO_PROXY") or os.environ.get("no_proxy")
    if existing_no_proxy:
        known = {item.strip() for item in existing_no_proxy.split(",") if item.strip()}
        for value in no_proxy_values:
            known.add(value)
        no_proxy = ",".join(sorted(known))
    else:
        no_proxy = ",".join(no_proxy_values)
    os.environ["NO_PROXY"] = no_proxy
    os.environ["no_proxy"] = no_proxy
    return removed


REMOVED_PROXY_ENV = sanitize_proxy_environment()
