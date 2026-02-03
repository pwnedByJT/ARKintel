"""
Program name: ARK.py (Professional Version)
Description: Modular ARK server monitor with graphical dashboards and system analytics.
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
from typing import List, Optional, Dict
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Centralized configuration for system paths and constants."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TARGET_CHANNEL_ID = 1178760002186526780
    ARK_ROLE_ID = 1364705580064706600
    FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
    MONITORS_FILE = os.path.join(BASE_DIR, "monitors.json")
    STATS_DB = os.path.join(BASE_DIR, "server_stats.db")
    FONT_TITLE = os.path.join(BASE_DIR, "assets", "fonts", "Orbitron-Bold.ttf")
    FONT_BODY = os.path.join(BASE_DIR, "assets", "fonts", "RobotoMono-Regular.ttf")
    API_URL = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_URL = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"

class DatabaseManager:
    """Handles persistence for server statistics."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_schema()

    def _initialize_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS server_stats 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, server_name TEXT, 
                            player_count INTEGER, max_players INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_server_time ON server_stats(server_name, timestamp)')

    def record_metric(self, name: str, current: int, limit: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO server_stats (server_name, player_count, max_players) VALUES (?, ?, ?)",
                         (name, current, limit))

class GraphicsEngine:
    """Generates high-fidelity visual reports."""
    @staticmethod
    def create_dashboard(data: Dict) -> io.BytesIO:
        width, height = 800, 450
        current = data.get('NumPlayers', 0)
        limit = data.get('MaxPlayers', 70)
        
        theme_color = (220, 50, 50) if current >= 60 else (50, 220, 150)
        img = Image.new('RGB', (width, height), color=(15, 20, 30))
        draw = ImageDraw.Draw(img)
        
        try:
            f_title = ImageFont.truetype(Config.FONT_TITLE, 48)
            f_data = ImageFont.truetype(Config.FONT_BODY, 22)
        except:
            f_title = f_data = ImageFont.load_default()

        draw.rectangle([(10, 10), (width-10, height-10)], outline=theme_color, width=2)
        draw.text((40, 40), data.get('Name', 'SYSTEM NODE')[:30].upper(), font=f_title, fill=(255, 255, 255))
        draw.text((40, 140), f"ZONE: {data.get('MapName', 'UNKNOWN').upper()}", font=f_data, fill=theme_color)
        draw.text((40, 180), f"ACTIVE USERS: {current} / {limit}", font=f_data, fill=(255, 255, 255))
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

class ARKCog(commands.Cog):
    """Core logic controller for server monitoring."""
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseManager(Config.STATS_DB)
        self.cache = []
        self.monitors = self._load_data(Config.MONITORS_FILE)
        self.last_rates = None
        self.sync_cache.start()
        self.update_active_monitors.start()

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
            response = requests.get(Config.API_URL, timeout=10)
            if response.status_code == 200: self.cache = response.json()
        except Exception as e: print(f"Synchronize error: {e}")

    @tasks.loop(seconds=60)
    async def update_active_monitors(self):
        if not self.monitors or not self.cache: return
        for srv_id, meta in list(self.monitors.items()):
            node = next((s for s in self.cache if srv_id in s.get("Name", "")), None)
            if not node: continue
            
            self.db.record_metric(srv_id, node.get('NumPlayers', 0), node.get('MaxPlayers', 70))
            channel = self.bot.get_channel(meta["channel_id"])
            if channel:
                img_buffer = GraphicsEngine.create_dashboard(node)
                file = discord.File(img_buffer, filename="status.png")
                embed = discord.Embed(color=0x3498db).set_image(url="attachment://status.png")
                try:
                    msg = await channel.fetch_message(meta["message_id"])
                    await msg.edit(embed=embed, attachments=[file])
                except: pass

    @app_commands.command(name="monitor", description="Deploy a live status terminal")
    async def monitor(self, itxn: discord.Interaction, server_id: str):
        await itxn.response.defer()
        node = next((s for s in self.cache if server_id in s['Name']), None)
        if not node: return await itxn.followup.send("Target node not identified.")
        
        img = GraphicsEngine.create_dashboard(node)
        file = discord.File(img, filename="status.png")
        msg = await itxn.followup.send(embed=discord.Embed().set_image(url="attachment://status.png"), file=file)
        
        self.monitors[server_id] = {"message_id": msg.id, "channel_id": itxn.channel_id, "last_vc_update": datetime.now(timezone.utc)}
        with open(Config.MONITORS_FILE, "w") as f:
            json.dump({k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in self.monitors.items()}, f, indent=4)

class SystemCog(commands.Cog):
    """Monitors hardware integrity for the local host."""
    @app_commands.command(name="diagnostics", description="Perform hardware integrity check")
    async def diagnostics(self, itxn: discord.Interaction):
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory()
        embed = discord.Embed(title="HARDWARE DIAGNOSTICS", color=0x2ecc71)
        embed.add_field(name="CPU LOAD", value=f"{cpu}%", inline=True)
        embed.add_field(name="MEMORY UTILIZATION", value=f"{ram.percent}%", inline=True)
        await itxn.response.send_message(embed=embed)

class MainBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.add_cog(ARKCog(self))
        await self.add_cog(SystemCog(self))
        await self.tree.sync()
        print("System initialization complete. Modules loaded.")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("CRITICAL: Environment token missing.")
        exit(1)
    MainBot().run(token)