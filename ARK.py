"""
Program name: ARK.py
Description: Professional ARK monitoring suite with high-fidelity HUD dashboards,
             analytical tracking, and system health metrics.
Author: Justin Aaron Turner
Updated: February 3, 2026
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
import os
import json
import sqlite3
import io
import psutil
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Load local environment configuration
load_dotenv()

class Config:
    """System-wide configuration and path management."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TARGET_CHANNEL_ID = 1178760002186526780
    ARK_ROLE_ID = 1364705580064706600
    FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
    MONITORS_FILE = os.path.join(BASE_DIR, "monitors.json")
    STATS_DB = os.path.join(BASE_DIR, "server_stats.db")
    FONT_TITLE = os.path.join(BASE_DIR, "assets", "fonts", "Orbitron-Bold.ttf")
    FONT_BODY = os.path.join(BASE_DIR, "assets", "fonts", "RobotoMono-Regular.ttf")
    OFFICIAL_API = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_API = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"

# --- AUTOCOMPLETE UTILITY (Moved above Cog to prevent NameError) ---
async def server_autocomplete(itxn: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    cog = itxn.client.get_cog("ARKCog")
    cache = cog.cache if cog else []
    return [app_commands.Choice(name=s['Name'], value=s['Name']) for s in cache if current.lower() in s['Name'].lower()][:25]

class AnalyticsEngine:
    """Handles the SQLite backend for historical performance data."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_schema()

    def _initialize_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS server_stats 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, server_name TEXT, 
                            player_count INTEGER, max_players INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    def record_state(self, name: str, current: int, limit: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO server_stats (server_name, player_count, max_players) VALUES (?, ?, ?)",
                         (name, current, limit))

class GraphicsEngine:
    """Renders polished tactical dashboards based on the original UI layout."""
    @staticmethod
    def generate_dashboard(data: Dict, rates: str = "1.0") -> io.BytesIO:
        W, H = 650, 480
        curr, mx = data.get('NumPlayers', 0), data.get('MaxPlayers', 70)
        img = Image.new('RGB', (W, H), color=(26, 28, 32))
        draw = ImageDraw.Draw(img)

        # Procedural Tech Grid Background
        for x in range(0, W, 30): draw.line([(x, 0), (x, H)], fill=(32, 35, 40), width=1)
        for y in range(0, H, 30): draw.line([(0, y), (W, y)], fill=(32, 35, 40), width=1)
        draw.rectangle([(0, 0), (8, H)], fill=(50, 220, 150)) # Signature Green Accent

        try:
            f_hdr = ImageFont.truetype(Config.FONT_TITLE, 22)
            f_lbl = ImageFont.truetype(Config.FONT_TITLE, 14)
            f_val = ImageFont.truetype(Config.FONT_BODY, 18)
        except: f_hdr = f_lbl = f_val = ImageFont.load_default()

        # Header & Tech Branding
        draw.text((30, 20), "OFFICIAL SERVER STATUS", font=f_hdr, fill=(255, 255, 255))
        draw.text((W-180, 25), "NODE: PWNEDBYJT", font=f_lbl, fill=(50, 220, 150))

        # Data Field Helper
        def draw_field(x, y, w, label, value):
            draw.text((x, y), label, font=f_lbl, fill=(200, 200, 200))
            draw.rectangle([(x, y+25), (x+w, y+65)], fill=(38, 41, 46))
            draw.text((x+15, y+35), str(value), font=f_val, fill=(255, 255, 255))

        draw_field(30, 70, 590, "SERVER IDENTIFIER", data.get('Name', 'Unknown'))
        draw_field(30, 160, 150, "ACTIVE USERS", f"{curr} / {mx}")
        draw_field(200, 160, 250, "GEOGRAPHIC ZONE", data.get('MapName', 'Unknown'))
        draw_field(470, 160, 150, "CYCLE", data.get('DayTime', 'N/A'))
        draw_field(30, 250, 400, "NETWORK ADDRESS", f"{data.get('IP')}:{data.get('Port')}")
        draw_field(30, 340, 590, "CURRENT MULTIPLIER", f"{rates}x EFFECTIVE")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

class ARKCog(commands.Cog):
    """Primary logic controller for the ARKintel suite."""
    def __init__(self, bot):
        self.bot = bot
        self.analytics = AnalyticsEngine(Config.STATS_DB)
        self.cache = []
        self.monitors = self._load_data(Config.MONITORS_FILE)
        self.current_rates = "1.0"
        self.sync_cache.start()
        self.update_active_displays.start()
        self.monitor_rates.start()

    def _load_data(self, path):
        if not os.path.exists(path): return {}
        with open(path, "r") as f:
            data = json.load(f)
            for k, v in data.items():
                if "last_vc_update" in v: v["last_vc_update"] = datetime.fromisoformat(v["last_vc_update"])
            return data

    @tasks.loop(seconds=60)
    async def sync_cache(self):
        try:
            r = requests.get(Config.OFFICIAL_API, timeout=10)
            if r.status_code == 200: self.cache = r.json()
        except: pass

    @tasks.loop(seconds=60)
    async def update_active_displays(self):
        if not self.monitors or not self.cache: return
        for srv_id, meta in list(self.monitors.items()):
            node = next((s for s in self.cache if srv_id in s.get("Name", "")), None)
            if not node: continue
            self.analytics.record_state(srv_id, node.get('NumPlayers', 0), node.get('MaxPlayers', 70))
            channel = self.bot.get_channel(meta["channel_id"])
            if channel:
                img = GraphicsEngine.generate_dashboard(node, self.current_rates)
                file = discord.File(img, filename="status.png")
                try:
                    msg = await channel.fetch_message(meta["message_id"])
                    await msg.edit(attachments=[file])
                except: pass

    @tasks.loop(minutes=10)
    async def monitor_rates(self):
        try:
            r = requests.get(Config.EVO_API, timeout=5)
            rate = next((line.split('=')[1].strip() for line in r.text.splitlines() if "XPMultiplier" in line), "1.0")
            self.current_rates = rate
        except: pass

    @app_commands.command(name="monitor", description="Deploy a graphical live status terminal")
    @app_commands.autocomplete(server_id=server_autocomplete)
    async def monitor(self, itxn: discord.Interaction, server_id: str):
        await itxn.response.defer()
        node = next((s for s in self.cache if server_id in s['Name']), None)
        if not node: return await itxn.followup.send("Target node not identified.")
        img = GraphicsEngine.generate_dashboard(node, self.current_rates)
        msg = await itxn.followup.send(file=discord.File(img, filename="status.png"))
        self.monitors[server_id] = {"message_id": msg.id, "channel_id": itxn.channel_id, "last_vc_update": datetime.now(timezone.utc)}
        with open(Config.MONITORS_FILE, "w") as f:
            json.dump({k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in self.monitors.items()}, f, indent=4)

class SystemCog(commands.Cog):
    """Monitors Raspberry Pi hardware metrics."""
    @app_commands.command(name="diagnostics", description="Perform hardware integrity check")
    async def diagnostics(self, itxn: discord.Interaction):
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory()
        await itxn.response.send_message(f"HOST_CPU: {cpu}% | HOST_RAM: {ram.percent}%")

class Application(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        await self.add_cog(ARKCog(self))
        await self.add_cog(SystemCog(self))
        await self.tree.sync()
        print("Initialization complete. Operational.")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token: Application().run(token)