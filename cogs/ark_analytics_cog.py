"""
Cog: cogs/ark_analytics_cog.py
Description: ArkStatus-powered server analytics and raid-target scouting.

Command: /targets
  Queries the ArkStatus API to surface ARK servers matching a name search,
  filters by 7-day average population (>= min_avg), then fetches 7-day
  population history to identify each server's lowest-traffic hour of the day
  — the ideal offline raid or scouting window.

Why this is better than /raidwindow:
  /raidwindow runs against locally-monitored servers only (requires /monitor).
  /targets uses ArkStatus which tracks thousands of servers independently.

Data flow:
  1. /servers?search=... — find candidate server IDs and current pop
  2. /servers/batch       — get 7-day stats in one call, filter by avg pop
  3. /servers/{id}/history?hours=168  — 15-min time series, group by UTC hour

CONFIRMED API LIMITATION (arkstatus.com/api-documentation, 2026-08-02):
  ArkStatus does NOT expose individual player names, EOS/Steam IDs, or session
  times anywhere in its API. All player fields are aggregate counts.
  A live /playerlist command is not implemented. Use /tag-player and
  /player-info (cogs/player_intel_cog.py) for manual player identity tracking.

Author: pwnedByJT
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from collections import defaultdict

from cogs.ark_status_client import (
    search_servers,
    batch_servers,
    get_history,
    ArkStatusError,
)


# ---------------------------------------------------------------------------
# ANALYTICS HELPERS
# ---------------------------------------------------------------------------

def _hourly_averages(history: list[dict]) -> dict[int, float]:
    """
    Reduce 15-min history buckets to per-UTC-hour averages.
    Returns {hour_int: avg_players_float} for hours that have >= 3 data points.
    """
    buckets: dict[int, list[float]] = defaultdict(list)
    for entry in history:
        ts_str = entry.get("timestamp", "")
        if not ts_str:
            continue
        try:
            hour = int(ts_str[11:13])   # "2025-01-07T12:15:00" → 12
        except (IndexError, ValueError):
            continue
        avg_pop = entry.get("players", {}).get("average")
        if avg_pop is not None:
            buckets[hour].append(float(avg_pop))

    return {
        h: round(sum(v) / len(v), 1)
        for h, v in buckets.items()
        if len(v) >= 3   # guard: require at least 3 samples per hour slot
    }


def _quiet_window(hourly: dict[int, float]) -> tuple[int, float] | None:
    """Return (hour_utc, avg_pop) for the quietest hour, or None."""
    if not hourly:
        return None
    return min(hourly.items(), key=lambda kv: (kv[1], -kv[0]))


def _fmt_approx_pt(hour_utc: int) -> str:
    """UTC → approx Pacific Time (UTC-7 summer / UTC-8 winter, labelled 'approx PT')."""
    pt_hour = (hour_utc - 7) % 24
    period  = "AM" if pt_hour < 12 else "PM"
    display = pt_hour % 12 or 12
    return f"{display}:00 {period} PT (approx)"


# ---------------------------------------------------------------------------
# EMBED BUILDERS
# ---------------------------------------------------------------------------

def _build_targets_embed(results: list[dict], search: str, min_avg: int) -> discord.Embed:
    embed = discord.Embed(
        title="Raid Targets — Low-Pop Windows",
        description=(
            f"Search: `{search or 'all'}` · Min weekly avg: `{min_avg}` players\n"
            "Quiet window = UTC hour with lowest average population over the past 7 days."
        ),
        color=discord.Color(0xED4245),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  Powered by ArkStatus API")

    for srv in results:
        name       = srv["name"]
        avg_7d     = srv.get("avg_7d", "N/A")
        peak_7d    = srv.get("peak_7d", "N/A")
        game_mode  = srv.get("game_mode", "?")
        platform   = srv.get("platform", "?")
        quiet      = srv.get("quiet_window")

        if quiet:
            h, pop = quiet
            window_str = f"`{h:02d}:00 UTC`  /  `{_fmt_approx_pt(h)}`\nAvg pop at window: `{pop}`"
        else:
            window_str = "`Insufficient history data`"

        embed.add_field(
            name=f"{name}",
            value=(
                f"7-Day Avg: `{avg_7d}` · Peak: `{peak_7d}` · {game_mode} / {platform}\n"
                f"Quiet Window: {window_str}"
            ),
            inline=False,
        )

    return embed


def _build_no_results_embed(search: str, min_avg: int) -> discord.Embed:
    return discord.Embed(
        title="Raid Targets — No Qualifying Servers",
        description=(
            f"No online servers matching `{search or 'all'}` have a 7-day average "
            f"population above **{min_avg}**.\n\nTry a different search term or lower `min_avg`."
        ),
        color=discord.Color(0xFEE75C),
        timestamp=datetime.now(timezone.utc),
    )


def _build_error_embed(err: ArkStatusError) -> discord.Embed:
    is_auth = err.code in ("AUTHENTICATION_REQUIRED", "INVALID_API_KEY")
    desc = (
        "**API key missing or invalid.**\n"
        "Add `ARK_STATUS_API_KEY=ark_your_key_here` to your `.env` file.\n"
        "Generate a key at arkstatus.com/settings#api-key-section."
        if is_auth else
        f"ArkStatus API error: `{err.message}` (code: `{err.code}`)"
    )
    return discord.Embed(
        title="[ERROR]  ArkStatus API",
        description=desc,
        color=discord.Color(0xED4245),
        timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# COG
# ---------------------------------------------------------------------------

class ArkAnalyticsCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="targets",
        description="Find prime raid targets by 7-day avg pop and lowest-traffic hour (ArkStatus).",
    )
    @app_commands.describe(
        search="Server name prefix to search (e.g. 'NA-PVP-Official'). Leave blank for all.",
        min_avg="Minimum 7-day average population to qualify (default 3).",
        limit="Max servers to fully analyse — capped at 5 due to API rate limits (default 3).",
    )
    async def targets(
        self,
        itxn: discord.Interaction,
        search: str = "",
        min_avg: int = 3,
        limit: int = 3,
    ) -> None:
        await itxn.response.defer()

        limit = max(1, min(limit, 5))  # hard cap at 5 (history endpoint is rate-limited)

        try:
            # Step 1: find candidate servers by name search
            candidates = await search_servers(search=search, status="online", sort="players")
        except ArkStatusError as e:
            return await itxn.followup.send(embed=_build_error_embed(e))
        except Exception as e:
            return await itxn.followup.send(
                f"[ERROR] Failed to reach ArkStatus API: `{e}`", ephemeral=True
            )

        if not candidates:
            return await itxn.followup.send(embed=_build_no_results_embed(search, min_avg))

        # Step 2: batch-fetch 7-day stats for up to 25 candidates in one call
        candidate_ids = [s["id"] for s in candidates if "id" in s][:25]
        try:
            batch = await batch_servers(candidate_ids)
        except ArkStatusError as e:
            return await itxn.followup.send(embed=_build_error_embed(e))
        except Exception as e:
            return await itxn.followup.send(
                f"[ERROR] Batch lookup failed: `{e}`", ephemeral=True
            )

        # Step 3: filter by 7-day average >= min_avg, sort by avg desc
        qualified = []
        for srv in candidates:
            srv_id   = srv.get("id")
            srv_data = batch.get(str(srv_id), {})
            stats    = srv_data.get("statistics", {}).get("7_days", {})
            avg_7d   = stats.get("average_players")
            if avg_7d is None or avg_7d < min_avg:
                continue
            qualified.append({
                "id":        srv_id,
                "name":      srv.get("name", str(srv_id)),
                "game_mode": srv.get("game_mode", "?"),
                "platform":  srv.get("platform", "?"),
                "avg_7d":    round(avg_7d, 1),
                "peak_7d":   stats.get("peak_players", "N/A"),
            })

        qualified.sort(key=lambda s: s["avg_7d"], reverse=True)
        qualified = qualified[:limit]

        if not qualified:
            return await itxn.followup.send(embed=_build_no_results_embed(search, min_avg))

        # Step 4: fetch 7-day history for each qualifying server and find quiet window
        for srv in qualified:
            try:
                history = await get_history(srv["id"], hours=168)
                hourly  = _hourly_averages(history)
                srv["quiet_window"] = _quiet_window(hourly)
            except ArkStatusError:
                srv["quiet_window"] = None
            except Exception:
                srv["quiet_window"] = None

        await itxn.followup.send(embed=_build_targets_embed(qualified, search, min_avg))

    @targets.error
    async def targets_error(self, itxn: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await itxn.response.send_message(
            f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ArkAnalyticsCog(bot))
