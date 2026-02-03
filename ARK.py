"""
Program name: ARKintel.py
Description: Enterprise-grade ARK monitoring suite with HUD-style dashboards,
             SQL metrics, and automated system diagnostics.
Author: Justin Turner
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
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dotenv import load_dotenv

# Initialize system environment
load_dotenv()

class Config:
    """Centralized management for system constants and directory paths."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TARGET_CHANNEL_ID = 1178760002186526780
    ARK_ROLE_ID = 1364705580064706600
    
    # Storage Paths
    FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
    MONITORS_FILE = os.path.join(BASE_DIR, "monitors.json")
    STATS_DB = os.path.join(BASE_DIR, "server_stats.db")
    
    # Asset Management
    FONT_TITLE = os.path.join(BASE_DIR, "assets", "fonts", "Orbitron-Bold.ttf")
    FONT_BODY = os.path.join(BASE_DIR, "assets", "fonts", "RobotoMono-Regular.ttf")
    BG_ASSET = os.path.join(BASE_DIR, "assets", "images", "hud_bg.png") # Optional background
    
    # API Endpoints
    OFFICIAL_API = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_API = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"
    
    ALERT_THRESHOLD = 8

class AnalyticsManager:
    """Handles persistence and analytical processing of server statistics."""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialize_schema()

    def _initialize_schema(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS server_stats 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            server_name TEXT, 
                            player_count INTEGER, 
                            max_players INTEGER, 
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_server_time ON server_stats(server_name, timestamp)')

    def record_state(self, name: str, current: int, limit: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO server_stats (server_name, player_count, max_players) VALUES (?, ?, ?)",
                         (name, current, limit))

    def get_metrics(self, name: str, hours: int = 24) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
            cursor = conn.execute("SELECT player_count FROM server_stats WHERE server_name = ? AND timestamp > ?", 
                                  (name, cutoff.isoformat()))
            rows = cursor.fetchall()
            if not rows: return None
            counts = [r["player_count"] for r in rows]
            return {"avg": round(sum(counts)/len(counts), 1), "peak": max(counts), "low": min(counts), "total": len(counts)}

class HUDGenerator:
    """Renders high-fidelity graphical dashboards with HUD elements."""
    @staticmethod
    def generate(data: Dict) -> io.BytesIO:
        W, H = 800, 450
        curr, mx = data.get('NumPlayers', 0), data.get('MaxPlayers', 70)
        theme = (50, 220, 150) if curr < 40 else (220, 140, 50) if curr < 60 else (220, 50, 50)
        
        # 1. Base Layer (Dark Blue Gradient + Procedural Grid)
        img = Image.new('RGB', (W, H), color=(10, 15, 25))
        draw = ImageDraw.Draw(img)
        
        # Procedural Blueprint Grid
        for x in range(0, W, 40): draw.line([(x, 0), (x, H)], fill=(20, 30, 45), width=1)
        for y in range(0, H, 40): draw.line([(0, y), (W, y)], fill=(20, 30, 45), width=1)

        # 2. UI Elements
        try:
            f_title = ImageFont.truetype(Config.FONT_TITLE, 44)
            f_data = ImageFont.truetype(Config.FONT_BODY, 20)
        except:
            f_title = f_data = ImageFont.load_default()

        # Header HUD Block
        draw.rectangle([(20, 20), (W-20, 90)], outline=theme, width=2)
        draw.text((40, 30), data.get('Name', 'SYSTEM NODE')[:32].upper(), font=f_title, fill=(255, 255, 255))
        
        # Info Panels
        draw.text((40, 140), f"ZONE: {data.get('MapName', 'UNKNOWN').upper()}", font=f_data, fill=theme)
        draw.text((40, 180), f"DAY CYCLE: {data.get('DayTime', 'N/A')}", font=f_data, fill=(200, 200, 200))
        draw.text((40, 220), f"NET_ADDR: {data.get('IP')}:{data.get('Port')}", font=f_data, fill=(150, 150, 150))

        # Progress Radial/Bar HUD
        draw.text((450, 140), "CAPACITY UTILIZATION", font=f_data, fill=(255, 255, 255))
        draw.rectangle([(450, 170), (750, 200)], outline=(60, 60, 60), width=1)
        fill_w = int(300 * (curr/mx)) if mx > 0 else 0
        if fill_w > 0:
            draw.rectangle([(452, 172), (450+fill_w, 198)], fill=theme)
        draw.text((450, 210), f"LOAD: {curr} / {mx}", font=f_title, fill=(255, 255, 255))

        # Footer
        draw.text((40, H-40), f"INTEGRITY VERIFIED | {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC", font=f_data, fill=(80, 80, 80))

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

class ARKCog(commands.Cog):
    """Core controller for Discord gateway and monitoring logic."""
    def __init__(self, bot):
        self.bot = bot
        self.analytics = AnalyticsManager(Config.STATS_DB)
        self.cache = []
        self.monitors = self._load_json(Config.MONITORS_FILE)
        self.last_rates = None
        
        self.sync_cache.start()
        self.background_refresh.start()
        self.evo_monitor.start()

    def _load_json(self, path):
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
    async def background_refresh(self):
        if not self.monitors or not self.cache: return
        for srv_id, meta in list(self.monitors.items()):
            node = next((s for s in self.cache if srv_id in s.get("Name", "")), None)
            if not node: continue
            
            self.analytics.record_state(srv_id, node.get('NumPlayers', 0), node.get('MaxPlayers', 70))
            
            # Dashboard Update
            channel = self.bot.get_channel(meta["channel_id"])
            if channel:
                img = HUDGenerator.generate(node)
                file = discord.File(img, filename="hud.png")
                embed = discord.Embed(color=0x2f3136).set_image(url="attachment://hud.png")
                try:
                    msg = await channel.fetch_message(meta["message_id"])
                    await msg.edit(embed=embed, attachments=[file])
                except: pass

    @tasks.loop(minutes=10)
    async def evo_monitor(self):
        try:
            r = requests.get(Config.EVO_API, timeout=5)
            rate = next((line.split('=')[1].strip() for line in r.text.splitlines() if "XPMultiplier" in line), None)
            if rate and self.last_rates and rate != self.last_rates:
                chan = self.bot.get_channel(Config.TARGET_CHANNEL_ID)
                if chan: await chan.send(f"NETWORK ADVISORY: Server rates updated to {rate}x")
            self.last_rates = rate
        except: pass

    @app_commands.command(name="monitor", description="Deploy HUD dashboard")
    @app_commands.autocomplete(server_id=server_autocomplete)
    async def monitor(self, itxn: discord.Interaction, server_id: str):
        await itxn.response.defer()
        node = next((s for s in self.cache if server_id in s['Name']), None)
        if not node: return await itxn.followup.send("Node not found.")
        
        img = HUDGenerator.generate(node)
        file = discord.File(img, filename="hud.png")
        msg = await itxn.followup.send(embed=discord.Embed().set_image(url="attachment://hud.png"), file=file)
        
        self.monitors[server_id] = {"message_id": msg.id, "channel_id": itxn.channel_id, "last_vc_update": datetime.now(timezone.utc)}
        with open(Config.MONITORS_FILE, "w") as f:
            json.dump({k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in self.monitors.items()}, f, indent=4)

    @app_commands.command(name="diagnostics", description="Host hardware health check")
    async def diagnostics(self, itxn: discord.Interaction):
        cpu, ram = psutil.cpu_percent(), psutil.virtual_memory()
        embed = discord.Embed(title="HARDWARE DIAGNOSTICS", color=0x00ff00)
        embed.add_field(name="CPU LOAD", value=f"{cpu}%", inline=True)
        embed.add_field(name="RAM UTILIZATION", value=f"{ram.percent}%", inline=True)
        await itxn.response.send_message(embed=embed)

async def server_autocomplete(itxn: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    # Access global cache via the Cog if loaded, or fetch fresh
    cog = itxn.client.get_cog("ARKCog")
    cache = cog.cache if cog else []
    return [app_commands.Choice(name=s['Name'], value=s['Name']) for s in cache if current.lower() in s['Name'].lower()][:25]

class MasterBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        await self.add_cog(ARKCog(self))
        await self.tree.sync()
        print("System stabilization complete. Operational.")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token: exit("Critical: Authorization token missing.")
    MasterBot().run(token)