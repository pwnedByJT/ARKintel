"""
Cog: cogs/tame_stats_cog.py
Description: /tame-stats slash command — endgame/meta stat allocation guidelines
             for alpha-tier PvP and boss-fight tames in ARK: Survival Ascended.
Author: pwnedByJT
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
from datetime import datetime, timezone

from data.tame_stats import (
    TAME_DATABASE,
    TAME_ALIASES,
    VALID_ROLES,
    resolve_tame,
    get_tame_data,
    search_tames,
    list_tame_display_names,
)


# ---------------------------------------------------------------------------
# AUTOCOMPLETE CALLBACKS
# ---------------------------------------------------------------------------

async def tame_autocomplete(
    itxn: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    """
    Autocomplete for the 'tame' parameter.
    Searches alias keys + display names for partial matches.
    """
    if not current:
        # Return a sampler of all available tames when field is empty
        return [
            app_commands.Choice(name=data["display_name"], value=data["display_name"])
            for data in list(TAME_DATABASE.values())
        ][:25]

    q = current.strip().lower()
    seen: set[str] = set()
    results: list[app_commands.Choice[str]] = []

    # Match against alias keys first (catches shorthand like "giga", "theri")
    for alias, canonical in TAME_ALIASES.items():
        if q in alias and canonical not in seen:
            display = TAME_DATABASE[canonical]["display_name"]
            results.append(app_commands.Choice(name=display, value=display))
            seen.add(canonical)

    # Also match against display names directly
    for canonical, data in TAME_DATABASE.items():
        if q in data["display_name"].lower() and canonical not in seen:
            results.append(app_commands.Choice(name=data["display_name"], value=data["display_name"]))
            seen.add(canonical)

    return results[:25]


# ---------------------------------------------------------------------------
# EMBED BUILDER
# ---------------------------------------------------------------------------

def _build_tame_embed(data: dict) -> discord.Embed:
    """
    Construct the /tame-stats response embed from a resolved stat block.
    Note: This command intentionally uses structured emoji headers per user spec,
    which is a deviation from the bot's general No-Emote policy.
    """
    embed = discord.Embed(
        title=f"{data['display_name']}  —  {data['role']}",
        description=(
            "Alpha-tier endgame stat guidelines for ASA. "
            "All values assume fully mutated lines (20/20 pat/mat), "
            "max imprint, and official rates. Adjust for custom servers."
        ),
        color=discord.Color(data["color"]),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  Baseline estimates — edit data/tame_stats.py")

    # --- Field 1: Priority ---
    embed.add_field(
        name="[PRIORITY]  Stat Allocation Order",
        value=f"```{data['priority']}```",
        inline=False,
    )

    # --- Field 2: Target Stats ---
    stats_lines = "\n".join(
        f"{stat:<12} {value}"
        for stat, value in data["target_stats"].items()
    )
    embed.add_field(
        name="[TARGETS]  Post-Mutated Endgame Stats",
        value=f"```{stats_lines}```",
        inline=False,
    )

    # --- Field 3: Domestic Level Distribution ---
    embed.add_field(
        name="[LEVELS]  Domestic Point Distribution  (88 pts total)",
        value=f"```{data['level_split']}```",
        inline=False,
    )

    # --- Field 4: Pro Tips ---
    tips_text = "\n".join(f"• {tip}" for tip in data["tips"])
    embed.add_field(
        name="[META]  Pro Tips & Gear Requirements",
        value=tips_text,
        inline=False,
    )

    return embed


# ---------------------------------------------------------------------------
# COG
# ---------------------------------------------------------------------------

class TameStatsCog(commands.Cog):
    """Slash commands for tame stat allocation and meta guidelines."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="tame-stats",
        description="Get endgame/meta stat allocation for a key ASA tame (alpha PvP / boss-fight focused).",
    )
    @app_commands.describe(
        tame="The creature to look up (e.g. Giganotosaurus, Theri, Giga, Rex, Carcha...)",
        role="Intended role/context (defaults to General Meta)",
    )
    @app_commands.autocomplete(tame=tame_autocomplete)
    @app_commands.choices(role=[
        app_commands.Choice(name=r, value=r) for r in VALID_ROLES
    ])
    async def tame_stats(
        self,
        itxn: discord.Interaction,
        tame: str,
        role: Optional[app_commands.Choice[str]] = None,
    ) -> None:
        """Return a stat allocation embed for the requested tame and role."""

        # Resolve input → canonical key
        canonical_key = resolve_tame(tame)

        # Fallback: try matching by display name if alias lookup missed
        if not canonical_key:
            q = tame.strip().lower()
            for key, data in TAME_DATABASE.items():
                if q in data["display_name"].lower() or data["display_name"].lower() in q:
                    canonical_key = key
                    break

        if not canonical_key:
            # Suggest close matches
            suggestions = search_tames(tame)
            suggestion_text = (
                "\n".join(f"  • {s}" for s in suggestions[:5])
                if suggestions
                else "  No close matches found."
            )
            await itxn.response.send_message(
                f"**[ERROR]** `{tame}` was not found in the tame database.\n"
                f"Did you mean one of these?\n{suggestion_text}\n\n"
                f"Full list of supported tames:\n"
                f"```{', '.join(list_tame_display_names())}```",
                ephemeral=True,
            )
            return

        # Resolve role
        requested_role = role.value if role else "General Meta"

        # Fetch stat block
        stat_data = get_tame_data(canonical_key, requested_role)
        if not stat_data:
            await itxn.response.send_message(
                "[ERROR] Failed to load stat data. This is a bug — report to pwnedByJT.",
                ephemeral=True,
            )
            return

        embed = _build_tame_embed(stat_data)
        await itxn.response.send_message(embed=embed)

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
# SETUP HOOK  (called by bot.load_extension or direct add_cog)
# ---------------------------------------------------------------------------

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TameStatsCog(bot))
