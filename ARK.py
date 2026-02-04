"""
Program name: ARK.py
Description: Final Restoration of the Classic Box GUI with Asynchronous OOP 
             and dynamic sidebar color logic.
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

load_dotenv()

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TARGET_CHANNEL_ID = 1178760002186526780
    ARK_ROLE_ID = 1364705580064706600
    MONITORS_FILE = os.path.join(BASE_DIR, "monitors.json")
    STATS_DB = os.path.join(BASE_DIR, "server_stats.db")
    FONT_TITLE = os.path.join(BASE_DIR, "assets", "fonts", "Orbitron-Bold.ttf")
    FONT_BODY = os.path.join(BASE_DIR, "assets", "fonts", "RobotoMono-Regular.ttf")
    OFFICIAL_API = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_API = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"

class GraphicsEngine:
    """Strict restoration of the compact Box UI for better readability."""
    def __init__(self):
        try:
            self.f_hdr = ImageFont.truetype(Config.FONT_TITLE, 22)
            self.f_lbl = ImageFont.truetype(Config.FONT_TITLE, 15)
            self.f_val = ImageFont.truetype(Config.FONT_BODY, 18)
        except:
            self.f_hdr = self.f_lbl = self.f_val = ImageFont.load_default()

    def generate_dashboard(self, data: Dict, rates: str) -> io.BytesIO:
        # Re-applying strict 650x480 dimensions to stop the stretching
        width, height = 650, 480
        img = Image.new('RGB', (width, height), color=(35, 38, 42)) # Matches image_f13bd8
        draw = ImageDraw.Draw(img)

        # 1. Dynamic Sidebar (Randomized color per run)
        sidebar_color = (random.randint(50, 255), random.randint(100, 255), random.randint(50, 255))
        draw.rectangle([(0, 0), (12, height)], fill=sidebar_color)

        # 2. Header (White text, professional font)
        draw.text((40, 25), "Official Server | Made by pwnedByJT", font=self.f_hdr, fill=(255, 255, 255))

        def draw_box(x, y, w, h, label, value):
            """Recreates the solid input-box style fields."""
            draw.text((x, y), label.upper(), font=self.f_lbl, fill=(200, 200, 200))
            # The field background box
            draw.rectangle([(x, y+25), (x+w, y+65)], fill=(28, 31, 35))
            # The data text inside the box
            draw.text((x+12, y+35), str(value), font=self.f_val, fill=(255, 255, 255))

        # 3. Exact Coordinate Mapping to match your "Old GUI" screenshots
        draw_box(40, 75, 570, 40, "Server Name", data.get('Name', 'Unknown'))
        
        # Row 2: Stats
        draw_box(40, 160, 150, 40, "Players Online", data.get('NumPlayers', 0))
        draw_box(210, 160, 240, 40, "Map", data.get('MapName', 'Unknown'))
        draw_box(470, 160, 140, 40, "Day", data.get('DayTime', 'N/A'))
        
        # Row 3: Connectivity
        draw_box(40, 245, 280, 40, "IP", data.get('IP', '0.0.0.0'))
        draw_box(340, 245, 270, 40, "Port", data.get('Port', '7777'))
        
        # Row 4: Game Environment
        draw_box(40, 330, 570, 40, "Server Rates", f"{rates}")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

# --- DISCORD BACKEND ---
async def server_autocomplete(itxn: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    cog = itxn.client.get_cog("ARKCog")
    cache = cog.cache if cog else []
    return [app_commands.Choice(name=s['Name'], value=s['Name']) 
            for s in cache if current.lower() in s['Name'].lower()][:25]

class ARKCog(commands.Cog):
    def __init__(self, bot):
        self.bot, self.gfx, self.cache = bot, GraphicsEngine(), []
        self.monitors, self.current_rates = self._load_data(), "1.0"
        self.sync_api.start()
        self.refresh_dashboards.start()
        self.check_rates.start()

    def _load_data(self):
        if not os.path.exists(Config.MONITORS_FILE): return {}
        with open(Config.MONITORS_FILE, "r") as f:
            d = json.load(f)
            for k,v in d.items(): v["last_vc_update"] = datetime.fromisoformat(v["last_vc_update"])
            return d

    @tasks.loop(seconds=60)
    async def sync_api(self):
        async with aiohttp.ClientSession() as s:
            async with s.get(Config.OFFICIAL_API) as r:
                if r.status == 200: self.cache = await r.json()

    @tasks.loop(seconds=60)
    async def refresh_dashboards(self):
        if not self.monitors or not self.cache: return
        for sid, meta in list(self.monitors.items()):
            node = next((s for s in self.cache if sid in s.get("Name", "")), None)
            if node:
                chan = self.bot.get_channel(meta["channel_id"])
                if chan:
                    img = self.gfx.generate_dashboard(node, self.current_rates)
                    try:
                        msg = await chan.fetch_message(meta["message_id"])
                        await msg.edit(attachments=[discord.File(img, filename="status.png")])
                    except: pass

    @tasks.loop(minutes=15)
    async def check_rates(self):
        async with aiohttp.ClientSession() as s:
            async with s.get(Config.EVO_API) as r:
                t = await r.text()
                self.current_rates = next((l.split('=')[1].strip() for l in t.splitlines() if "XPMultiplier" in l), "1.0")

    @app_commands.command(name="monitor", description="Deploy classic status terminal")
    @app_commands.autocomplete(server_id=server_autocomplete)
    async def monitor(self, itxn: discord.Interaction, server_id: str):
        await itxn.response.defer()
        node = next((s for s in self.cache if server_id in s['Name']), None)
        if not node: return await itxn.followup.send("Node failure.")
        img = self.gfx.generate_dashboard(node, self.current_rates)
        msg = await itxn.followup.send(file=discord.File(img, filename="status.png"))
        self.monitors[server_id] = {"message_id": msg.id, "channel_id": itxn.channel_id, "last_vc_update": datetime.now(timezone.utc)}
        with open(Config.MONITORS_FILE, "w") as f:
            json.dump({k:{**v, "last_vc_update":v["last_vc_update"].isoformat()} for k,v in self.monitors.items()}, f)

class MasterBot(commands.Bot):
    def __init__(self): super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        await self.add_cog(ARKCog(self))
        await self.tree.sync()

if __name__ == "__main__":
    MasterBot().run(os.getenv("DISCORD_TOKEN"))