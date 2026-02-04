"""
Program name: ARK.py
Description: Enterprise-grade ARK monitoring suite.
             Features: Text-based Embed Dashboards, Voice Counters, Favorites, 
             SQL Analytics, and Auto-EVO Alerts.
             Architecture: Async/OOP (Non-blocking)
             Standards: Strict No-Emote Policy
Author: Justin Aaron Turner
Updated: February 3, 2026
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import aiosqlite
import os
import json
import random
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TARGET_CHANNEL_ID = 1178760002186526780
    ARK_ROLE_ID = 1364705580064706600
    MONITORS_FILE = os.path.join(BASE_DIR, "monitors.json")
    STATS_DB = os.path.join(BASE_DIR, "server_stats.db")
    FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
    
    OFFICIAL_API = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_API = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"
    ALERT_THRESHOLD = 8

# --- DATABASE ENGINE ---
class DatabaseEngine:
    def __init__(self, db_path):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS server_stats 
                                (id INTEGER PRIMARY KEY AUTOINCREMENT, server_name TEXT, 
                                player_count INTEGER, max_players INTEGER, 
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_server_time ON server_stats(server_name, timestamp)')
            await db.commit()

    async def record_stats(self, name: str, current: int, limit: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO server_stats (server_name, player_count, max_players) VALUES (?, ?, ?)",
                             (name, current, limit))
            await db.commit()

    async def get_stats(self, name: str, hours: int = 24):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            async with db.execute("SELECT player_count FROM server_stats WHERE server_name = ? AND timestamp > ? ORDER BY timestamp", (name, cutoff)) as cursor:
                rows = await cursor.fetchall()
                if not rows: return None
                counts = [r['player_count'] for r in rows]
                return {
                    "current": counts[-1], "avg": round(sum(counts)/len(counts), 1),
                    "peak": max(counts), "low": min(counts), "samples": len(counts)
                }

# --- UI UTILITIES ---
class EmbedFactory:
    @staticmethod
    def create_monitor(data: Dict, rates: str = "1.0") -> discord.Embed:
        # Status Color Logic (Green for low pop, Red for high pop)
        pop = data.get('NumPlayers', 0)
        color = discord.Color.green() if pop < 40 else (discord.Color.gold() if pop < 65 else discord.Color.red())
        
        status_text = "[ONLINE]" if pop < 70 else "[FULL]"
        
        embed = discord.Embed(title=f"{status_text} {data.get('Name')}", color=color)
        embed.set_footer(text=f"UPDATED: {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
        
        # Professional Code Blocks for Copy-Paste
        embed.add_field(name="Server Name", value=f"```{data.get('Name')}```", inline=False)
        embed.add_field(name="Player Count", value=f"```{pop}/{data.get('MaxPlayers', 70)}```", inline=True)
        embed.add_field(name="Map Name", value=f"```{data.get('MapName')}```", inline=True)
        embed.add_field(name="Day Cycle", value=f"```{data.get('DayTime')}```", inline=True)
        embed.add_field(name="IP Address", value=f"```{data.get('IP')}```", inline=True)
        embed.add_field(name="Port", value=f"```{data.get('Port')}```", inline=True)
        embed.add_field(name="EVO Multiplier", value=f"```{rates}x```", inline=False)
        
        return embed

async def server_autocomplete(itxn: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    cog = itxn.client.get_cog("ARKCog")
    cache = cog.cache if cog else []
    return [app_commands.Choice(name=s['Name'], value=s['Name']) 
            for s in cache if current.lower() in s['Name'].lower()][:25]

# --- MAIN LOGIC ---
class ARKCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseEngine(Config.STATS_DB)
        self.cache = []
        self.monitors = self._load_json(Config.MONITORS_FILE)
        self.favorites = self._load_json(Config.FAVORITES_FILE)
        self.current_rates = "1.0"
        self.last_rates = None
        
        self.sync_cache.start()
        self.update_monitors.start()
        self.check_evo.start()

    def _load_json(self, path):
        if not os.path.exists(path): return {}
        try:
            with open(path, 'r') as f: return json.load(f)
        except: return {}

    def _save_json(self, path, data):
        with open(path, 'w') as f: json.dump(data, f, indent=4)

    @tasks.loop(seconds=60)
    async def sync_cache(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(Config.OFFICIAL_API, timeout=10) as r:
                    if r.status == 200: self.cache = await r.json()
            except: pass

    @tasks.loop(seconds=60)
    async def update_monitors(self):
        if not self.monitors or not self.cache: return
        
        for srv_id, meta in list(self.monitors.items()):
            node = next((s for s in self.cache if srv_id in s.get("Name", "")), None)
            if node:
                # 1. Update Database
                await self.db.record_stats(srv_id, node.get('NumPlayers'), node.get('MaxPlayers'))
                
                # 2. Update Embed
                chan = self.bot.get_channel(meta["channel_id"])
                if chan:
                    embed = EmbedFactory.create_monitor(node, self.current_rates)
                    try:
                        msg = await chan.fetch_message(meta["message_id"])
                        await msg.edit(embed=embed)
                    except: pass
                    
                    # 3. Update Voice Channel
                    vc_id = meta.get("vc_id")
                    if vc_id:
                        vc = self.bot.get_channel(vc_id)
                        if vc:
                            new_name = f"VC {srv_id}: {node.get('NumPlayers')}/{node.get('MaxPlayers')}"
                            if vc.name != new_name:
                                try: await vc.edit(name=new_name)
                                except: pass

    @tasks.loop(minutes=10)
    async def check_evo(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(Config.EVO_API) as r:
                    txt = await r.text()
                    rate = next((l.split('=')[1].strip() for l in txt.splitlines() if "XPMultiplier" in l), "1.0")
                    self.current_rates = rate
                    
                    if self.last_rates and rate != self.last_rates:
                        chan = self.bot.get_channel(Config.TARGET_CHANNEL_ID)
                        if chan: await chan.send(f"**EVO ALERT**: Rates changed to **{rate}x**!")
                    self.last_rates = rate
            except: pass

    # --- COMMANDS ---

    @app_commands.command(name="monitor", description="Start a live dashboard and voice counter")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def monitor(self, itxn: discord.Interaction, server_number: str):
        await itxn.response.defer()
        
        node = next((s for s in self.cache if server_number in s['Name']), None)
        if not node: return await itxn.followup.send("Server not found in API cache.")

        # Create Embed
        embed = EmbedFactory.create_monitor(node, self.current_rates)
        msg = await itxn.followup.send(embed=embed)
        
        # Create Voice Channel
        vc_id = None
        if itxn.guild:
            cat = discord.utils.get(itxn.guild.categories, name="[ Ark ]") or itxn.channel.category
            try:
                vc = await itxn.guild.create_voice_channel(
                    name=f"VC {server_number}: {node.get('NumPlayers')}/70", 
                    category=cat
                )
                vc_id = vc.id
            except: await itxn.followup.send("Failed to create Voice Channel (Check permissions).", ephemeral=True)

        self.monitors[server_number] = {"message_id": msg.id, "channel_id": itxn.channel_id, "vc_id": vc_id}
        self._save_json(Config.MONITORS_FILE, self.monitors)

    @app_commands.command(name="stopmonitor", description="Stop tracking a server")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def stopmonitor(self, itxn: discord.Interaction, server_number: str):
        if server_number in self.monitors:
            data = self.monitors.pop(server_number)
            self._save_json(Config.MONITORS_FILE, self.monitors)
            
            # Cleanup
            try: 
                if data.get("vc_id"): await self.bot.get_channel(data["vc_id"]).delete()
                await (await self.bot.get_channel(data["channel_id"]).fetch_message(data["message_id"])).delete()
            except: pass
            
            await itxn.response.send_message(f"Stopped monitoring **{server_number}**.")
        else:
            await itxn.response.send_message("Server is not being monitored.", ephemeral=True)

    @app_commands.command(name="fav_add", description="Add server to favorites")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def fav_add(self, itxn: discord.Interaction, server_number: str):
        uid = str(itxn.user.id)
        if uid not in self.favorites: self.favorites[uid] = []
        if server_number not in self.favorites[uid]:
            self.favorites[uid].append(server_number)
            self._save_json(Config.FAVORITES_FILE, self.favorites)
            await itxn.response.send_message(f"Added **{server_number}** to favorites.")
        else:
            await itxn.response.send_message("Server is already in favorites.", ephemeral=True)

    @app_commands.command(name="fav_list", description="View your favorites")
    async def fav_list(self, itxn: discord.Interaction):
        uid = str(itxn.user.id)
        if uid not in self.favorites or not self.favorites[uid]:
            return await itxn.response.send_message("You have no favorites.", ephemeral=True)
        
        embed = discord.Embed(title=f"{itxn.user.name}'s Favorites", color=discord.Color.gold())
        for srv in self.favorites[uid]:
            node = next((s for s in self.cache if srv in s['Name']), None)
            status = f"[ONLINE] {node.get('NumPlayers')}/70" if node else "[OFFLINE]"
            embed.add_field(name=srv, value=status, inline=False)
        await itxn.response.send_message(embed=embed)

    @app_commands.command(name="serverstats", description="View historical analytics")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def serverstats(self, itxn: discord.Interaction, server_number: str, hours: int = 24):
        await itxn.response.defer()
        stats = await self.db.get_stats(server_number, hours)
        if not stats: return await itxn.followup.send("No data recorded yet. Monitor the server first.")
        
        embed = discord.Embed(title=f"Analytics: {server_number}", color=discord.Color.blue())
        embed.add_field(name="Current", value=f"`{stats['current']}`", inline=True)
        embed.add_field(name="Average", value=f"`{stats['avg']}`", inline=True)
        embed.add_field(name="Peak", value=f"`{stats['peak']}`", inline=True)
        embed.add_field(name="Samples", value=f"`{stats['samples']}`", inline=True)
        await itxn.followup.send(embed=embed)

class Bot(commands.Bot):
    def __init__(self): super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        cog = ARKCog(self)
        await cog.db.initialize()
        await self.add_cog(cog)
        await self.tree.sync()
        print("System Online | No-Emote Mode")

if __name__ == "__main__":
    Bot().run(os.getenv("DISCORD_TOKEN"))