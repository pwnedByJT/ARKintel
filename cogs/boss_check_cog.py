"""
Cog: cogs/boss_check_cog.py
Description: /boss-check slash command — artifact, tribute, tame army,
             and stat threshold checklist for Island boss encounters.
Author: pwnedByJT
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import List
from datetime import datetime, timezone

from data.boss_data import (
    BOSS_DATABASE,
    BOSS_ALIASES,
    TIER_ALIASES,
    resolve_boss,
    resolve_tier,
    get_boss_data,
    list_boss_names,
)

TIER_COLORS = {
    "Gamma": 0x2ECC71,   # Green  — easiest
    "Beta":  0xF39C12,   # Orange — medium
    "Alpha": 0xE74C3C,   # Red    — hardest
}


async def boss_autocomplete(
    itxn: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    if not current:
        return [
            app_commands.Choice(name=d["display_name"], value=d["display_name"])
            for d in BOSS_DATABASE.values()
        ][:25]

    q = current.strip().lower()
    seen: set[str] = set()
    results: list[app_commands.Choice[str]] = []

    for alias, canonical in BOSS_ALIASES.items():
        if q in alias and canonical not in seen:
            results.append(app_commands.Choice(
                name=BOSS_DATABASE[canonical]["display_name"],
                value=BOSS_DATABASE[canonical]["display_name"],
            ))
            seen.add(canonical)

    for canonical, data in BOSS_DATABASE.items():
        if q in data["display_name"].lower() and canonical not in seen:
            results.append(app_commands.Choice(name=data["display_name"], value=data["display_name"]))
            seen.add(canonical)

    return results[:25]


def _build_boss_embed(data: dict) -> discord.Embed:
    color = TIER_COLORS.get(data["tier"], 0x95A5A6)

    embed = discord.Embed(
        title=f"{data['tier']} {data['display_name']} — Entry Checklist",
        color=discord.Color(color),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  Verify tributes against current ASA patch")

    # Artifacts
    embed.add_field(
        name="🏺  Required Artifacts",
        value="```" + "\n".join(data["artifacts"]) + "```",
        inline=False,
    )

    # Tribute items
    embed.add_field(
        name="💀  Apex Tributes",
        value="```" + "\n".join(data["tributes"]) + "```",
        inline=False,
    )

    # Army composition
    embed.add_field(
        name="🦖  Recommended Army",
        value=f"```{data['tames']}```",
        inline=False,
    )

    # Thresholds — inline pair
    embed.add_field(
        name="🛡️  Saddle Requirement",
        value=f"`{data['saddle']}`",
        inline=True,
    )
    embed.add_field(
        name="❤️  HP Floor",
        value=f"`{data['hp_floor']}`",
        inline=True,
    )

    # Warnings
    embed.add_field(
        name="⚠️  Wipe Risks",
        value="\n".join(data["warnings"]),
        inline=False,
    )

    return embed


class BossCheckCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="boss-check",
        description="Entry checklist for Island boss fights — artifacts, tributes, army, and thresholds.",
    )
    @app_commands.describe(
        boss="Boss to check (Broodmother, Megapithecus, Dragon)",
        tier="Difficulty tier (Gamma / Beta / Alpha)",
    )
    @app_commands.autocomplete(boss=boss_autocomplete)
    @app_commands.choices(tier=[
        app_commands.Choice(name="Gamma", value="Gamma"),
        app_commands.Choice(name="Beta",  value="Beta"),
        app_commands.Choice(name="Alpha", value="Alpha"),
    ])
    async def boss_check(
        self,
        itxn: discord.Interaction,
        boss: str,
        tier: app_commands.Choice[str],
    ) -> None:
        canonical_boss = resolve_boss(boss)

        if not canonical_boss:
            q = boss.strip().lower()
            for key, data in BOSS_DATABASE.items():
                if q in data["display_name"].lower():
                    canonical_boss = key
                    break

        if not canonical_boss:
            await itxn.response.send_message(
                f"**[ERROR]** `{boss}` not recognised.\n"
                f"**Supported:** ```{', '.join(list_boss_names())}```",
                ephemeral=True,
            )
            return

        data = get_boss_data(canonical_boss, tier.value)
        if not data:
            await itxn.response.send_message(
                f"**[ERROR]** No data for `{boss} {tier.value}`. Report to pwnedByJT.",
                ephemeral=True,
            )
            return

        await itxn.response.send_message(embed=_build_boss_embed(data))

    @boss_check.error
    async def boss_check_error(self, itxn: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await itxn.response.send_message(f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BossCheckCog(bot))
