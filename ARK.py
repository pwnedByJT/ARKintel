"""
Program name: ARK.py
Description: Asynchronous ARK monitoring suite with dynamic box-style HUD dashboards,
             randomized sidebar accents, and full SQL analytics.
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
    FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
    
    FONT_TITLE = os.path.join(BASE_DIR, "assets", "fonts", "Orbitron-Bold.ttf")
    FONT_BODY = os.path.join(BASE_DIR, "assets", "fonts", "RobotoMono-Regular.ttf")
    
    OFFICIAL_API = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_API = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"

# --- CORE UTILITIES ---
async def fetch_json(url: str):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                return await response.json() if response.status == 200 else None
        except: return None

async def server_autocomplete(itxn: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    cog = itxn.client.get_cog("ARKCog")
    cache = cog.cache if cog else []
    return [app_commands.Choice(name=s['Name'], value=s['Name']) 
            for s in cache if current.lower() in s['Name'].lower()][:25]

# --- ENGINES ---
class AnalyticsEngine:
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
    """Restores the 'Box' UI layout with dynamic sidebar color logic."""
    def __init__(self):
        try:
            self.f_hdr = ImageFont.truetype(Config.FONT_TITLE, 22)
            self.f_lbl = ImageFont.truetype(Config.FONT_TITLE, 15)
            self.f_val = ImageFont.truetype(Config.FONT_BODY, 18)
        except:
            self.f_hdr = self.f_lbl = self.f_val = ImageFont.load_default()

    def render_hud(self, data: Dict, rates: str) -> io.BytesIO:
        W, H = 650, 480
        img = Image.new('RGB', (W, H), color=(26, 28, 32))
        draw = ImageDraw.Draw(img)

        # 1. Random Sidebar Color Logic
        sidebar_color = (random.randint(50, 255), random.randint(150, 255), random.randint(50, 255))
        draw.rectangle([(0, 0), (12, H)], fill=sidebar_color)

        # 2. Header
        draw.text((40, 20), "Official Server | Made by pwnedByJT", font=self.f_hdr, fill=(255, 255, 255))

        # 3. Box Rendering Helper
        def draw_box(x, y, w, h, label, value):
            draw.text((x, y), label, font=self.f_lbl, fill=(240, 240, 240))
            # Box background
            draw.rectangle([(x, y+25), (x+w, y+65)], fill=(38, 41, 46))
            # Text inside box
            draw.text((x+12, y+35), str(value), font=self.f_val, fill=(255, 255, 255))

        # Layout mapping exactly to screenshots
        draw_box(40, 65, 570, 40, "Server Name", data.get('Name', 'Unknown'))
        
        draw_box(40, 150, 150, 40, "Players Online", data.get('NumPlayers', 0))
        draw_box(210, 150, 240, 40, "Map", data.get('MapName', 'Unknown'))
        draw_box(470, 150, 140, 40, "Day", data.get('DayTime', 'N/A'))
        
        draw_box(40, 235, 280, 40, "IP", data.get('IP', '0.0.0.0'))
        draw_box(340, 235, 270, 40, "Port", data.get('Port', '7777'))
        
        draw_box(40, 320, 570, 40, "Server Rates", f"{rates}")

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf

# --- COGS ---
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
            try:
                data = json.load(f)
                for k, v in data.items():
                    if "last_vc_update" in v: v["last_vc_update"] = datetime.fromisoformat(v["last_vc_update"])
                return data
            except: return {}

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
                        await msg.edit(attachments=[discord.File(img, filename="status.png")])
                    except: pass

    @tasks.loop(minutes=15)
    async def evo_monitor(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(Config.EVO_API) as r:
                    text = await r.text()
                    rate = next((l.split('=')[1].strip() for l in text.splitlines() if "XPMultiplier" in l), "1.0")
                    self.current_rates = rate
            except: pass

    @app_commands.command(name="monitor", description="Deploy the graphical dashboard")
    @app_commands.autocomplete(server_id=server_autocomplete)
    async def monitor(self, itxn: discord.Interaction, server_id: str):
        await itxn.response.defer()
        node = next((s for s in self.cache if server_id in s['Name']), None)
        if not node: return await itxn.followup.send("Node lookup failed.")
        
        img = self.gfx.render_hud(node, self.current_rates)
        msg = await itxn.followup.send(file=discord.File(img, filename="status.png"))
        
        self.monitors[server_id] = {"message_id": msg.id, "channel_id": itxn.channel_id, "last_vc_update": datetime.now(timezone.utc)}
        with open(Config.MONITORS_FILE, "w") as f:
            json.dump({k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in self.monitors.items()}, f)

class SysAdminCog(commands.Cog):
    @app_commands.command(name="pistats", description="Check Raspberry Pi Hardware Health")
    async def pistats(self, itxn: discord.Interaction):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        latency = round(itxn.client.latency * 1000)
        await itxn.response.send_message(f"CPU: {cpu}% | RAM: {ram}% | PING: {latency}ms")

class MainBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        cog = ARKCog(self)
        await cog.analytics.initialize()
        await self.add_cog(cog)
        await self.add_cog(SysAdminCog())
        await self.tree.sync()
        print("✅ ARK Master System Initialized")

if __name__ == "__main__":
    MainBot().run(os.getenv("DISCORD_TOKEN"))