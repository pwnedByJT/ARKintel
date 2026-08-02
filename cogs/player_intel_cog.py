"""
Cog: cogs/player_intel_cog.py
Description: Player identity tagging and intel lookup system.
             Modelled loosely on Overseer-style player tracking.

IMPORTANT — API limitation (documented):
  The official ASA server list API (cdn2.arkdedicated.com) returns only
  aggregate data (NumPlayers, server name, IP, map). It exposes NO
  per-player data: no names, no platform IDs, no session times.

  A2S (Steam Source Query Protocol) queries were tested against live
  official servers and uniformly timed out — ASA uses Epic Online
  Services (EOS) for session management, which is not publicly queryable
  without EOS developer credentials.

  Therefore, this cog does NOT implement a /playerlist command against
  official servers. The feature set is:

    /tag-player  — manually log a player identity into the DB
    /player-info — look up a tagged player's current record + change history

  If you operate a *community* server with A2S enabled, a2s.players()
  would work against your own IP/port — that is out of scope here.

Author: pwnedByJT
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
from typing import List


# ---------------------------------------------------------------------------
# AUTOCOMPLETE — queries the live DB for /player-info
# ---------------------------------------------------------------------------

async def player_autocomplete(
    itxn: discord.Interaction, current: str
) -> List[app_commands.Choice[str]]:
    cog = itxn.client.get_cog("ARKCog")
    if not cog:
        return []
    results = await cog.db.search_players(current or "", limit=25)
    choices = []
    for r in results:
        tribe  = f"[{r['tribe_tag']}] " if r.get("tribe_tag") else ""
        server = f" — srv {r['main_server']}" if r.get("main_server") else ""
        label  = f"{tribe}{r['display_name']}{server}"[:100]
        choices.append(app_commands.Choice(name=label, value=r["player_id"]))
    return choices


# ---------------------------------------------------------------------------
# EMBED BUILDERS
# ---------------------------------------------------------------------------

def _build_tag_embed(is_new: bool, player_id: str, display_name: str,
                     main_server: str | None, tribe_tag: str | None,
                     custom_note: str | None) -> discord.Embed:
    action = "Tagged" if is_new else "Updated"
    color  = discord.Color(0x57F287) if is_new else discord.Color(0x45B7D1)

    embed = discord.Embed(
        title=f"[PLAYER INTEL]  {action}: {display_name}",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  Player Intel")

    embed.add_field(name="Player ID",   value=f"`{player_id}`",              inline=False)
    embed.add_field(name="Name",        value=f"`{display_name}`",           inline=True)
    embed.add_field(name="Main Server", value=f"`{main_server or 'N/A'}`",   inline=True)
    embed.add_field(name="Tribe",       value=f"`{tribe_tag or 'N/A'}`",     inline=True)
    embed.add_field(name="Note",        value=f"`{custom_note or 'None'}`",  inline=True)
    return embed


def _build_info_embed(player: dict, history: list) -> discord.Embed:
    embed = discord.Embed(
        title=f"[PLAYER INTEL]  {player['display_name']}",
        color=discord.Color.random(),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  Player Intel")

    tribe  = player.get("tribe_tag")   or "N/A"
    server = player.get("main_server") or "N/A"
    note   = player.get("custom_note") or "None"

    embed.add_field(name="Player ID",    value=f"```{player['player_id']}```", inline=False)
    embed.add_field(name="Tribe",        value=f"`{tribe}`",                   inline=True)
    embed.add_field(name="Main Server",  value=f"`{server}`",                  inline=True)
    embed.add_field(name="Note",         value=f"`{note}`",                    inline=True)
    embed.add_field(name="Times Tagged", value=f"`{player['tag_count']}`",     inline=True)
    embed.add_field(name="First Seen",   value=f"`{player['first_tagged_at'][:16]} UTC`", inline=True)
    embed.add_field(name="Last Updated", value=f"`{player['last_updated_at'][:16]} UTC`", inline=True)

    if history:
        lines = []
        for h in history:
            ts    = h["tagged_at"][:16]
            t     = f"[{h['tribe_tag']}] " if h.get("tribe_tag") else ""
            srv   = f"srv {h['main_server']}" if h.get("main_server") else "srv ?"
            lines.append(f"{ts}  {t}{h['display_name']}  {srv}")
        embed.add_field(
            name=f"Tag History (last {len(history)})",
            value="```" + "\n".join(lines) + "```",
            inline=False,
        )
    return embed


def _build_not_found_embed(query: str) -> discord.Embed:
    embed = discord.Embed(
        title="[PLAYER INTEL]  Not Found",
        description=(
            f"No tagged player matches `{query}`.\n\n"
            "Use `/tag-player` to add them to the database."
        ),
        color=discord.Color(0xFEE75C),
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="Designed by pwnedByJT  |  ARKintel  |  Player Intel")
    return embed


# ---------------------------------------------------------------------------
# COG
# ---------------------------------------------------------------------------

class PlayerIntelCog(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @property
    def _db(self):
        cog = self.bot.get_cog("ARKCog")
        return cog.db if cog else None

    # ------------------------------------------------------------------ #
    #  /tag-player                                                         #
    # ------------------------------------------------------------------ #

    @app_commands.command(
        name="tag-player",
        description="Log or update a player identity in the ARKintel database.",
    )
    @app_commands.describe(
        player_id="EOS / Steam / Xbox / PSN ID for this player",
        display_name="In-game display name",
        main_server="Server number they main (e.g. 2018)",
        tribe_tag="Tribe tag or name (e.g. IBTB)",
        note="Optional freeform note (e.g. [JoEgg] / hostile raider)",
    )
    async def tag_player(
        self,
        itxn: discord.Interaction,
        player_id: str,
        display_name: str,
        main_server: str,
        tribe_tag: str,
        note: str = "",
    ) -> None:
        db = self._db
        if not db:
            return await itxn.response.send_message(
                "[ERROR] Intel database not available.", ephemeral=True
            )

        is_new = await db.upsert_player_tag(
            player_id=player_id.strip(),
            display_name=display_name.strip(),
            main_server=main_server.strip() or None,
            tribe_tag=tribe_tag.strip() or None,
            custom_note=note.strip() or None,
            tagged_by=str(itxn.user.id),
        )

        embed = _build_tag_embed(
            is_new, player_id.strip(), display_name.strip(),
            main_server.strip() or None,
            tribe_tag.strip() or None,
            note.strip() or None,
        )
        await itxn.response.send_message(embed=embed)

    # ------------------------------------------------------------------ #
    #  /player-info                                                        #
    # ------------------------------------------------------------------ #

    @app_commands.command(
        name="player-info",
        description="Look up a tagged player's identity record and tagging history.",
    )
    @app_commands.describe(
        query="Player ID (exact) or display name (partial) — supports autocomplete",
    )
    @app_commands.autocomplete(query=player_autocomplete)
    async def player_info(self, itxn: discord.Interaction, query: str) -> None:
        await itxn.response.defer()

        db = self._db
        if not db:
            return await itxn.followup.send(
                "[ERROR] Intel database not available.", ephemeral=True
            )

        # Prefer exact player_id match; fall back to display_name search
        player = await db.get_player(query.strip())
        if not player:
            results = await db.search_players(query.strip(), limit=1)
            if results:
                player = await db.get_player(results[0]["player_id"])

        if not player:
            return await itxn.followup.send(embed=_build_not_found_embed(query))

        history = await db.get_tag_history(player["player_id"], limit=5)
        await itxn.followup.send(embed=_build_info_embed(player, history))

    # ------------------------------------------------------------------ #
    #  Error handlers                                                      #
    # ------------------------------------------------------------------ #

    @tag_player.error
    async def tag_player_error(self, itxn: discord.Interaction, error) -> None:
        await itxn.response.send_message(
            f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True
        )

    @player_info.error
    async def player_info_error(self, itxn: discord.Interaction, error) -> None:
        await itxn.response.send_message(
            f"[ERROR] `{error}` — contact pwnedByJT.", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PlayerIntelCog(bot))
