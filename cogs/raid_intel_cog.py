"""
Cog: cogs/raid_intel_cog.py
Description: /raidwindow — population analytics and offline-raid target scouting.

Scans historical population data (collected by /monitor) to surface servers
with healthy weekly activity but predictable low-population windows — the
optimal windows for offline raids or server transfers.

Logic:
  1. Qualify servers: weekly average population > min_avg (default 3).
  2. For each qualifying server find the UTC hour with the lowest average
     population, requiring at least 3 data points for that hour (guards
     against a single stray 0-pop sample winning as a false raid window).
  3. Return a ranked embed (highest weekly avg first — more active servers
     have more to raid).

Important caveat: population history only exists for servers that were
previously tracked via /monitor. This command operates on that monitored
subset, not the entire official server list.

Author: pwnedByJT
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# TIME HELPERS
# ---------------------------------------------------------------------------

def _fmt_utc(hour: int) -> str:
    return f"{hour:02d}:00 UTC"


def _fmt_approx_pt(hour: int) -> str:
    """
    Approximate Pacific Time. Offset is -7 (PDT, Mar–Nov) or -8 (PST, Nov–Mar).
    Labelled 'approx PT' so the output stays correct year-round without DST logic.
    """
    pt_hour = (hour - 7) % 24
    period  = "AM" if pt_hour < 12 else "PM"
    display = pt_hour % 12 or 12
    return f"{display}:00 {period} PT (approx)"


# ---------------------------------------------------------------------------
# EMBED BUILDERS
# ---------------------------------------------------------------------------

def _build_raidwindow_embed(results: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title="Raid Intel — Low-Pop Windows",
        description=(
            "Servers ranked by weekly average population. "
            "Quiet window = the UTC hour with the lowest average player count over the past 7 days.\n"
            "**Data source:** servers actively tracked via `/monitor` only."
        ),
        color=discord.Color(0xED4245),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  Minimum 3 samples/hour required")

    for entry in results:
        srv          = entry["server_name"]
        weekly_avg   = entry["weekly_avg"]
        window       = entry.get("window")

        if window:
            h   = window["hour_utc"]
            pop = window["avg_pop"]
            window_str = f"`{_fmt_utc(h)}`  /  `{_fmt_approx_pt(h)}`\nAvg pop during window: `{pop}`"
        else:
            window_str = "`Insufficient hourly data — monitor longer for a reliable window`"

        embed.add_field(
            name=f"{srv}",
            value=f"Weekly Avg: `{weekly_avg}` players\nQuiet Window: {window_str}",
            inline=False,
        )

    return embed


def _build_no_data_embed(min_avg: float) -> discord.Embed:
    embed = discord.Embed(
        title="Raid Intel — No Qualifying Servers",
        description=(
            f"No monitored servers have a weekly average population above **{min_avg}** "
            f"with enough data to analyze.\n\n"
            f"Start tracking servers with `/monitor` and run this command again after "
            f"accumulating at least a day of data."
        ),
        color=discord.Color(0xFEE75C),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel")
    return embed


# ---------------------------------------------------------------------------
# COG
# ---------------------------------------------------------------------------

class RaidIntelCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @property
    def _db(self):
        """Fetch the shared DatabaseEngine from ARKCog at call-time (no re-init)."""
        cog = self.bot.get_cog("ARKCog")
        return cog.db if cog else None

    @app_commands.command(
        name="raidwindow",
        description="Identify prime offline-raid targets by weekly avg pop and low-pop windows.",
    )
    @app_commands.describe(
        min_avg="Minimum weekly average population to qualify a server (default 3)",
    )
    async def raidwindow(self, itxn: discord.Interaction, min_avg: int = 3) -> None:
        await itxn.response.defer()

        db = self._db
        if not db:
            return await itxn.followup.send(
                "[ERROR] Analytics engine unavailable — ARKCog not loaded.",
                ephemeral=True,
            )

        # Step 1: qualifying servers
        targets = await db.get_scout_targets(min_avg=float(min_avg))
        if not targets:
            return await itxn.followup.send(embed=_build_no_data_embed(min_avg))

        # Step 2: enrich each server with its quiet window
        for entry in targets:
            entry["window"] = await db.get_quiet_window(entry["server_name"])

        await itxn.followup.send(embed=_build_raidwindow_embed(targets))

    @raidwindow.error
    async def raidwindow_error(self, itxn: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await itxn.response.send_message(
            f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RaidIntelCog(bot))
