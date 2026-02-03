"""
Program name: ARKintel.py (Graphical Version - PM2 Optimized)
Description: Monitors Official ARK servers with generated graphical dashboards.
Author: Justin Aaron Turner
Updated: 2/3/2026
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
import os
import json
import sqlite3
import io
from datetime import datetime, timezone, timedelta
from typing import List 

# --- PILLOW IMPORTS ---
from PIL import Image, ImageDraw, ImageFont

# --- CONFIGURATION ---
TARGET_CHANNEL_ID = 1178760002186526780
ARK_ROLE_ID = 1364705580064706600
FAVORITES_FILE = "favorites.json"
MONITORS_FILE = "monitors.json"
STATS_DB = "server_stats.db"
ALERT_THRESHOLD = 8

# --- ASSET PATHS ---
FONT_TITLE_PATH = "assets/fonts/Orbitron-Bold.ttf"
FONT_BODY_PATH = "assets/fonts/RobotoMono-Regular.ttf"

# --- GLOBALS ---
CACHED_SERVERS = [] 
monitored_servers = {} 

# =========================================
# HELPER FUNCTIONS (DATABASE & UTILS)
# =========================================

def init_stats_db():
    conn = sqlite3.connect(STATS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS server_stats 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, server_name TEXT, 
                 player_count INTEGER, max_players INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def record_server_stats(server_name: str, player_count: int, max_players: int):
    try:
        conn = sqlite3.connect(STATS_DB)
        conn.execute("INSERT INTO server_stats (server_name, player_count, max_players) VALUES (?, ?, ?)",
                     (server_name, player_count, max_players))
        conn.commit()
        conn.close()
    except Exception as e: print(f"DB Error: {e}")

def load_monitors():
    if not os.path.exists(MONITORS_FILE): return {}
    try:
        with open(MONITORS_FILE, "r") as f:
            data = json.load(f)
            for k, v in data.items():
                if "last_vc_update" in v:
                    v["last_vc_update"] = datetime.fromisoformat(v["last_vc_update"])
            return data
    except: return {}

def save_monitors():
    data = {k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in monitored_servers.items()}
    with open(MONITORS_FILE, "w") as f: json.dump(data, f, indent=4)

def fetch_xp_multiplier():
    try:
        r = requests.get("https://cdn2.arkdedicated.com/asa/dynamicconfig.ini", timeout=5)
        for line in r.text.splitlines():
            if "XPMultiplier" in line: return line.split('=')[1].strip()
    except: return None

async def server_autocomplete(interaction, current: str):
    return [app_commands.Choice(name=s['Name'], value=s['Name']) for s in CACHED_SERVERS if current.lower() in s['Name'].lower()][:25]

# =========================================
# GRAPHICAL IMAGE GENERATOR
# =========================================

def generate_dashboard_image(server_data):
    W, H = 800, 450
    curr, mx = server_data.get('NumPlayers', 0), server_data.get('MaxPlayers', 70)
    
    # Theme color based on pop
    THEME = (220, 50, 50) if curr >= 60 else (50, 220, 150)
    
    img = Image.new('RGB', (W, H), color=(15, 20, 30))
    draw = ImageDraw.Draw(img)

    try:
        f_big = ImageFont.truetype(FONT_TITLE_PATH, 50)
        f_data = ImageFont.truetype(FONT_BODY_PATH, 22)
    except:
        f_big = f_data = ImageFont.load_default()

    # Borders & Header
    draw.rectangle([(10, 10), (W-10, H-10)], outline=THEME, width=3)
    draw.text((40, 40), server_data.get('Name', 'ARK SERVER')[:30], font=f_big, fill=(255,255,255))
    
    # Data stats
    draw.text((40, 150), f"MAP: {server_data.get('MapName')}", font=f_data, fill=THEME)
    draw.text((40, 200), f"PLAYERS: {curr} / {mx}", font=f_data, fill=(255,255,255))
    draw.text((40, 250), f"DAY: {server_data.get('DayTime')}", font=f_data, fill=(255,255,255))

    # Memory Buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# =========================================
# THE COG CLASS
# =========================================

class ARKCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.LAST_KNOWN_RATES = None
        init_stats_db()
        global monitored_servers
        monitored_servers = load_monitors()
        self.update_server_cache.start()
        self.update_dashboards.start()

    @tasks.loop(seconds=60)
    async def update_server_cache(self):
        global CACHED_SERVERS
        try:
            r = requests.get("https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json", timeout=10)
            if r.status_code == 200: CACHED_SERVERS = r.json()
        except: pass

    @tasks.loop(seconds=60)
    async def update_dashboards(self):
        if not monitored_servers or not CACHED_SERVERS: return
        for srv_num, info in list(monitored_servers.items()):
            new_data = next((s for s in CACHED_SERVERS if srv_num in s.get("Name", "")), None)
            if not new_data: continue

            channel = self.bot.get_channel(info["channel_id"])
            if channel:
                img = generate_dashboard_image(new_data)
                file = discord.File(img, filename="status.png")
                embed = discord.Embed(color=discord.Color.blue()).set_image(url="attachment://status.png")
                try:
                    msg = await channel.fetch_message(info["message_id"])
                    await msg.edit(embed=embed, attachments=[file])
                except: pass

    @app_commands.command(name="monitor")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def monitor(self, itxn, server_number: str):
        await itxn.response.defer()
        target = next((s for s in CACHED_SERVERS if server_number in s['Name']), None)
        if not target: return await itxn.followup.send("Server not found.")

        img = generate_dashboard_image(target)
        file = discord.File(img, filename="status.png")
        embed = discord.Embed().set_image(url="attachment://status.png")
        msg = await itxn.followup.send(embed=embed, file=file)

        monitored_servers[server_number] = {
            "message_id": msg.id, "channel_id": itxn.channel_id,
            "last_vc_update": datetime.now(timezone.utc)
        }
        save_monitors()

async def setup(bot):
    await bot.add_cog(ARKCog(bot))

# =========================================
# MAIN EXECUTION (PM2 / ENVIRONMENT)
# =========================================

if __name__ == "__main__":
    # PM2 should provide DISCORD_TOKEN as an environment variable
    TOKEN = os.getenv("DISCORD_TOKEN")

    if not TOKEN:
        print("CRITICAL ERROR: DISCORD_TOKEN is missing from the environment.")
        exit(1)

    class ArkBot(commands.Bot):
        async def setup_hook(self):
            await self.add_cog(ARKCog(self))
            await self.tree.sync()

    bot = ArkBot(command_prefix="!", intents=discord.Intents.default())
    bot.run(TOKEN)