"""
Cog: cogs/tame_stats_cog.py
Description: /tame-stats slash command — endgame leveling guide for alpha-tier
             PvP and boss-fight tames in ARK: Survival Ascended.
             Focus: where to dump 88 domestic points post-hatch, key thresholds,
             and tribal meta tips.
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
    """
    Autocomplete for the 'tame' parameter.
    Checks alias keys first (catches shorthand: giga, theri, carcha, daed...),
    then display names. Capped at 25 per Discord limit.
    """
    if not current:
        return [
            app_commands.Choice(name=data["display_name"], value=data["display_name"])
            for data in TAME_DATABASE.values()
        ][:25]

    q = current.strip().lower()
    seen: set[str] = set()
    results: list[app_commands.Choice[str]] = []

    # Alias match first — catches shorthand inputs
    for alias, canonical in TAME_ALIASES.items():
        if q in alias and canonical not in seen:
            display = TAME_DATABASE[canonical]["display_name"]
            results.append(app_commands.Choice(name=display, value=display))
            seen.add(canonical)

    # Display name match — catches full or partial name typing
    for canonical, data in TAME_DATABASE.items():
        if q in data["display_name"].lower() and canonical not in seen:
            results.append(app_commands.Choice(name=data["display_name"], value=data["display_name"]))
            seen.add(canonical)

    return results[:25]


# ---------------------------------------------------------------------------
# EMBED BUILDER
# ---------------------------------------------------------------------------

def _build_tame_embed(tame_data: dict) -> discord.Embed:
    """
    Build the /tame-stats response embed.

    3-field layout:
      🎯  Priority Stat Allocation   — named builds with point dumps
      ⚙️  Key Thresholds & Mechanics — engine caps, rage points, cake thresholds
      💡  Tribe Meta Pro-Tips        — saddles, synergy, usage notes
    """
    embed = discord.Embed(
        title=f"ARK: SA Endgame Leveling Guide - {tame_data['display_name']}",
        description=(
            "Post-hatch/tame leveling strategy for alpha-tier content. "
            "Assumes max imprint, fully mutated lines, and official rates."
        ),
        color=discord.Color(tame_data["color"]),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(
        text="Designed by pwnedByJT  |  ARKintel  |  Update values in data/tame_stats.py"
    )

    # --- Field 1: 🎯 Priority Stat Allocation ---
    builds = tame_data.get("builds", [])
    if builds:
        build_lines = "\n\n".join(
            f"[ {b['name']} ]\n{b['split']}"
            for b in builds
        )
    else:
        build_lines = "No build data available."

    embed.add_field(
        name="🎯  Priority Stat Allocation  (88 domestic pts)",
        value=f"```{build_lines}```",
        inline=False,
    )

    # --- Field 2: ⚙️ Key Thresholds & Mechanics ---
    thresholds = tame_data.get("thresholds", [])
    threshold_text = "\n".join(f"• {t}" for t in thresholds) if thresholds else "No threshold data."
    embed.add_field(
        name="⚙️  Key Thresholds & Mechanics",
        value=threshold_text,
        inline=False,
    )

    # --- Field 3: 💡 Tribe Meta Pro-Tips ---
    tips = tame_data.get("tips", [])
    tips_text = "\n".join(f"• {tip}" for tip in tips) if tips else "No tips available."
    embed.add_field(
        name="💡  Tribe Meta Pro-Tips",
        value=tips_text,
        inline=False,
    )

    return embed


# ---------------------------------------------------------------------------
# COG
# ---------------------------------------------------------------------------

class TameStatsCog(commands.Cog):
    """Slash commands for tame leveling guides and meta strategy."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="tame-stats",
        description="Get an endgame leveling guide for a key ASA tame (PvP / boss / utility).",
    )
    @app_commands.describe(
        tame="Creature to look up — type a name or shorthand (giga, theri, carcha, daed, paracer...)",
    )
    @app_commands.autocomplete(tame=tame_autocomplete)
    async def tame_stats(
        self,
        itxn: discord.Interaction,
        tame: str,
    ) -> None:
        """Return the leveling guide embed for the requested tame."""

        # --- Resolve input → canonical key ---
        canonical_key = resolve_tame(tame)

        # Fallback: substring match against display names
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
                if suggestions
                else "  No close matches found."
            )
            await itxn.response.send_message(
                f"**[ERROR]** `{tame}` was not found in the tame database.\n"
                f"Did you mean:\n{suggestion_block}\n\n"
                f"**All supported tames:**\n"
                f"```{', '.join(list_tame_display_names())}```",
                ephemeral=True,
            )
            return

        tame_data = get_tame_data(canonical_key)
        if not tame_data:
            await itxn.response.send_message(
                "[ERROR] Failed to load tame data. Report this bug to pwnedByJT.",
                ephemeral=True,
            )
            return

        await itxn.response.send_message(embed=_build_tame_embed(tame_data))

    @tame_stats.error
    async def tame_stats_error(
        self,
        itxn: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        await itxn.response.send_message(
            f"[ERROR] Command failed: `{error}`\nContact pwnedByJT if this persists.",
            ephemeral=True,
        )


# ---------------------------------------------------------------------------
# SETUP HOOK
# ---------------------------------------------------------------------------

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TameStatsCog(bot))
