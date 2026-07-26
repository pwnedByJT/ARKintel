"""
Cog: cogs/raid_calc_cog.py
Description: /raid-calc slash command — explosive requirements and raw material costs
             for destroying ASA structures.
Author: pwnedByJT
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import List
from datetime import datetime, timezone

from data.raid_data import (
    STRUCTURE_DATABASE,
    STRUCTURE_ALIASES,
    calculate_explosives,
    resolve_structure,
    list_structure_names,
)


async def structure_autocomplete(
    itxn: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    if not current:
        return [
            app_commands.Choice(name=d["display_name"], value=d["display_name"])
            for d in STRUCTURE_DATABASE.values()
        ][:25]

    q = current.strip().lower()
    seen: set[str] = set()
    results: list[app_commands.Choice[str]] = []

    for alias, canonical in STRUCTURE_ALIASES.items():
        if q in alias and canonical not in seen:
            results.append(app_commands.Choice(
                name=STRUCTURE_DATABASE[canonical]["display_name"],
                value=STRUCTURE_DATABASE[canonical]["display_name"],
            ))
            seen.add(canonical)

    for canonical, data in STRUCTURE_DATABASE.items():
        if q in data["display_name"].lower() and canonical not in seen:
            results.append(app_commands.Choice(name=data["display_name"], value=data["display_name"]))
            seen.add(canonical)

    return results[:25]


def _build_raid_embed(result: dict) -> discord.Embed:
    structure   = result["structure"]
    quantity    = result["quantity"]
    total_hp    = result["total_hp"]
    explosives  = result["explosives"]

    embed = discord.Embed(
        title=f"Raid Calc — {structure['display_name']}  x{quantity}",
        description=f"{structure['notes']}",
        color=discord.Color(0xE74C3C),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  Verify damage values in-game")

    # Summary line
    embed.add_field(
        name="📊  Target",
        value=f"```{quantity}x {structure['display_name']}  |  Total HP: {total_hp:,}```",
        inline=False,
    )

    # One field per explosive type
    for exp_key, exp in explosives.items():
        mat_lines = "\n".join(
            f"{mat:<20} {amt:,}"
            for mat, amt in exp["raw_materials"].items()
        )
        embed.add_field(
            name=f"💣  {exp['display_name']}  ×{exp['count']:,}",
            value=f"```Raw materials to craft {exp['count']:,}:\n{mat_lines}```",
            inline=False,
        )

    return embed


class RaidCalcCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="raid-calc",
        description="Calculate explosives and raw materials needed to destroy a structure.",
    )
    @app_commands.describe(
        structure="Structure type to destroy (Metal Wall, Tek Wall, Vault...)",
        quantity="Number of that structure to destroy (default: 1)",
    )
    @app_commands.autocomplete(structure=structure_autocomplete)
    async def raid_calc(
        self,
        itxn: discord.Interaction,
        structure: str,
        quantity: int = 1,
    ) -> None:
        if quantity < 1 or quantity > 500:
            await itxn.response.send_message(
                "**[ERROR]** Quantity must be between 1 and 500.", ephemeral=True
            )
            return

        canonical = resolve_structure(structure)
        if not canonical:
            q = structure.strip().lower()
            for key, data in STRUCTURE_DATABASE.items():
                if q in data["display_name"].lower():
                    canonical = key
                    break

        if not canonical:
            await itxn.response.send_message(
                f"**[ERROR]** `{structure}` not found.\n"
                f"**Supported:** ```{', '.join(list_structure_names())}```",
                ephemeral=True,
            )
            return

        result = calculate_explosives(canonical, quantity)
        await itxn.response.send_message(embed=_build_raid_embed(result))

    @raid_calc.error
    async def raid_calc_error(self, itxn: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await itxn.response.send_message(f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RaidCalcCog(bot))
