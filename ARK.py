"""
Program name: ARK.py (Final Master Version)
Description: Graphical ARK monitor with integrated Pi System Stats and .env support.
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
import psutil  # For Pi Stats
from datetime import datetime, timezone, timedelta
from typing import List 
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# --- INITIALIZE ENVIRONMENT ---
load_dotenv()  # This pulls the DISCORD_TOKEN from your .env file

# --- DYNAMIC PATH CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TARGET_CHANNEL_ID = 1178760002186526780
ARK_ROLE_ID = 1364705580064706600
FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
MONITORS_FILE = os.path.join(BASE_DIR, "monitors.json")
STATS_DB = os.path.join(BASE_DIR, "server_stats.db")
ALERT_THRESHOLD = 8

FONT_TITLE_PATH = os.path.join(BASE_DIR, "assets", "fonts", "Orbitron-Bold.ttf")
FONT_BODY_PATH = os.path.join(BASE_DIR, "assets", "fonts", "RobotoMono-Regular.ttf")

# --- GLOBALS ---
CACHED_SERVERS = [] 
monitored_servers = {} 

# =========================================
# HELPER FUNCTIONS
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

def load_json(file_path):
    if not os.path.exists(file_path): return {}
    try:
        with open(file_path, "r") as f: return json.load(f)
    except: return {}

def save_json(file_path, data):
    with open(file_path, "w") as f: json.dump(data, f, indent=4)

async def server_autocomplete(interaction, current: str):
    return [app_commands.Choice(name=s['Name'], value=s['Name']) for s in CACHED_SERVERS if current.lower() in s['Name'].lower()][:25]

# =========================================
# GRAPHICAL IMAGE GENERATOR
# =========================================

def generate_dashboard_image(server_data):
    W, H = 800, 450
    curr, mx = server_data.get('NumPlayers', 0), server_data.get('MaxPlayers', 70)
    THEME = (220, 50, 50) if curr >= 60 else (50, 220, 150)
    img = Image.new('RGB', (W, H), color=(15, 20, 30))
    draw = ImageDraw.Draw(img)
    try:
        f_big = ImageFont.truetype(FONT_TITLE_PATH, 50)
        f_data = ImageFont.truetype(FONT_BODY_PATH, 22)
    except:
        f_big = f_data = ImageFont.load_default()
    draw.rectangle([(10, 10), (W-10, H-10)], outline=THEME, width=3)
    draw.text((40, 40), server_data.get('Name', 'ARK SERVER')[:30], font=f_big, fill=(255,255,255))
    draw.text((40, 150), f"MAP: {server_data.get('MapName')}", font=f_data, fill=THEME)
    draw.text((40, 200), f"PLAYERS: {curr} / {mx}", font=f_data, fill=(255,255,255))
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    return buf

# =========================================
# COGS
# =========================================

class ARKCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_stats_db()
        global monitored_servers
        data = load_json(MONITORS_FILE)
        for k, v in data.items():
            if "last_vc_update" in v: v["last_vc_update"] = datetime.fromisoformat(v["last_vc_update"])
        monitored_servers = data
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
            record_server_stats(srv_num, new_data.get('NumPlayers', 0), new_data.get('MaxPlayers', 70))
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
        msg = await itxn.followup.send(embed=discord.Embed().set_image(url="attachment://status.png"), file=file)
        monitored_servers[server_number] = {"message_id": msg.id, "channel_id": itxn.channel_id, "last_vc_update": datetime.now(timezone.utc)}
        save_json(MONITORS_FILE, {k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in monitored_servers.items()})

class SysAdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="pistats", description="Check Raspberry Pi Hardware Health")
    async def pistats(self, itxn: discord.Interaction):
        cpu_usage = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        
        # Get Pi Temp (Linux Only)
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read()) / 1000
                temp_str = f"{temp:.1f}°C"
        except: temp_str = "N/A"

        embed = discord.Embed(title="🥧 Pi Hardware Monitor", color=discord.Color.green())
        embed.add_field(name="CPU Usage", value=f"`{cpu_usage}%`", inline=True)
        embed.add_field(name="CPU Temp", value=f"`{temp_str}`", inline=True)
        embed.add_field(name="RAM Usage", value=f"`{ram.percent}%` ({ram.used // 1024 // 1024}MB)", inline=False)
        await itxn.response.send_message(embed=embed)

# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        print("CRITICAL: DISCORD_TOKEN not found in env!")
        exit(1)

    class ArkBot(commands.Bot):
        async def setup_hook(self):
            await self.add_cog(ARKCog(self))
            await self.add_cog(SysAdminCog(self))
            await self.tree.sync()
            print("✅ ARK Master Ready & Synced with .env")

    ArkBot(command_prefix="!", intents=discord.Intents.all()).run(TOKEN)