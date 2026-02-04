"""
Program name: ARK.py
Description: Professional ARK monitoring suite with restored classic box HUDs,
             dynamic sidebar generation, and high-performance async management.
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

# Initialize environment configuration
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
    
    # Assets
    FONT_TITLE = os.path.join(BASE_DIR, "assets", "fonts", "Orbitron-Bold.ttf")
    FONT_BODY = os.path.join(BASE_DIR, "assets", "fonts", "RobotoMono-Regular.ttf")
    
    # API Endpoints
    OFFICIAL_API = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_API = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"

class AnalyticsEngine:
    """Manages asynchronous SQLite operations for historical analytics."""
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

class GraphicsEngine:
    """Renders the classic box-style HUD with no background artifacts."""
    def __init__(self):
        try:
            self.f_hdr = ImageFont.truetype(Config.FONT_TITLE, 22)
            self.f_lbl = ImageFont.truetype(Config.FONT_TITLE, 15)
            self.f_val = ImageFont.truetype(Config.FONT_BODY, 18)
        except:
            self.f_hdr = self.f_lbl = self.f_val = ImageFont.load_default()

    def generate_dashboard(self, data: Dict, rates: str) -> io.BytesIO:
        # Strict Classic Dimensions: 650x480 for better copy-paste contrast
        width, height = 650, 480
        img = Image.new('RGB', (width, height), color=(26, 28, 32))
        draw = ImageDraw.Draw(img)

        # Dynamic Sidebar - Assigns random accent per render
        sidebar_color = (random.randint(50, 255), random.randint(100, 255), random.randint(50, 255))
        draw.rectangle([(0, 0), (12, height)], fill=sidebar_color)

        # Title Label
        draw.text((40, 20), "OFFICIAL SERVER STATUS | AUTH: PWNEDBYJT", font=self.f_hdr, fill=(255, 255, 255))

        def draw_field(x, y, w, h, label, value):
            """Renders solid background boxes for high contrast."""
            draw.text((x, y), label.upper(), font=self.f_lbl, fill=(200, 200, 200))
            # The 'Classic Box' background - No grid lines allowed here
            draw.rectangle([(x, y+25), (x+w, y+65)], fill=(38, 41, 46))
            # Center-aligned data text
            draw.text((x+12, y+35), str(value), font=self.f_val, fill=(255, 255, 255))

        # Field Layout Mapping
        draw_field(40, 65, 570, 40, "Server Name", data.get('Name', 'Unknown'))
        draw_field(40, 150, 150, 40, "Active Users", f"{data.get('NumPlayers', 0)} / {data.get('MaxPlayers', 70)}")
        draw_field(210, 150, 240, 40, "Map Node", data.get('MapName', 'Unknown'))
        draw_field(470, 150, 140, 40, "Time Cycle", data.get('DayTime', 'N/A'))
        draw_field(40, 235, 280, 40, "Network IP", data.get('IP', '0.0.0.0'))
        draw_field(340, 235, 270, 40, "Port Address", data.get('Port', '7777'))
        draw_field(40, 320, 570, 40, "Global Multiplier", f"{rates}x EFFECTIVE")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

# --- AUTOCOMPLETE UTILITY ---
async def server_autocomplete(itxn: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    cog = itxn.client.get_cog("ARKCog")
    cache = cog.cache if cog else []
    return [app_commands.Choice(name=s['Name'], value=s['Name']) 
            for s in cache if current.lower() in s['Name'].lower()][:25]

class ARKCog(commands.Cog):
    """Primary logic controller for the Discord monitoring gateway."""
    def __init__(self, bot):
        self.bot = bot
        self.analytics = AnalyticsEngine(Config.STATS_DB)
        self.gfx = GraphicsEngine()
        self.cache = []
        self.current_rates = "1.0"
        self.monitors = self._load_persistence()
        
        self.sync_api_cache.start()
        self.refresh_active_monitors.start()
        self.monitor_system_rates.start()

    def _load_persistence(self):
        if not os.path.exists(Config.MONITORS_FILE): return {}
        with open(Config.MONITORS_FILE, "r") as f:
            try:
                data = json.load(f)
                for k, v in data.items():
                    if "last_vc_update" in v: v["last_vc_update"] = datetime.fromisoformat(v["last_vc_update"])
                return data
            except: return {}

    @tasks.loop(seconds=60)
    async def sync_api_cache(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(Config.OFFICIAL_API, timeout=10) as r:
                    if r.status == 200: self.cache = await r.json()
            except: pass

    @tasks.loop(seconds=60)
    async def refresh_active_monitors(self):
        if not self.monitors or not self.cache: return
        for srv_id, meta in list(self.monitors.items()):
            node = next((s for s in self.cache if srv_id in s.get("Name", "")), None)
            if node:
                await self.analytics.record_metric(srv_id, node.get('NumPlayers', 0), node.get('MaxPlayers', 70))
                channel = self.bot.get_channel(meta["channel_id"])
                if channel:
                    img = self.gfx.generate_dashboard(node, self.current_rates)
                    try:
                        msg = await channel.fetch_message(meta["message_id"])
                        await msg.edit(attachments=[discord.File(img, filename="status.png")])
                    except: pass

    @tasks.loop(minutes=15)
    async def monitor_system_rates(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(Config.EVO_API) as r:
                    text = await r.text()
                    self.current_rates = next((l.split('=')[1].strip() for l in text.splitlines() if "XPMultiplier" in l), "1.0")
            except: pass

    @app_commands.command(name="monitor", description="Deploy a graphical live status terminal")
    @app_commands.autocomplete(server_id=server_autocomplete)
    async def monitor(self, itxn: discord.Interaction, server_id: str):
        await itxn.response.defer()
        node = next((s for s in self.cache if server_id in s['Name']), None)
        if not node: return await itxn.followup.send("Target node lookup failed.")
        
        img = self.gfx.generate_dashboard(node, self.current_rates)
        msg = await itxn.followup.send(file=discord.File(img, filename="status.png"))
        
        self.monitors[server_id] = {"message_id": msg.id, "channel_id": itxn.channel_id, "last_vc_update": datetime.now(timezone.utc)}
        with open(Config.MONITORS_FILE, "w") as f:
            json.dump({k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in self.monitors.items()}, f, indent=4)

class SystemCog(commands.Cog):
    """Monitors host hardware performance metrics."""
    @app_commands.command(name="diagnostics", description="Perform hardware integrity check")
    async def diagnostics(self, itxn: discord.Interaction):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        latency = round(itxn.client.latency * 1000)
        await itxn.response.send_message(f"SYSTEM_CPU: {cpu}% | SYSTEM_RAM: {ram}% | LATENCY: {latency}ms")

class Application(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        cog = ARKCog(self)
        await cog.analytics.initialize()
        await self.add_cog(cog)
        await self.add_cog(SystemCog())
        await self.tree.sync()
        print("Initialization sequence complete. Operational modules verified.")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        Application().run(token)