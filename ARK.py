"""
Program name: ARK.py
Description: Enterprise-grade ARK monitoring suite with classic box-style 
             HUD dashboards, random accent colors, and async data persistence.
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
import random
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Initialize environment
load_dotenv()

class Config:
    """Centralized management for system constants and directory paths."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TARGET_CHANNEL_ID = 1178760002186526780
    ARK_ROLE_ID = 1364705580064706600
    
    # Persistence
    MONITORS_FILE = os.path.join(BASE_DIR, "monitors.json")
    STATS_DB = os.path.join(BASE_DIR, "server_stats.db")
    FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
    
    # Visuals
    FONT_TITLE = os.path.join(BASE_DIR, "assets", "fonts", "Orbitron-Bold.ttf")
    FONT_BODY = os.path.join(BASE_DIR, "assets", "fonts", "RobotoMono-Regular.ttf")
    
    # Official API Endpoints
    OFFICIAL_API = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_API = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"

class AnalyticsEngine:
    """Manages asynchronous SQLite operations for historical player data."""
    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS server_stats 
                                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                                server_name TEXT, player_count INTEGER, 
                                max_players INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            await db.commit()

    async def record_metric(self, name: str, current: int, limit: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO server_stats (server_name, player_count, max_players) VALUES (?, ?, ?)",
                             (name, current, limit))
            await db.commit()

    async def get_historical_stats(self, name: str, hours: int = 24) -> Dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            async with db.execute("SELECT player_count FROM server_stats WHERE server_name = ? AND timestamp > ?", (name, cutoff)) as cursor:
                rows = await cursor.fetchall()
                if not rows: return {"error": "Insufficient data"}
                counts = [r['player_count'] for r in rows]
                return {"current": counts[-1], "avg": round(sum(counts)/len(counts), 1), "peak": max(counts), "low": min(counts), "points": len(counts)}

class GraphicsEngine:
    """Restores the Classic Box GUI with dynamic color accents."""
    def __init__(self):
        try:
            self.f_hdr = ImageFont.truetype(Config.FONT_TITLE, 22)
            self.f_lbl = ImageFont.truetype(Config.FONT_TITLE, 15)
            self.f_val = ImageFont.truetype(Config.FONT_BODY, 18)
        except:
            self.f_hdr = self.f_lbl = self.f_val = ImageFont.load_default()

    def generate_dashboard(self, data: Dict, rates: str) -> io.BytesIO:
        # Strict Classic Dimensions: 650x480
        W, H = 650, 480
        img = Image.new('RGB', (W, H), color=(35, 38, 42))
        draw = ImageDraw.Draw(img)

        # Dynamic Sidebar - Generates random accent per render
        accent = (random.randint(50, 255), random.randint(100, 255), random.randint(50, 255))
        draw.rectangle([(0, 0), (12, H)], fill=accent)

        # Header - Professional technical labeling
        draw.text((40, 25), "OFFICIAL SERVER STATUS | AUTH: PWNEDBYJT", font=self.f_hdr, fill=(255, 255, 255))

        def draw_box(x, y, w, h, label, value):
            draw.text((x, y), label.upper(), font=self.f_lbl, fill=(200, 200, 200))
            draw.rectangle([(x, y+25), (x+w, y+65)], fill=(28, 31, 35)) # High-contrast box
            draw.text((x+12, y+35), str(value), font=self.f_val, fill=(255, 255, 255))

        # Field Mapping
        draw_box(40, 75, 570, 40, "Server Identifier", data.get('Name', 'Unknown'))
        draw_box(40, 160, 150, 40, "Online", f"{data.get('NumPlayers', 0)} / {data.get('MaxPlayers', 70)}")
        draw_box(210, 160, 240, 40, "Map Node", data.get('MapName', 'Unknown'))
        draw_box(470, 160, 140, 40, "Time Cycle", data.get('DayTime', 'N/A'))
        draw_box(40, 245, 280, 40, "Network IP", data.get('IP', '0.0.0.0'))
        draw_box(340, 245, 270, 40, "Port Address", data.get('Port', '7777'))
        draw_box(40, 330, 570, 40, "Effective Multiplier", f"{rates}x")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

