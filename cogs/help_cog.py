"""
Cog: cogs/help_cog.py
Description: /ark-help slash command — full ARKintel command reference.
Author: pwnedByJT
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone


HELP_SECTIONS = [
    {
        "name": "🦖  Tame Intelligence",
        "value": (
            "```"
            "/tame-stats tame:<name>\n"
            "  Endgame leveling guide — where to dump 88 domestic pts.\n"
            "  Aliases: giga, theri, carcha, daed, paracer, dunk...\n"
            "\n"
            "/imprint creature:<name> time_remaining:<HH:MM> [ping_role:<role>]\n"
            "  Hatch/cuddle timer. Pings at 5-min warning + when window opens.\n"
            "  One active timer per user. Bot restart = timer lost.\n"
            "\n"
            "/imprint-cancel\n"
            "  Cancels your active imprint timer."
            "```"
        ),
    },
    {
        "name": "🧪  Consumables & Crafting",
        "value": (
            "```"
            "/recipe item:<name>\n"
            "  Ingredients, effects, and spoil notes for endgame consumables.\n"
            "  Items: Veggie Cake | Mindwipe | Shadow Steak | Medical Brew\n"
            "         Focal Chili | Battle Tartare"
            "```"
        ),
    },
    {
        "name": "💣  Raid Operations",
        "value": (
            "```"
            "/raid-calc structure:<name> [quantity:<int>]\n"
            "  Exact C4 / RPG / Grenade count + raw material costs to craft.\n"
            "  Structures: Metal Wall | Tek Wall | Vault | Heavy Turret\n"
            "              Tek Generator | Behemoth Gate | and more...\n"
            "  Default quantity: 1. Max: 500."
            "```"
        ),
    },
    {
        "name": "🏺  Boss Preparation",
        "value": (
            "```"
            "/boss-check boss:<name> tier:<Gamma|Beta|Alpha>\n"
            "  Entry checklist: artifacts, apex tributes, army composition,\n"
            "  saddle armor requirements, HP floors, and wipe risks.\n"
            "  Bosses: Dragon | Broodmother | Megapithecus"
            "```"
        ),
    },
    {
        "name": "📡  Server Monitoring",
        "value": (
            "```"
            "/monitor server_number:<name>\n"
            "  Start a live dashboard + voice counter for a server.\n"
            "  Auto-updates every 60 seconds.\n"
            "\n"
            "/serverpop server_number:<name>\n"
            "  One-time server snapshot (no persistent monitoring).\n"
            "\n"
            "/stopmonitor server_number:<name>\n"
            "  Stop tracking a server and remove its voice counter.\n"
            "\n"
            "/serverstats server_number:<name> [hours:<int>]\n"
            "  Historical population analytics. Default: last 24 hours.\n"
            "\n"
            "/popgraph server_number:<name> [hours:<int>]\n"
            "  Visual population chart as an image. Same window as serverstats.\n"
            "  Requires at least 2 recorded data points (run /monitor first).\n"
            "\n"
            "/popwatch server_number:<name> threshold:<int>\n"
            "  Get pinged when a server's population drops below your threshold.\n"
            "  Checks every 60s. Re-arms automatically when pop recovers.\n"
            "\n"
            "/popwatch_remove server_number:<name>\n"
            "  Cancel a population alert you previously set."
            "```"
        ),
    },
    {
        "name": "🕵️  Player Intel",
        "value": (
            "```"
            "/tag-player player_id:<id> display_name:<name> main_server:<srv> tribe_tag:<tag> [note:<text>]\n"
            "  Log or update a player identity. Accepts any platform ID\n"
            "  (EOS / Steam / Xbox / PSN) entered manually.\n"
            "  Every update is appended to the player's change history.\n"
            "\n"
            "/player-info query:<id_or_name>\n"
            "  Look up a tagged player's current record and full tag history.\n"
            "  Supports autocomplete — start typing name or ID."
            "```"
        ),
    },
    {
        "name": "🎯  Raid Intel",
        "value": (
            "```"
            "/raidwindow [min_avg:<int>]\n"
            "  Scan monitored servers for low-population windows over the past 7 days.\n"
            "  Qualifies servers with weekly avg pop > min_avg (default: 3).\n"
            "  Reports: weekly avg, quietest UTC/PT hour, avg pop during that window.\n"
            "  Note: only servers tracked via /monitor have population history."
            "```"
        ),
    },
    {
        "name": "🖥️  Infrastructure",
        "value": (
            "```"
            "/cluster-status\n"
            "  Live K3s Pod health: name, namespace, status, restarts,\n"
            "  uptime, cluster IP, node, and memory/CPU limits.\n"
            "  Requires RBAC setup — see k8s/rbac.yaml in the repo."
            "```"
        ),
    },
    {
        "name": "⭐  Favorites & Utilities",
        "value": (
            "```"
            "/fav_add server_number:<name>    Add a server to your favorites list.\n"
            "/fav_list                        View all saved favorites with live status.\n"
            "/fav_remove server_number:<name> Remove a server from your favorites.\n"
            "\n"
            "/console\n"
            "  Copy-paste console optimization command string for ASA.\n"
            "  Drops shadows, foliage, fog, bloom — max competitive visibility."
            "```"
        ),
    },
]


class HelpCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="ark-help",
        description="Full ARKintel command reference — all commands, parameters, and usage.",
    )
    async def ark_help(self, itxn: discord.Interaction) -> None:
        embed = discord.Embed(
            title="ARKintel — Command Reference",
            description=(
                "Alpha-tier PvP & PvE intelligence suite for ARK: Survival Ascended.\n"
                "All commands support autocomplete — start typing to see options."
            ),
            color=discord.Color.random(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  github.com/pwnedByJT/ARKintel")

        for section in HELP_SECTIONS:
            embed.add_field(name=section["name"], value=section["value"], inline=False)

        await itxn.response.send_message(embed=embed)

    @ark_help.error
    async def ark_help_error(self, itxn: discord.Interaction, error: app_commands.AppCommandError) -> None:
        await itxn.response.send_message(f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
