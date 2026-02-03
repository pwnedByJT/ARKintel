"""
Program name: ARKintel.py (Master Master Version)
Description: Full-featured ARK monitor with Graphical Dashboards, Stats, Favorites, and Peak Analysis.
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
from PIL import Image, ImageDraw, ImageFont

# --- ROBUST PATH CONFIGURATION ---
# This ensures assets are found whether launched from Windows or Pi/PM2
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
# HELPER FUNCTIONS (DATABASE & LOGIC)
# =========================================

def init_stats_db():
    conn = sqlite3.connect(STATS_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS server_stats 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, server_name TEXT, 
                 player_count INTEGER, max_players INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_server_time ON server_stats(server_name, timestamp)')
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

def get_server_stats(server_name: str, hours: int = 24) -> dict:
    try:
        conn = sqlite3.connect(STATS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        c.execute("SELECT * FROM server_stats WHERE server_name = ? AND timestamp > ? ORDER BY timestamp", (server_name, cutoff.isoformat()))
        rows = c.fetchall()
        conn.close()
        if not rows: return {"error": "No data found"}
        counts = [r["player_count"] for r in rows]
        return {"current": counts[-1], "avg": round(sum(counts)/len(counts), 1), "peak": max(counts), "low": min(counts)}
    except: return {"error": "DB Error"}

def get_peak_hours(server_name: str, days: int = 7) -> dict:
    try:
        conn = sqlite3.connect(STATS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        c.execute("SELECT * FROM server_stats WHERE server_name = ? AND timestamp > ?", (server_name, cutoff.isoformat()))
        rows = c.fetchall()
        conn.close()
        if not rows: return {"error": "No data found"}
        hour_data = {h: [] for h in range(24)}
        for r in rows:
            ts = datetime.fromisoformat(r["timestamp"])
            hour_data[ts.hour].append(r["player_count"])
        avgs = {h: round(sum(c)/len(c), 1) for h, c in hour_data.items() if c}
        if not avgs: return {"error": "Insufficient data"}
        peak_h = max(avgs, key=avgs.get)
        return {"peak_hour": peak_h, "peak_players": avgs[peak_h]}
    except: return {"error": "DB Error"}

def load_json(file_path):
    if not os.path.exists(file_path): return {}
    try:
        with open(file_path, "r") as f: return json.load(f)
    except: return {}

def save_json(file_path, data):
    with open(file_path, "w") as f: json.dump(data, f, indent=4)

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
    
    # Theme color logic
    if curr >= 60: THEME = (220, 50, 50) # Red
    elif curr >= 35: THEME = (220, 140, 50) # Orange
    else: THEME = (50, 220, 150) # Green/Cyan

    img = Image.new('RGB', (W, H), color=(15, 20, 30))
    draw = ImageDraw.Draw(img)
    try:
        f_big = ImageFont.truetype(FONT_TITLE_PATH, 50)
        f_data = ImageFont.truetype(FONT_BODY_PATH, 22)
        f_small = ImageFont.truetype(FONT_BODY_PATH, 16)
    except:
        f_big = f_data = f_small = ImageFont.load_default()

    # Draw UI Elements
    draw.rectangle([(10, 10), (W-10, H-10)], outline=THEME, width=3)
    draw.text((40, 40), server_data.get('Name', 'ARK SERVER')[:30], font=f_big, fill=(255,255,255))
    
    # Stats Panels
    draw.text((40, 150), f"MAP: {server_data.get('MapName')}", font=f_data, fill=THEME)
    draw.text((40, 200), f"PLAYERS: {curr} / {mx}", font=f_data, fill=(255,255,255))
    draw.text((40, 250), f"DAY: {server_data.get('DayTime')}", font=f_data, fill=(255,255,255))
    draw.text((40, H-40), f"ARKintel Master | {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC", font=f_small, fill=(150,150,150))
    
    # Simple Bar
    bar_w = 340
    fill_w = int(bar_w * (curr / mx)) if mx > 0 else 0
    draw.rectangle([(420, 200), (420 + bar_w, 230)], outline=(100,100,100), width=1)
    if fill_w > 0: draw.rectangle([(422, 202), (420 + fill_w, 228)], fill=THEME)

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
        data = load_json(MONITORS_FILE)
        for k, v in data.items():
            if "last_vc_update" in v: v["last_vc_update"] = datetime.fromisoformat(v["last_vc_update"])
        monitored_servers = data
        self.update_server_cache.start()
        self.update_dashboards.start()
        self.check_evo_event.start()

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

    @tasks.loop(minutes=10)
    async def check_evo_event(self):
        curr = fetch_xp_multiplier()
        if curr and self.LAST_KNOWN_RATES and curr != self.LAST_KNOWN_RATES:
            channel = self.bot.get_channel(TARGET_CHANNEL_ID)
            if channel: await channel.send(f"🦖 <@&{ARK_ROLE_ID}> **EVO EVENT UPDATE!** New Rates: **{curr}x**")
        self.LAST_KNOWN_RATES = curr

    # --- MONITORING ---

    @app_commands.command(name="monitor", description="Deploy a graphical live monitor")
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

    @app_commands.command(name="stopmonitor", description="Disable tracking for a server")
    async def stopmonitor(self, itxn, server_number: str):
        if server_number in monitored_servers:
            del monitored_servers[server_number]
            save_json(MONITORS_FILE, {k: {**v, "last_vc_update": v["last_vc_update"].isoformat()} for k, v in monitored_servers.items()})
            await itxn.response.send_message(f"Monitoring terminated for {server_number}.")
        else: await itxn.response.send_message("Not currently monitored.", ephemeral=True)

    # --- ANALYTICS ---

    @app_commands.command(name="serverstats", description="View 24h player history")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def serverstats(self, itxn, server_number: str, hours: int = 24):
        stats = get_server_stats(server_number, hours)
        if "error" in stats: return await itxn.response.send_message("No data found.", ephemeral=True)
        await itxn.response.send_message(f"📊 **{server_number}** stats: Peak: `{stats['peak']}` | Avg: `{stats['avg']}` | Low: `{stats['low']}`")

    @app_commands.command(name="peaktime", description="Find quietest/busiest log-in times")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def peaktime(self, itxn, server_number: str):
        peak = get_peak_hours(server_number)
        if "error" in peak: return await itxn.response.send_message("No data found.", ephemeral=True)
        await itxn.response.send_message(f"⏰ **{server_number}** peaks at `{peak['peak_hour']}:00 UTC` with `{peak['peak_players']}` avg players.")

    @app_commands.command(name="topserver", description="Show the top 5 populated servers")
    async def topserver(self, itxn):
        top = sorted(CACHED_SERVERS, key=lambda s: s.get('NumPlayers', 0), reverse=True)[:5]
        embed = discord.Embed(title="🔥 Top 5 Active Official Servers", color=discord.Color.gold())
        for i, s in enumerate(top, 1):
            embed.add_field(name=f"#{i} {s['Name']}", value=f"👥 {s['NumPlayers']}/70 | 🗺️ {s['MapName']}", inline=False)
        await itxn.response.send_message(embed=embed)

    # --- FAVORITES ---

    @app_commands.command(name="fav_add", description="Save a server to your personal list")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def fav_add(self, itxn, server_number: str):
        data = load_json(FAVORITES_FILE); uid = str(itxn.user.id)
        if uid not in data: data[uid] = []
        if server_number not in data[uid]:
            data[uid].append(server_number); save_json(FAVORITES_FILE, data)
            await itxn.response.send_message(f"⭐ Added {server_number} to your favorites!")
        else: await itxn.response.send_message("Already in your list.", ephemeral=True)

    @app_commands.command(name="fav_list", description="List your favorites and their live counts")
    async def fav_list(self, itxn):
        data = load_json(FAVORITES_FILE).get(str(itxn.user.id), [])
        if not data: return await itxn.response.send_message("No favorites found.", ephemeral=True)
        favs = [s for s in CACHED_SERVERS if any(f in s['Name'] for f in data)]
        embed = discord.Embed(title="⭐ Your Favorite Servers", color=discord.Color.blue())
        for f in favs: embed.add_field(name=f['Name'], value=f"👥 {f['NumPlayers']}/70", inline=False)
        await itxn.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ARKCog(bot))

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN: exit(1)
    class ArkBot(commands.Bot):
        async def setup_hook(self):
            await self.add_cog(ARKCog(self)); await self.tree.sync()
            print("✅ ARKintel Master Ready & Synced")
    ArkBot(command_prefix="!", intents=discord.Intents.all()).run(TOKEN)