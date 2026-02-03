"""
Program name: ARK.py
Description: Asynchronous, HUD-driven ARK monitoring suite with non-blocking 
             I/O, database pruning, and network latency diagnostics.
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
import io
import psutil
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TARGET_CHANNEL_ID = 1178760002186526780
    ARK_ROLE_ID = 1364705580064706600
    MONITORS_FILE = os.path.join(BASE_DIR, "monitors.json")
    STATS_DB = os.path.join(BASE_DIR, "server_stats.db")
    
    # Pre-loading paths for Font Cache
    FONT_TITLE = os.path.join(BASE_DIR, "assets", "fonts", "Orbitron-Bold.ttf")
    FONT_BODY = os.path.join(BASE_DIR, "assets", "fonts", "RobotoMono-Regular.ttf")
    
    # Official Endpoints
    OFFICIAL_API = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_API = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"

# --- UTILITIES ---
async def fetch_json(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as response:
            return await response.json() if response.status == 200 else None

async def server_autocomplete(itxn: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    cog = itxn.client.get_cog("ARKCog")
    cache = cog.cache if cog else []
    return [app_commands.Choice(name=s['Name'], value=s['Name']) 
            for s in cache if current.lower() in s['Name'].lower()][:25]

# --- CORE ENGINES ---
class AnalyticsEngine:
    """Non-blocking SQLite manager for high-frequency metrics."""
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS server_stats 
                                (id INTEGER PRIMARY KEY AUTOINCREMENT, server_name TEXT, 
                                player_count INTEGER, max_players INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            await db.commit()

    async def record_metric(self, name: str, current: int, limit: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO server_stats (server_name, player_count, max_players) VALUES (?, ?, ?)",
                             (name, current, limit))
            await db.commit()

class GraphicsEngine:
    """Pre-cached font rendering engine for CPU efficiency."""
    def __init__(self):
        try:
            self.f_hdr = ImageFont.truetype(Config.FONT_TITLE, 24)
            self.f_val = ImageFont.truetype(Config.FONT_BODY, 18)
        except:
            self.f_hdr = self.f_val = ImageFont.load_default()

    def render_hud(self, data: Dict, rates: str) -> io.BytesIO:
        W, H = 650, 400
        curr, mx = data.get('NumPlayers', 0), data.get('MaxPlayers', 70)
        img = Image.new('RGB', (W, H), color=(18, 20, 25))
        draw = ImageDraw.Draw(img)

        # Tactical Blueprint Grid
        for i in range(0, W, 40): draw.line([(i, 0), (i, H)], fill=(25, 30, 40), width=1)
        for i in range(0, H, 40): draw.line([(0, i), (W, i)], fill=(25, 30, 40), width=1)
        
        # Border Accents
        draw.rectangle([(0, 0), (W, 5)], fill=(50, 220, 150))
        
        # Data Layout
        draw.text((30, 30), f"NODE: {data.get('Name')}", font=self.f_hdr, fill=(255, 255, 255))
        draw.text((30, 100), f"POPULATION: {curr}/{mx}", font=self.f_val, fill=(50, 220, 150))
        draw.text((30, 140), f"MAP_ZONE: {data.get('MapName')}", font=self.f_val, fill=(200, 200, 200))
        draw.text((30, 180), f"EVO_RATE: {rates}x", font=self.f_val, fill=(200, 200, 200))
        
        # Latency/Integrity Branding
        draw.text((W-200, H-40), "INTEGRITY: SECURE", font=self.f_val, fill=(40, 40, 45))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

# --- DISCORD CONTROLLERS ---
class ARKCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.analytics = AnalyticsEngine(Config.STATS_DB)
        self.gfx = GraphicsEngine()
        self.cache = []
        self.current_rates = "1.0"
        self.monitors = self._load_json()
        
        self.sync_cache.start()
        self.background_refresh.start()
        self.evo_monitor.start()

    def _load_json(self):
        if not os.path.exists(Config.MONITORS_FILE): return {}
        with open(Config.MONITORS_FILE, "r") as f:
            data = json.load(f)
            for k, v in data.items():
                if "last_vc_update" in v: v["last_vc_update"] = datetime.fromisoformat(v["last_vc_update"])
            return data

    @tasks.loop(seconds=60)
    async def sync_cache(self):
        data = await fetch_json(Config.OFFICIAL_API)
        if data: self.cache = data

    @tasks.loop(seconds=60)
    async def background_refresh(self):
        if not self.monitors or not self.cache: return
        for srv_id, meta in list(self.monitors.items()):
            node = next((s for s in self.cache if srv_id in s.get("Name", "")), None)
            if node:
                await self.analytics.record_metric(srv_id, node.get('NumPlayers', 0), node.get('MaxPlayers', 70))
                channel = self.bot.get_channel(meta["channel_id"])
                if channel:
                    img = self.gfx.render_hud(node, self.current_rates)
                    try:
                        msg = await channel.fetch_message(meta["message_id"])
                        await msg.edit(attachments=[discord.File(img, filename="hud.png")])
                    except: pass

    @tasks.loop(minutes=15)
    async def evo_monitor(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.EVO_API) as r:
                text = await r.text()
                rate = next((l.split('=')[1].strip() for l in text.splitlines() if "XPMultiplier" in l), "1.0")
                self.current_rates = rate

    @app_commands.command(name="monitor")
    @app_commands.autocomplete(server_id=server_autocomplete)
    async def monitor(self, itxn: discord.Interaction, server_id: str):
        await itxn.response.defer()
        node = next((s for s in self.cache if server_id in s['Name']), None)
        if not node: return await itxn.followup.send("Node failure: ID not found.")
        
        img = self.gfx.render_hud(node, self.current_rates)
        msg = await itxn.followup.send(file=discord.File(img, filename="hud.png"))
        
        self.monitors[server_id] = {"message_id": msg.id, "channel_id": itxn.channel_id, "last_vc_update": datetime.now(timezone.utc)}
        with open(Config.MONITORS_FILE, "w") as f:
            json.dump({k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in self.monitors.items()}, f)

class SysAdminCog(commands.Cog):
    @app_commands.command(name="diagnostics", description="Network and Hardware telemetry")
    async def diagnostics(self, itxn: discord.Interaction):
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Logic for Discord Latency
        latency = round(itxn.client.latency * 1000)
        
        embed = discord.Embed(title="SYSTEM TELEMETRY", color=0x3498db)
        embed.add_field(name="CPU LOAD", value=f"{cpu}%", inline=True)
        embed.add_field(name="RAM UTIL", value=f"{ram.percent}%", inline=True)
        embed.add_field(name="DISK FREE", value=f"{disk.free // (2**30)} GB", inline=True)
        embed.add_field(name="NET LATENCY", value=f"{latency}ms", inline=True)
        await itxn.response.send_message(embed=embed)

    @app_commands.command(name="purge_stats", description="Prune old database records (SysAdmin Utility)")
    @app_commands.checks.has_permissions(administrator=True)
    async def purge_stats(self, itxn: discord.Interaction, days: int = 7):
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        async with aiosqlite.connect(Config.STATS_DB) as db:
            await db.execute("DELETE FROM server_stats WHERE timestamp < ?", (cutoff,))
            await db.commit()
        await itxn.response.send_message(f"Integrity check: Pruned records older than {days} days.")

class MainBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        # Async initialization for Database
        cog = ARKCog(self)
        await cog.analytics.initialize()
        await self.add_cog(cog)
        await self.add_cog(SysAdminCog())
        await self.tree.sync()
        print("✅ Enterprise HUD System Online")

if __name__ == "__main__":
    MainBot().run(os.getenv("DISCORD_TOKEN"))