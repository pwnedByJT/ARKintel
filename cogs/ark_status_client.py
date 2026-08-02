"""
Module: cogs/ark_status_client.py
Description: Thin async HTTP client for the ArkStatus API v1.
             https://arkstatus.com/api-documentation

CONFIRMED API CAPABILITIES (from rendered documentation, 2026-08-02):
  GET /servers                       — paginated server list (aggregate counts only)
  POST /servers/batch                — batch server lookup with 7-day stats
  GET /servers/{id}                  — single server with statistics.7_days block
  GET /servers/{id}/history?hours=N  — 15-min resolution time series
  GET /servers/{id}/preview          — lightweight snapshot
  GET /statistics/player-stats       — global player trends
  GET /statistics/server-distribution
  GET /statistics/platform-stats

CONFIRMED API LIMITATION:
  No per-player endpoint exists anywhere in the API.
  All player fields are aggregate counts (e.g. "players": 45).
  Individual player names, EOS/Steam IDs, and session times are not
  exposed by this API. A live /playerlist command is not implemented.

Auth: X-API-Key header.
Key: ARK_STATUS_API_KEY environment variable.

Author: pwnedByJT
"""

import os
import aiohttp
from typing import Any


BASE_URL = "https://arkstatus.com/api/v1"
_API_KEY  = None  # resolved lazily so os.getenv runs at call-time, not import-time


def _key() -> str | None:
    global _API_KEY
    if _API_KEY is None:
        _API_KEY = os.getenv("ARK_STATUS_API_KEY")
    return _API_KEY


def _headers() -> dict:
    key = _key()
    if not key:
        raise ValueError(
            "ARK_STATUS_API_KEY is not set. "
            "Add it to your .env file: ARK_STATUS_API_KEY=ark_your_key_here"
        )
    return {"X-API-Key": key}


class ArkStatusError(Exception):
    """Raised when the ArkStatus API returns success:false."""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.message = message
        self.code    = code


async def _get(path: str, params: dict | None = None, timeout: int = 10) -> Any:
    """Perform an authenticated GET and return the parsed data payload."""
    url = f"{BASE_URL}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=_headers(),
            params=params,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            body = await resp.json()
            if not body.get("success"):
                err = body.get("error", {})
                raise ArkStatusError(
                    err.get("message", "Unknown API error"),
                    err.get("code",    "UNKNOWN"),
                )
            return body["data"]


async def _post(path: str, json_body: dict, timeout: int = 10) -> Any:
    """Perform an authenticated POST and return the parsed data payload."""
    url = f"{BASE_URL}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            headers={**_headers(), "Content-Type": "application/json"},
            json=json_body,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            body = await resp.json()
            if not body.get("success"):
                err = body.get("error", {})
                raise ArkStatusError(
                    err.get("message", "Unknown API error"),
                    err.get("code",    "UNKNOWN"),
                )
            return body["data"]


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

async def search_servers(
    search: str = "",
    status: str = "online",
    game_mode: str = "",
    platform: str = "",
    sort: str = "players",
    limit: int = 50,
) -> list[dict]:
    """
    Search servers and return a list of server objects.
    Fields include: id, name, map, status, players, max_players,
    player_percentage, platform, game_mode, is_official, last_updated.
    NOTE: statistics block is NOT included — use batch_servers() for 7-day averages.
    """
    params: dict = {"sort": sort}
    if search:
        params["search"] = search
    if status:
        params["status"] = status
    if game_mode:
        params["game_mode"] = game_mode
    if platform:
        params["platform"] = platform

    data = await _get("/servers", params=params)
    servers = data if isinstance(data, list) else data.get("data", data) if isinstance(data, dict) else []

    # Normalise: the /servers list response wraps in data.data under pagination
    if isinstance(data, dict) and "data" in data:
        servers = data["data"]
    elif isinstance(data, list):
        servers = data

    return servers[:limit]


async def batch_servers(ids: list[int]) -> dict:
    """
    Look up multiple servers by numeric ID in one call.
    Returns dict keyed by str(id), each value contains statistics.7_days block:
      { "average_players": 38.5, "peak_players": 68, "uptime_percentage": 98.7 }
    """
    if not ids:
        return {}
    return await _post("/servers/batch", {"ids": ids[:25]})


async def get_server(server_id: int) -> dict:
    """Get full server details including statistics.7_days block."""
    return await _get(f"/servers/{server_id}")


async def get_history(server_id: int, hours: int = 168) -> list[dict]:
    """
    Get time-series history for a server (default 7 days = 168 hours).
    Each bucket: { timestamp, players: {peak, average, minimum}, uptime, data_points }
    Resolution: 15 minutes.
    Rate limit: 5/min (free tier), 30/min (premium).
    """
    data = await _get(f"/servers/{server_id}/history", params={"hours": hours})
    # Response: { server_id, time_range, resolution, data: [...] }
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data if isinstance(data, list) else []
