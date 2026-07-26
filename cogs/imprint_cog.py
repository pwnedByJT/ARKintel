"""
Cog: cogs/imprint_cog.py
Description: /imprint slash command — hatch/cuddle timer with Discord ping alerts
             at 5-minute warning and 0-minute (imprint now) thresholds.
             NOTE: Timers are IN-MEMORY only. Bot restart clears all active timers.
Author: pwnedByJT
"""

import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def parse_hhmin(time_str: str) -> int | None:
    """
    Parse 'HH:MM' → total seconds.
    Returns None on invalid input (non-numeric, out-of-range minutes, etc.).
    """
    parts = time_str.strip().split(":")
    if len(parts) != 2:
        return None
    try:
        h, m = int(parts[0]), int(parts[1])
        if h < 0 or m < 0 or m >= 60:
            return None
        return h * 3600 + m * 60
    except ValueError:
        return None


def fmt_duration(seconds: int) -> str:
    """Format total seconds → 'Xh Ym' or 'Ym Zs'."""
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


# ---------------------------------------------------------------------------
# COG
# ---------------------------------------------------------------------------

class ImprintCog(commands.Cog):
    """Hatch / imprint cuddle timer with @ping alerts."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # user_id → asyncio.Task  (one active timer per user)
        self._tasks: dict[int, asyncio.Task] = {}

    # -----------------------------------------------------------------------
    # BACKGROUND TASK
    # -----------------------------------------------------------------------

    async def _imprint_task(
        self,
        user_id: int,
        channel: discord.TextChannel | discord.DMChannel,
        total_seconds: int,
        creature: str,
        ping_role: Optional[discord.Role],
    ) -> None:
        """
        Sleeps until 5-min warning and 0-min alert.
        Sends channel messages (NOT followup) so the interaction token
        expiry (~15 min) does not break long-running timers.
        """
        mention = ping_role.mention if ping_role else f"<@{user_id}>"

        try:
            if total_seconds > 300:
                await asyncio.sleep(total_seconds - 300)
                await channel.send(
                    f"{mention} ⏰ **5 MINUTE WARNING** — "
                    f"**{creature}** imprint window opens in 5 minutes!",
                    allowed_mentions=discord.AllowedMentions(users=True, roles=True),
                )
                await asyncio.sleep(300)
            else:
                await asyncio.sleep(total_seconds)

            await channel.send(
                f"{mention} 🚨 **IMPRINT NOW** — "
                f"**{creature}** cuddle window is OPEN! Get to it!",
                allowed_mentions=discord.AllowedMentions(users=True, roles=True),
            )
        except asyncio.CancelledError:
            pass
        finally:
            self._tasks.pop(user_id, None)

    # -----------------------------------------------------------------------
    # COMMAND
    # -----------------------------------------------------------------------

    @app_commands.command(
        name="imprint",
        description="Set a hatch/imprint timer. Pings you at 5 min warning and when window opens.",
    )
    @app_commands.describe(
        creature="Name of the creature hatching/imprinting (e.g. Giga, Rex, Theri)",
        time_remaining="Time until next imprint window in HH:MM format (e.g. 02:30, 00:45)",
        ping_role="Optional: ping a tribe role instead of just you (leave blank for personal ping)",
    )
    async def imprint(
        self,
        itxn: discord.Interaction,
        creature: str,
        time_remaining: str,
        ping_role: Optional[discord.Role] = None,
    ) -> None:

        total_seconds = parse_hhmin(time_remaining)

        # --- Input validation ---
        if total_seconds is None:
            await itxn.response.send_message(
                "**[ERROR]** Invalid time format. Use `HH:MM` — e.g. `02:30`, `00:45`, `08:00`.",
                ephemeral=True,
            )
            return

        if total_seconds == 0:
            await itxn.response.send_message(
                "**[ERROR]** Time remaining is 0. The window is already open!",
                ephemeral=True,
            )
            return

        if total_seconds > 86400:  # 24h sanity cap
            await itxn.response.send_message(
                "**[ERROR]** Time exceeds 24 hours. Check your input.",
                ephemeral=True,
            )
            return

        # --- Cancel any existing timer for this user ---
        existing = self._tasks.get(itxn.user.id)
        if existing and not existing.done():
            existing.cancel()

        # --- Calculate fire times ---
        now      = datetime.now(timezone.utc)
        fire_at  = now + timedelta(seconds=total_seconds)
        warn_at  = fire_at - timedelta(minutes=5) if total_seconds > 300 else None

        creature_clean = creature.strip().title()
        channel        = itxn.channel

        # --- Start background task ---
        task = asyncio.get_event_loop().create_task(
            self._imprint_task(
                user_id=itxn.user.id,
                channel=channel,
                total_seconds=total_seconds,
                creature=creature_clean,
                ping_role=ping_role,
            )
        )
        self._tasks[itxn.user.id] = task

        # --- Confirm embed ---
        role_line = ping_role.mention if ping_role else f"<@{itxn.user.id}>"
        embed = discord.Embed(
            title=f"Imprint Timer Set — {creature_clean}",
            color=discord.Color(0x3498DB),
            timestamp=now,
        )
        embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  In-memory only — clears on restart")

        embed.add_field(
            name="⏱️  Timer Details",
            value=(
                f"```"
                f"Creature     {creature_clean}\n"
                f"Time Left    {fmt_duration(total_seconds)}\n"
                f"Window At    {fire_at.strftime('%H:%M UTC')}\n"
                f"5-Min Warn   {warn_at.strftime('%H:%M UTC') if warn_at else 'Skipped (< 5 min)'}"
                f"```"
            ),
            inline=False,
        )
        embed.add_field(
            name="🔔  Ping Target",
            value=role_line,
            inline=False,
        )
        embed.add_field(
            name="⚠️  Notice",
            value="• Timer lives in memory only. Bot restart = timer lost.\n"
                  "• Starting a new `/imprint` cancels your current timer.",
            inline=False,
        )

        await itxn.response.send_message(embed=embed)

    @imprint.error
    async def imprint_error(self, itxn: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await itxn.response.send_message(
            f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True
        )

    # -----------------------------------------------------------------------
    # CANCEL COMMAND
    # -----------------------------------------------------------------------

    @app_commands.command(
        name="imprint-cancel",
        description="Cancel your active imprint timer.",
    )
    async def imprint_cancel(self, itxn: discord.Interaction) -> None:
        task = self._tasks.get(itxn.user.id)
        if task and not task.done():
            task.cancel()
            self._tasks.pop(itxn.user.id, None)
            await itxn.response.send_message("✅ Imprint timer cancelled.", ephemeral=True)
        else:
            await itxn.response.send_message("No active imprint timer found.", ephemeral=True)

    # -----------------------------------------------------------------------
    # CLEANUP ON UNLOAD
    # -----------------------------------------------------------------------

    async def cog_unload(self) -> None:
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImprintCog(bot))
