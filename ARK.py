"""
Program name: ARK.py
Description: Enterprise-grade ARK monitoring suite.
             Features: Live Dashboards, /console optimization, /serverpop,
             Voice Counters, Favorites, SQL Analytics, and Auto-EVO Alerts.
             Architecture: Async/OOP (Non-blocking)
             Standards: Strict No-Emote Policy | Dynamic Random Colors
Author: Justin Aaron Turner
Updated: February 3, 2026
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import aiosqlite
import os
import sys
import json
import random
import io
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from dotenv import load_dotenv
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.dates as mdates

# Ensure repo root is on sys.path so 'data' and 'cogs' packages resolve
# when running as `python ARK.py` from the repo root directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# --- CONFIGURATION ---
class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TARGET_CHANNEL_ID = 1178760002186526780
    ARK_ROLE_ID = 1364705580064706600
    MONITORS_FILE = os.path.join(BASE_DIR, "monitors.json")
    STATS_DB = os.path.join(BASE_DIR, "server_stats.db")
    FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")
    
    OFFICIAL_API = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
    EVO_API = "https://cdn2.arkdedicated.com/asa/dynamicconfig.ini"
    ALERT_THRESHOLD = 8
    POP_ALERTS_FILE = os.path.join(BASE_DIR, "pop_alerts.json")

# --- DATABASE ENGINE ---
class DatabaseEngine:
    def __init__(self, db_path):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''CREATE TABLE IF NOT EXISTS server_stats 
                                (id INTEGER PRIMARY KEY AUTOINCREMENT, server_name TEXT, 
                                player_count INTEGER, max_players INTEGER, 
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_server_time ON server_stats(server_name, timestamp)')
            await db.commit()

    async def record_stats(self, name: str, current: int, limit: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT INTO server_stats (server_name, player_count, max_players) VALUES (?, ?, ?)",
                             (name, current, limit))
            await db.commit()

    async def get_stats(self, name: str, hours: int = 24):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
            async with db.execute("SELECT player_count FROM server_stats WHERE server_name = ? AND timestamp > ? ORDER BY timestamp", (name, cutoff)) as cursor:
                rows = await cursor.fetchall()
                if not rows: return None
                counts = [r['player_count'] for r in rows]
                return {
                    "current": counts[-1], "avg": round(sum(counts)/len(counts), 1),
                    "peak": max(counts), "low": min(counts), "samples": len(counts)
                }

    async def get_timeseries(self, name: str, hours: int = 24):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT player_count, timestamp FROM server_stats "
                "WHERE server_name = ? AND timestamp > datetime('now', ?) "
                "ORDER BY timestamp",
                (name, f'-{hours} hours')
            ) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    return None
                return [(r['timestamp'], r['player_count']) for r in rows]

    async def get_scout_targets(self, min_avg: float = 3.0, min_samples: int = 24, days: int = 7) -> list:
        """
        Return servers whose weekly average population exceeds min_avg.
        Only servers that have been actively monitored via /monitor will appear —
        record_stats is only called from update_monitors.
        Results capped at 10, ordered by weekly avg descending.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT server_name,
                       ROUND(AVG(player_count), 1) AS weekly_avg,
                       COUNT(*)                    AS total_samples
                FROM   server_stats
                WHERE  timestamp > datetime('now', ?)
                GROUP  BY server_name
                HAVING weekly_avg > ? AND total_samples >= ?
                ORDER  BY weekly_avg DESC
                LIMIT  10
                """,
                (f'-{days} days', min_avg, min_samples)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_quiet_window(self, name: str, min_hour_samples: int = 3, days: int = 7) -> dict | None:
        """
        Find the UTC hour-of-day with the lowest average population for a server.
        Hours with fewer than min_hour_samples data points are excluded — a single
        stray 0-pop sample would otherwise win as a false raid window.
        Returns dict(hour_utc, avg_pop, samples) or None.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT CAST(strftime('%H', timestamp) AS INTEGER) AS hour_utc,
                       ROUND(AVG(player_count), 1)                AS avg_pop,
                       COUNT(*)                                   AS samples
                FROM   server_stats
                WHERE  server_name = ? AND timestamp > datetime('now', ?)
                GROUP  BY hour_utc
                HAVING samples >= ?
                ORDER  BY avg_pop ASC, samples DESC
                LIMIT  1
                """,
                (name, f'-{days} days', min_hour_samples)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

# --- UI UTILITIES ---
class EmbedFactory:
    @staticmethod
    def create_monitor(data: Dict, rates: str = "1.0") -> discord.Embed:
        # Status Color Logic
        pop = data.get('NumPlayers', 0)
        color = discord.Color.green() if pop < 40 else (discord.Color.gold() if pop < 65 else discord.Color.red())
        
        status_text = "[ONLINE]" if pop < 70 else "[FULL]"
        
        embed = discord.Embed(title=f"{status_text} {data.get('Name')}", color=color)
        
        # FOOTER: Includes branding and update time
        footer_time = datetime.now(timezone.utc).strftime('%H:%M UTC')
        embed.set_footer(text=f"Designed by pwnedByJT | UPDATED: {footer_time}")
        
        # Professional Code Blocks
        embed.add_field(name="Server Name", value=f"```{data.get('Name')}```", inline=False)
        embed.add_field(name="Player Count", value=f"```{pop}/{data.get('MaxPlayers', 70)}```", inline=True)
        embed.add_field(name="Map Name", value=f"```{data.get('MapName')}```", inline=True)
        embed.add_field(name="Day Cycle", value=f"```{data.get('DayTime')}```", inline=True)
        embed.add_field(name="IP Address", value=f"```{data.get('IP')}```", inline=True)
        embed.add_field(name="Port", value=f"```{data.get('Port')}```", inline=True)
        embed.add_field(name="EVO Multiplier", value=f"```{rates}x```", inline=False)
        
        return embed

async def server_autocomplete(itxn: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    cog = itxn.client.get_cog("ARKCog")
    cache = cog.cache if cog else []
    return [app_commands.Choice(name=s['Name'], value=s['Name']) 
            for s in cache if current.lower() in s['Name'].lower()][:25]

# --- MAIN LOGIC ---
class ARKCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = DatabaseEngine(Config.STATS_DB)
        self.cache = []
        self.monitors = self._load_json(Config.MONITORS_FILE)
        self.favorites = self._load_json(Config.FAVORITES_FILE)
        self.pop_alerts = self._load_json(Config.POP_ALERTS_FILE)
        self.current_rates = "1.0"
        self.last_rates = None

        self.sync_cache.start()
        self.update_monitors.start()
        self.check_evo.start()
        self.check_pop_alerts.start()

    def _load_json(self, path):
        if not os.path.exists(path): return {}
        try:
            with open(path, 'r') as f: return json.load(f)
        except: return {}

    def _save_json(self, path, data):
        with open(path, 'w') as f: json.dump(data, f, indent=4)

    @tasks.loop(seconds=60)
    async def sync_cache(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(Config.OFFICIAL_API, timeout=10) as r:
                    if r.status == 200: self.cache = await r.json()
            except: pass

    @tasks.loop(seconds=60)
    async def update_monitors(self):
        if not self.monitors or not self.cache: return
        
        for srv_id, meta in list(self.monitors.items()):
            node = next((s for s in self.cache if srv_id in s.get("Name", "")), None)
            if node:
                await self.db.record_stats(srv_id, node.get('NumPlayers'), node.get('MaxPlayers'))
                
                chan = self.bot.get_channel(meta["channel_id"])
                if chan:
                    embed = EmbedFactory.create_monitor(node, self.current_rates)
                    try:
                        msg = await chan.fetch_message(meta["message_id"])
                        await msg.edit(embed=embed)
                    except: pass
                    
                    vc_id = meta.get("vc_id")
                    if vc_id:
                        vc = self.bot.get_channel(vc_id)
                        if vc:
                            new_name = f"VC {srv_id}: {node.get('NumPlayers')}/{node.get('MaxPlayers')}"
                            if vc.name != new_name:
                                try: await vc.edit(name=new_name)
                                except: pass

    @tasks.loop(minutes=10)
    async def check_evo(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(Config.EVO_API) as r:
                    txt = await r.text()
                    rate = next((l.split('=')[1].strip() for l in txt.splitlines() if "XPMultiplier" in l), "1.0")
                    self.current_rates = rate
                    
                    if self.last_rates and rate != self.last_rates:
                        chan = self.bot.get_channel(Config.TARGET_CHANNEL_ID)
                        if chan: await chan.send(f"**EVO ALERT**: Rates changed to **{rate}x**!")
                    self.last_rates = rate
            except: pass

    @tasks.loop(seconds=60)
    async def check_pop_alerts(self):
        if not self.pop_alerts or not self.cache:
            return

        save_needed = False
        for uid, alerts in self.pop_alerts.items():
            for alert in alerts:
                node = next((s for s in self.cache if alert["server"] in s.get("Name", "")), None)
                if not node:
                    continue
                pop = node.get('NumPlayers') or 0
                below = pop < alert["threshold"]

                if below and not alert.get("triggered"):
                    alert["triggered"] = True
                    save_needed = True
                    chan = self.bot.get_channel(alert["channel_id"])
                    if chan:
                        try:
                            await chan.send(
                                f"<@{uid}> **[POP ALERT]** **{alert['server']}** has dropped below "
                                f"**{alert['threshold']}** players -- currently **{pop}** online."
                            )
                        except:
                            pass
                elif not below and alert.get("triggered"):
                    alert["triggered"] = False
                    save_needed = True

        if save_needed:
            self._save_json(Config.POP_ALERTS_FILE, self.pop_alerts)

    # --- COMMANDS ---

    @app_commands.command(name="console", description="Get optimization console commands")
    async def console(self, itxn: discord.Interaction):
        # Optimization String
        cmd_string = (
            "FoliageQuality 0 | sg.TextureQuality 0 | r.Shading.FurnaceTest.SampleCount 0 | "
            "r.VolumetricCloud 0 | r.VolumetricFog 0 | r.Water.SingleLayer.Reflection 0 | "
            "r.ShadowQuality 0 | r.ContactShadows 0 | r.depthoffieldquality 0 | r.Fog 0 | "
            "r.bloomquality 0 | r.LightCulling.Quality 0 | r.SkyAtmosphere 0 | "
            "r.Lumen.Reflections.Allow 1 | r.Lumen.DiffuseIndirect.Allow 1 | "
            "r.Shadow.Virtual.Enable 0 | r.DistanceFieldShadowing 1 | "
            "r.Shadow.CSM.MaxCascades 0 | r.SkylightIntensityMultiplier 1 | grass.sizescale 0 | "
            "ark.MaxActiveDestroyedMeshGeoCollectionCount 0 | r.Tonemapper.Sharpen 2 | "
            "r.SkyLight.RealTimeReflectionCapture 0 | r.EyeAdaptation.BlackHistogramBucketInfluence 0 | "
            "r.Lumen.Reflections.Contrast -4 | r.LightMaxDrawDistanceScale -1 | "
            "r.Lumen.ScreenProbeGather.DirectLighting 1 | r.Color.Grading 0 | grass.sizeScale 0 | "
            "r.Water.SingleLayer.Reflection 0 | r.shadowquality 0 | r.shadow.virtual.enable 0 | gamma 4 |"
        )
        
        rand_color = discord.Color(random.randint(0, 0xFFFFFF))
        embed = discord.Embed(title="Console Optimization Commands", color=rand_color)
        embed.set_footer(text="Designed by pwnedByJT")
        embed.add_field(name="Copy Command String", value=f"```{cmd_string}```", inline=False)
        
        await itxn.response.send_message(embed=embed)

    @app_commands.command(name="monitor", description="Start a live dashboard and voice counter")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def monitor(self, itxn: discord.Interaction, server_number: str):
        await itxn.response.defer()
        
        node = next((s for s in self.cache if server_number in s['Name']), None)
        if not node: return await itxn.followup.send("Server not found in API cache.")

        embed = EmbedFactory.create_monitor(node, self.current_rates)
        msg = await itxn.followup.send(embed=embed)
        
        vc_id = None
        if itxn.guild:
            cat = discord.utils.get(itxn.guild.categories, name="[ Ark ]") or itxn.channel.category
            try:
                vc = await itxn.guild.create_voice_channel(
                    name=f"VC {server_number}: {node.get('NumPlayers')}/70", 
                    category=cat
                )
                vc_id = vc.id
            except: await itxn.followup.send("Failed to create Voice Channel (Check permissions).", ephemeral=True)

        self.monitors[server_number] = {"message_id": msg.id, "channel_id": itxn.channel_id, "vc_id": vc_id}
        self._save_json(Config.MONITORS_FILE, self.monitors)

    @app_commands.command(name="serverpop", description="Check current status (One-time snapshot)")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def serverpop(self, itxn: discord.Interaction, server_number: str):
        await itxn.response.defer()
        
        node = next((s for s in self.cache if server_number in s['Name']), None)
        if not node: return await itxn.followup.send("Server not found in API cache.")

        embed = EmbedFactory.create_monitor(node, self.current_rates)
        await itxn.followup.send(embed=embed)

    @app_commands.command(name="stopmonitor", description="Stop tracking a server")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def stopmonitor(self, itxn: discord.Interaction, server_number: str):
        if server_number in self.monitors:
            data = self.monitors.pop(server_number)
            self._save_json(Config.MONITORS_FILE, self.monitors)
            try: 
                if data.get("vc_id"): await self.bot.get_channel(data["vc_id"]).delete()
                await (await self.bot.get_channel(data["channel_id"]).fetch_message(data["message_id"])).delete()
            except: pass
            await itxn.response.send_message(f"Stopped monitoring **{server_number}**.")
        else:
            await itxn.response.send_message("Server is not being monitored.", ephemeral=True)

    @app_commands.command(name="popwatch", description="Alert when a server drops below a population threshold")
    @app_commands.describe(server_number="Server to watch", threshold="Alert when population drops below this number")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def popwatch(self, itxn: discord.Interaction, server_number: str, threshold: int):
        uid = str(itxn.user.id)
        if uid not in self.pop_alerts:
            self.pop_alerts[uid] = []

        existing = next((a for a in self.pop_alerts[uid] if a["server"] == server_number), None)
        if existing:
            existing["threshold"] = threshold
            existing["triggered"] = False
            msg = f"Updated alert for **{server_number}** — will ping when below **{threshold}** players."
        else:
            self.pop_alerts[uid].append({
                "server": server_number,
                "threshold": threshold,
                "channel_id": itxn.channel_id,
                "triggered": False
            })
            msg = f"Alert set for **{server_number}** — you will be pinged when population drops below **{threshold}** players."

        self._save_json(Config.POP_ALERTS_FILE, self.pop_alerts)
        await itxn.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="popwatch_remove", description="Remove a population alert")
    @app_commands.describe(server_number="Server to stop watching")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def popwatch_remove(self, itxn: discord.Interaction, server_number: str):
        uid = str(itxn.user.id)
        if uid not in self.pop_alerts or not self.pop_alerts[uid]:
            return await itxn.response.send_message("You have no active population alerts.", ephemeral=True)

        before = len(self.pop_alerts[uid])
        self.pop_alerts[uid] = [a for a in self.pop_alerts[uid] if a["server"] != server_number]
        if len(self.pop_alerts[uid]) < before:
            self._save_json(Config.POP_ALERTS_FILE, self.pop_alerts)
            await itxn.response.send_message(f"Removed pop alert for **{server_number}**.", ephemeral=True)
        else:
            await itxn.response.send_message(f"No alert found for **{server_number}**.", ephemeral=True)

    @app_commands.command(name="fav_add", description="Add server to favorites")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def fav_add(self, itxn: discord.Interaction, server_number: str):
        uid = str(itxn.user.id)
        if uid not in self.favorites: self.favorites[uid] = []
        if server_number not in self.favorites[uid]:
            self.favorites[uid].append(server_number)
            self._save_json(Config.FAVORITES_FILE, self.favorites)
            await itxn.response.send_message(f"Added **{server_number}** to favorites.")
        else:
            await itxn.response.send_message("Server is already in favorites.", ephemeral=True)

    @app_commands.command(name="fav_list", description="View your favorites")
    async def fav_list(self, itxn: discord.Interaction):
        uid = str(itxn.user.id)
        if uid not in self.favorites or not self.favorites[uid]:
            return await itxn.response.send_message("You have no favorites.", ephemeral=True)
        
        rand_color = discord.Color(random.randint(0, 0xFFFFFF))
        embed = discord.Embed(title=f"{itxn.user.name}'s Favorites", color=rand_color)
        embed.set_footer(text="Designed by pwnedByJT") 
        
        for srv in self.favorites[uid]:
            node = next((s for s in self.cache if srv in s['Name']), None)
            status = f"[ONLINE] {node.get('NumPlayers')}/70" if node else "[OFFLINE]"
            embed.add_field(name=srv, value=status, inline=False)
        await itxn.response.send_message(embed=embed)

    @app_commands.command(name="fav_remove", description="Remove a server from favorites")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def fav_remove(self, itxn: discord.Interaction, server_number: str):
        uid = str(itxn.user.id)
        if uid not in self.favorites or server_number not in self.favorites[uid]:
            return await itxn.response.send_message("Server not in your favorites.", ephemeral=True)
        self.favorites[uid].remove(server_number)
        self._save_json(Config.FAVORITES_FILE, self.favorites)
        await itxn.response.send_message(f"Removed **{server_number}** from favorites.")

    @app_commands.command(name="serverstats", description="View historical analytics")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def serverstats(self, itxn: discord.Interaction, server_number: str, hours: int = 24):
        await itxn.response.defer()
        stats = await self.db.get_stats(server_number, hours)
        if not stats: return await itxn.followup.send("No data recorded yet. Monitor the server first.")
        
        rand_color = discord.Color(random.randint(0, 0xFFFFFF))
        embed = discord.Embed(title=f"Analytics: {server_number}", color=rand_color)
        embed.set_footer(text="Designed by pwnedByJT")
        
        embed.add_field(name="Current", value=f"`{stats['current']}`", inline=True)
        embed.add_field(name="Average", value=f"`{stats['avg']}`", inline=True)
        embed.add_field(name="Peak", value=f"`{stats['peak']}`", inline=True)
        embed.add_field(name="Samples", value=f"`{stats['samples']}`", inline=True)
        await itxn.followup.send(embed=embed)

    @app_commands.command(name="popgraph", description="Visual population chart for a monitored server")
    @app_commands.describe(server_number="Server to graph", hours="How many hours back to show (default 24)")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def popgraph(self, itxn: discord.Interaction, server_number: str, hours: int = 24):
        await itxn.response.defer()

        rows = await self.db.get_timeseries(server_number, hours)
        if not rows or len(rows) < 2:
            return await itxn.followup.send(
                "Not enough data to graph. Run `/monitor` on the server first to start collecting history."
            )

        # Parse timestamps — SQLite CURRENT_TIMESTAMP is space-separated, not ISO 'T'
        timestamps = [datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S') for r in rows]
        counts = [r[1] for r in rows]
        avg = sum(counts) / len(counts)
        peak = max(counts)
        low = min(counts)

        # Pick line color by average population (mirrors EmbedFactory logic)
        line_color = '#57f287' if avg < 40 else ('#fee75c' if avg < 65 else '#ed4245')

        # Build chart — OO API only, no pyplot (headless-safe, no figure leak)
        fig = Figure(figsize=(10, 4), dpi=110)
        FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)

        # Discord dark theme
        fig.patch.set_facecolor('#2b2d31')
        ax.set_facecolor('#1e1f22')

        # Main line + fill
        ax.plot(timestamps, counts, color=line_color, linewidth=2.2, zorder=3)
        ax.fill_between(timestamps, counts, alpha=0.12, color=line_color)

        # Reference lines
        ax.axhline(avg,  color='#b5bac1', linewidth=0.9, linestyle='--', alpha=0.6, label=f'Avg {avg:.1f}')
        ax.axhline(peak, color='#ed4245', linewidth=0.9, linestyle=':',  alpha=0.7, label=f'Peak {peak}')

        # Axes styling
        ax.set_ylim(0, 75)
        ax.set_ylabel('Players', color='#b5bac1', fontsize=9)
        ax.set_xlabel('Time (UTC)', color='#b5bac1', fontsize=9)
        ax.tick_params(colors='#b5bac1', which='both', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#3f4148')
        ax.set_title(f'{server_number}  —  last {hours}h', color='#ffffff', fontsize=11, pad=10)
        ax.legend(facecolor='#2b2d31', edgecolor='#3f4148', labelcolor='#b5bac1', fontsize=8)

        # X-axis: show HH:MM, auto-rotate labels
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        fig.autofmt_xdate(rotation=35, ha='right')
        fig.tight_layout()

        # Render to buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', facecolor=fig.get_facecolor())
        buf.seek(0)

        # Stats embed with chart as image
        rand_color = discord.Color(random.randint(0, 0xFFFFFF))
        embed = discord.Embed(title=f"Population Chart: {server_number}", color=rand_color)
        embed.set_footer(text="Designed by pwnedByJT")
        embed.add_field(name="Current", value=f"`{counts[-1]}`", inline=True)
        embed.add_field(name="Average", value=f"`{avg:.1f}`",    inline=True)
        embed.add_field(name="Peak",    value=f"`{peak}`",        inline=True)
        embed.add_field(name="Low",     value=f"`{low}`",         inline=True)
        embed.add_field(name="Samples", value=f"`{len(counts)}`", inline=True)
        embed.add_field(name="Window",  value=f"`{hours}h`",      inline=True)
        embed.set_image(url="attachment://pop.png")

        await itxn.followup.send(embed=embed, file=discord.File(buf, filename="pop.png"))

class Bot(commands.Bot):
    def __init__(self): super().__init__(command_prefix="!", intents=discord.Intents.all())
    async def setup_hook(self):
        # Core monitoring cog
        cog = ARKCog(self)
        await cog.db.initialize()
        await self.add_cog(cog)

        # Tame stats / meta guide cog
        from cogs.tame_stats_cog import TameStatsCog
        await self.add_cog(TameStatsCog(self))

        # Imprint / hatch timer cog
        from cogs.imprint_cog import ImprintCog
        await self.add_cog(ImprintCog(self))

        # Consumable recipe reference cog
        from cogs.recipe_cog import RecipeCog
        await self.add_cog(RecipeCog(self))

        # Raid calculator cog
        from cogs.raid_calc_cog import RaidCalcCog
        await self.add_cog(RaidCalcCog(self))

        # Boss entry checklist cog
        from cogs.boss_check_cog import BossCheckCog
        await self.add_cog(BossCheckCog(self))

        # Help / command reference cog
        from cogs.help_cog import HelpCog
        await self.add_cog(HelpCog(self))

        # K3s cluster health cog
        from cogs.cluster_status_cog import ClusterStatusCog
        await self.add_cog(ClusterStatusCog(self))

        # Raid intel / population analytics cog
        from cogs.raid_intel_cog import RaidIntelCog
        await self.add_cog(RaidIntelCog(self))

        await self.tree.sync()
        print(
            "System Online | ARKintel Enterprise | "
            "Commands: /tame-stats /imprint /recipe /raid-calc /boss-check /cluster-status /ark-help"
        )

if __name__ == "__main__":
    Bot().run(os.getenv("DISCORD_TOKEN"))