# --- AUTOCOMPLETE UTILITY ---
async def server_autocomplete(itxn: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    cog = itxn.client.get_cog("ARKCog")
    cache = cog.cache if cog else []
    return [app_commands.Choice(name=s['Name'], value=s['Name']) 
            for s in cache if current.lower() in s['Name'].lower()][:25]

class ARKCog(commands.Cog):
    """Primary logic controller for server monitoring and user favorites."""
    def __init__(self, bot):
        self.bot = bot
        self.analytics = AnalyticsEngine(Config.STATS_DB)
        self.gfx = GraphicsEngine()
        self.cache = []
        self.current_rates = "1.0"
        self.last_known_rates = None
        self.monitors = self._load_json(Config.MONITORS_FILE)
        
        self.sync_api.start()
        self.refresh_monitors.start()
        self.evo_check.start()

    def _load_json(self, path):
        if not os.path.exists(path): return {}
        with open(path, "r") as f:
            try:
                data = json.load(f)
                for k, v in data.items():
                    if "last_vc_update" in v: v["last_vc_update"] = datetime.fromisoformat(v["last_vc_update"])
                return data
            except: return {}

    @tasks.loop(seconds=60)
    async def sync_api(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.OFFICIAL_API) as r:
                if r.status == 200: self.cache = await r.json()

    @tasks.loop(seconds=60)
    async def refresh_monitors(self):
        if not self.monitors or not self.cache: return
        for srv_id, meta in list(self.monitors.items()):
            node = next((s for s in self.cache if srv_id in s.get("Name", "")), None)
            if node:
                await self.analytics.record_metric(srv_id, node.get('NumPlayers', 0), node.get('MaxPlayers', 70))
                chan = self.bot.get_channel(meta["channel_id"])
                if chan:
                    img = self.gfx.generate_dashboard(node, self.current_rates)
                    try:
                        msg = await chan.fetch_message(meta["message_id"])
                        await msg.edit(attachments=[discord.File(img, filename="status.png")])
                    except: pass

    @tasks.loop(minutes=10)
    async def evo_check(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.EVO_API) as r:
                text = await r.text()
                rate = next((l.split('=')[1].strip() for l in text.splitlines() if "XPMultiplier" in l), "1.0")
                self.current_rates = rate
                if self.last_known_rates and rate != self.last_known_rates:
                    chan = self.bot.get_channel(Config.TARGET_CHANNEL_ID)
                    if chan: await chan.send(f"SYSTEM ADVISORY: GLOBAL MULTIPLIER UPDATED TO {rate}x")
                self.last_known_rates = rate

    @app_commands.command(name="monitor", description="Deploy a graphical live dashboard")
    @app_commands.autocomplete(server_id=server_autocomplete)
    async def monitor(self, itxn: discord.Interaction, server_id: str):
        await itxn.response.defer()
        node = next((s for s in self.cache if server_id in s['Name']), None)
        if not node: return await itxn.followup.send("ERROR: Node not identified.")
        img = self.gfx.generate_dashboard(node, self.current_rates)
        msg = await itxn.followup.send(file=discord.File(img, filename="status.png"))
        self.monitors[server_id] = {"message_id": msg.id, "channel_id": itxn.channel_id, "last_vc_update": datetime.now(timezone.utc)}
        with open(Config.MONITORS_FILE, "w") as f:
            json.dump({k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in self.monitors.items()}, f)

class SystemCog(commands.Cog):
    """Monitors host hardware health."""
    @app_commands.command(name="diagnostics", description="Hardware integrity check")
    async def diagnostics(self, itxn: discord.Interaction):
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
        latency = round(itxn.client.latency * 1000)
        await itxn.response.send_message(f"CPU_LOAD: {cpu}% | RAM_UTIL: {ram}% | NET_LATENCY: {latency}ms")

class Application(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        cog = ARKCog(self)
        await cog.analytics.initialize()
        await self.add_cog(cog)
        await self.add_cog(SystemCog())
        await self.tree.sync()
        print("SYSTEM INITIALIZATION COMPLETE: OPERATIONAL.")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token: Application().run(token)