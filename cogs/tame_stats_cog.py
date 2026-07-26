"""
Cog: cogs/tame_stats_cog.py
Description: /tame-stats slash command — hyper-concise endgame leveling guides
             for alpha-tier PvP and boss tames in ARK: Survival Ascended.
Author: pwnedByJT
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import List
from datetime import datetime, timezone

from data.tame_stats import (
    TAME_DATABASE,
    TAME_ALIASES,
    resolve_tame,
    get_tame_data,
    search_tames,
    list_tame_display_names,
)


# ---------------------------------------------------------------------------
# AUTOCOMPLETE
# ---------------------------------------------------------------------------

async def tame_autocomplete(
    itxn: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    if not current:
        return [
            app_commands.Choice(name=data["display_name"], value=data["display_name"])
            for data in TAME_DATABASE.values()
        ][:25]

    q = current.strip().lower()
    seen: set[str] = set()
    results: list[app_commands.Choice[str]] = []

    for alias, canonical in TAME_ALIASES.items():
        if q in alias and canonical not in seen:
            display = TAME_DATABASE[canonical]["display_name"]
            results.append(app_commands.Choice(name=display, value=display))
            seen.add(canonical)

    for canonical, data in TAME_DATABASE.items():
        if q in data["display_name"].lower() and canonical not in seen:
            results.append(app_commands.Choice(name=data["display_name"], value=data["display_name"]))
            seen.add(canonical)

    return results[:25]


# ---------------------------------------------------------------------------
# EMBED BUILDER
# ---------------------------------------------------------------------------

def _format_builds(builds: list[dict]) -> str:
    """
    Format named builds into a scannable code block.

    Output:
        [ Sky Freighter ]
        • 80 Pts → Weight
        • 8 Pts  → Stamina

        [ Mobile Raid FOB ]
        • 60 Pts → Weight
        ...
    """
    sections = []
    for build in builds:
        lines = [f"[ {build['name']} ]"]
        for pt in build["points"]:
            lines.append(f"• {pt}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def _build_tame_embed(tame_data: dict) -> discord.Embed:
    """
    3-field hyper-concise embed:
      🎯  Priority Stat Allocation
      ⚙️  Key Caps & Thresholds     (max 2 bullets)
      💡  Tribe Pro-Tips             (max 2 bullets)
    """
    embed = discord.Embed(
        title=f"ARK: SA Endgame Leveling Guide - {tame_data['display_name']}",
        description=tame_data["meta"],
        color=discord.Color(tame_data["color"]),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(
        text="Designed by pwnedByJT  |  ARKintel  |  Edit: data/tame_stats.py"
    )

    # 🎯 Allocation
    embed.add_field(
        name="🎯  Priority Stat Allocation  (88 domestic pts)",
        value=f"```{_format_builds(tame_data['builds'])}```",
        inline=False,
    )

    # ⚙️ Thresholds — max 2 bullets
    thresholds = tame_data.get("thresholds", [])
    embed.add_field(
        name="⚙️  Key Caps & Thresholds",
        value="\n".join(thresholds) if thresholds else "• N/A",
        inline=False,
    )

    # 💡 Tips — max 2 bullets
    tips = tame_data.get("tips", [])
    embed.add_field(
        name="💡  Tribe Pro-Tips",
        value="\n".join(tips) if tips else "• N/A",
        inline=False,
    )

    return embed


# ---------------------------------------------------------------------------
# COG
# ---------------------------------------------------------------------------

class TameStatsCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="tame-stats",
        description="Endgame leveling guide for a key ASA tame — where to dump your 88 pts.",
    )
    @app_commands.describe(
        tame="Creature name or shorthand (giga, theri, carcha, daed, paracer, dunk...)",
    )
    @app_commands.autocomplete(tame=tame_autocomplete)
    async def tame_stats(self, itxn: discord.Interaction, tame: str) -> None:
        canonical_key = resolve_tame(tame)

        if not canonical_key:
            q = tame.strip().lower()
            for key, data in TAME_DATABASE.items():
                if q in data["display_name"].lower() or data["display_name"].lower() in q:
                    canonical_key = key
                    break

        if not canonical_key:
            suggestions = search_tames(tame)
            suggestion_block = (
                "\n".join(f"  • {s}" for s in suggestions[:5])
                if suggestions else "  No close matches found."
            )
            await itxn.response.send_message(
                f"**[ERROR]** `{tame}` not found.\nDid you mean:\n{suggestion_block}\n\n"
                f"**Supported tames:**\n```{', '.join(list_tame_display_names())}```",
                ephemeral=True,
            )
            return

        tame_data = get_tame_data(canonical_key)
        if not tame_data:
            await itxn.response.send_message(
                "[ERROR] Failed to load tame data. Report to pwnedByJT.",
                ephemeral=True,
            )
            return

        await itxn.response.send_message(embed=_build_tame_embed(tame_data))

    @tame_stats.error
    async def tame_stats_error(self, itxn: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await itxn.response.send_message(
            f"[ERROR] `{error}` — contact pwnedByJT.",
            ephemeral=True,
        )


# ---------------------------------------------------------------------------
# SETUP HOOK
# ---------------------------------------------------------------------------

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TameStatsCog(bot))
