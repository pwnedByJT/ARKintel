"""
Cog: cogs/recipe_cog.py
Description: /recipe slash command — endgame consumable quick-reference.
Author: pwnedByJT
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import List
from datetime import datetime, timezone

from data.recipes import (
    RECIPE_DATABASE,
    RECIPE_ALIASES,
    resolve_recipe,
    get_recipe,
    list_recipe_names,
)


async def recipe_autocomplete(
    itxn: discord.Interaction,
    current: str,
) -> List[app_commands.Choice[str]]:
    if not current:
        return [
            app_commands.Choice(name=d["display_name"], value=d["display_name"])
            for d in RECIPE_DATABASE.values()
        ][:25]

    q = current.strip().lower()
    seen: set[str] = set()
    results: list[app_commands.Choice[str]] = []

    for alias, canonical in RECIPE_ALIASES.items():
        if q in alias and canonical not in seen:
            results.append(app_commands.Choice(
                name=RECIPE_DATABASE[canonical]["display_name"],
                value=RECIPE_DATABASE[canonical]["display_name"],
            ))
            seen.add(canonical)

    for canonical, data in RECIPE_DATABASE.items():
        if q in data["display_name"].lower() and canonical not in seen:
            results.append(app_commands.Choice(name=data["display_name"], value=data["display_name"]))
            seen.add(canonical)

    return results[:25]


def _build_recipe_embed(data: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"Recipe — {data['display_name']}",
        description=f"Crafted in: **{data['crafted_in']}**",
        color=discord.Color.random(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  Verify quantities in-game")

    embed.add_field(
        name="🧪  Ingredients",
        value="```" + "\n".join(data["ingredients"]) + "```",
        inline=False,
    )
    embed.add_field(
        name="⚡  Effects",
        value="\n".join(data["effects"]),
        inline=False,
    )
    embed.add_field(
        name="📦  Notes",
        value="\n".join(data["notes"]),
        inline=False,
    )
    return embed


class RecipeCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="recipe",
        description="Crafting ingredients and effects for endgame consumables.",
    )
    @app_commands.describe(item="Consumable to look up (Veggie Cake, Mindwipe, Shadow Steak...)")
    @app_commands.autocomplete(item=recipe_autocomplete)
    async def recipe(self, itxn: discord.Interaction, item: str) -> None:
        canonical = resolve_recipe(item)

        if not canonical:
            q = item.strip().lower()
            for key, data in RECIPE_DATABASE.items():
                if q in data["display_name"].lower():
                    canonical = key
                    break

        if not canonical:
            await itxn.response.send_message(
                f"**[ERROR]** `{item}` not found.\n"
                f"**Supported:** ```{', '.join(list_recipe_names())}```",
                ephemeral=True,
            )
            return

        data = get_recipe(canonical)
        await itxn.response.send_message(embed=_build_recipe_embed(data))

    @recipe.error
    async def recipe_error(self, itxn: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await itxn.response.send_message(f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RecipeCog(bot))
