"""
Program name: ARKintel.py (Cog Version)
Description: Monitors Official ARK servers with Live Dashboards, Voice Channels, Favorites, Autocomplete, and Auto-EVO Alerts.
Author: Justin Aaron Turner
Updated: 1/30/2026
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
import os
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import List 
from dotenv import load_dotenv

# --- CONFIGURATION ---
TARGET_CHANNEL_ID = 1178760002186526780
ARK_ROLE_ID = 1364705580064706600
FAVORITES_FILE = "favorites.json"
STATS_DB = "server_stats.db"
ALERT_THRESHOLD = 8  # Players needed to trigger alert
# ---------------------

# --- MODULE LEVEL GLOBALS ---
# Kept global so the standalone autocomplete function can access them easily
CACHED_SERVERS = [] 
monitored_servers = {} 

# =========================================
# HELPER FUNCTIONS
# =========================================

def init_stats_db():
    """Initialize the server stats database"""
    conn = sqlite3.connect(STATS_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS server_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_name TEXT NOT NULL,
            player_count INTEGER NOT NULL,
            max_players INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_server_time 
        ON server_stats(server_name, timestamp)
    ''')
    conn.commit()
    conn.close()

def record_server_stats(server_name: str, player_count: int, max_players: int):
    """Record player count for a server"""
    try:
        conn = sqlite3.connect(STATS_DB)
        c = conn.cursor()
        c.execute(
            "INSERT INTO server_stats (server_name, player_count, max_players) VALUES (?, ?, ?)",
            (server_name, player_count, max_players)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error recording stats: {e}")

def get_server_stats(server_name: str, hours: int = 24) -> dict:
    """Get server stats for the last N hours"""
    try:
        conn = sqlite3.connect(STATS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        c.execute(
            "SELECT * FROM server_stats WHERE server_name = ? AND timestamp > ? ORDER BY timestamp",
            (server_name, cutoff_time.isoformat())
        )
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return {"error": "No data found"}
        
        player_counts = [row["player_count"] for row in rows]
        return {
            "current": player_counts[-1],
            "avg": round(sum(player_counts) / len(player_counts), 1),
            "peak": max(player_counts),
            "low": min(player_counts),
            "datapoints": len(player_counts)
        }
    except Exception as e:
        print(f"Error retrieving stats: {e}")
        return {"error": str(e)}

def get_peak_hours(server_name: str, days: int = 7) -> dict:
    """Analyze peak hours for a server"""
    try:
        conn = sqlite3.connect(STATS_DB)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        c.execute(
            "SELECT * FROM server_stats WHERE server_name = ? AND timestamp > ? ORDER BY timestamp",
            (server_name, cutoff_time.isoformat())
        )
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return {"error": "No data found"}
        
        # Group by hour of day
        hour_data = {hour: [] for hour in range(24)}
        for row in rows:
            ts = datetime.fromisoformat(row["timestamp"])
            hour = ts.hour
            hour_data[hour].append(row["player_count"])
        
        # Calculate averages per hour
        hour_avg = {}
        for hour, counts in hour_data.items():
            if counts:
                hour_avg[hour] = round(sum(counts) / len(counts), 1)
        
        if not hour_avg:
            return {"error": "No data found"}
        
        # Find peak hour
        peak_hour = max(hour_avg, key=hour_avg.get)
        peak_players = hour_avg[peak_hour]
        
        # Get top 3 hours
        top_3 = sorted(hour_avg.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "peak_hour": peak_hour,
            "peak_players": peak_players,
            "top_3": top_3,
            "all_hours": hour_avg
        }
    except Exception as e:
        print(f"Error retrieving peak hours: {e}")
        return {"error": str(e)}

def load_favorites_data():
    if not os.path.exists(FAVORITES_FILE):
        return {}
    try:
        with open(FAVORITES_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_favorites_data(data):
    with open(FAVORITES_FILE, "w") as f:
        json.dump(data, f, indent=4)

def update_user_favorites(user_id, server_number, action="add"):
    data = load_favorites_data()
    user_key = str(user_id)
    if user_key not in data:
        data[user_key] = []
    
    if action == "add":
        if server_number not in data[user_key]:
            data[user_key].append(server_number)
            save_favorites_data(data)
            return True
        return False 
    elif action == "remove":
        if server_number in data[user_key]:
            data[user_key].remove(server_number)
            if not data[user_key]: del data[user_key]
            save_favorites_data(data)
            return True
        return False 

def fetch_xp_multiplier():
    try:
        response = requests.get("https://cdn2.arkdedicated.com/asa/dynamicconfig.ini", timeout=10)
        response.raise_for_status()
        data = response.text
        for line in data.splitlines():
            if "XPMultiplier" in line:
                key, value = line.split('=', 1)
                return value.strip()
        return None 
    except Exception as e:
        print(f"Error fetching rates: {e}")
        return None

def create_monitor_embed(server):
    player_count = server.get("NumPlayers", 0)
    status_color = discord.Color.green() if player_count < 40 else discord.Color.red()
    status_emoji = "🟢" if player_count < 70 else "🔴"
    
    embed = discord.Embed(
        title=f"{status_emoji} {server.get('Name')} | Live Monitor",
        description=f"**IP:** `{server.get('IP')}:{server.get('Port')}`",
        color=status_color
    )
    
    embed.add_field(name="🗺️ Map", value=f"```{server.get('MapName', 'Unknown')}```", inline=True)
    embed.add_field(name="👥 Players", value=f"```{server.get('NumPlayers')}/{server.get('MaxPlayers', 70)}```", inline=True)
    embed.add_field(name="📆 Day", value=f"```{server.get('DayTime', 'Unknown')}```", inline=True)
    
    embed.set_footer(text=f"Last Updated: {datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC | Updates every 60s")
    return embed

async def server_autocomplete(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    if not CACHED_SERVERS:
        return []
    matches = [
        app_commands.Choice(name=s['Name'], value=s['Name'])
        for s in CACHED_SERVERS 
        if current.lower() in s['Name'].lower()
    ]
    return matches[:25]

# =========================================
# THE COG CLASS
# =========================================

class ARKCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.LAST_KNOWN_RATES = None
        
        # Initialize Database
        init_stats_db()
        print("✅ [ARKCog] Database Initialized")
        
        # Start Background Tasks
        self.update_server_cache.start()
        self.update_dashboards.start()
        self.check_evo_event.start()

    def cog_unload(self):
        """Clean up tasks when cog is unloaded"""
        self.update_server_cache.cancel()
        self.update_dashboards.cancel()
        self.check_evo_event.cancel()

    # --- TASKS ---

    @tasks.loop(seconds=60)
    async def update_server_cache(self):
        global CACHED_SERVERS
        try:
            url = "https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                CACHED_SERVERS = response.json()
            else:
                print("Failed to fetch ARK API during cache update.")
        except Exception as e:
            print(f"Error fetching ARK API: {e}")

    @tasks.loop(seconds=60)
    async def update_dashboards(self):
        global monitored_servers, CACHED_SERVERS
        if not monitored_servers or not CACHED_SERVERS:
            return

        for srv_num, info in list(monitored_servers.items()):
            try:
                new_data = next((s for s in CACHED_SERVERS if srv_num in s.get("Name", "")), None)

                if new_data:
                    new_embed = create_monitor_embed(new_data)
                    channel = self.bot.get_channel(info["channel_id"])
                    
                    if channel:
                        try:
                            message = await channel.fetch_message(info["message_id"])
                            await message.edit(embed=new_embed)
                            
                            current_players = new_data.get("NumPlayers", 0)
                            max_players = new_data.get("MaxPlayers", 70)
                            
                            record_server_stats(srv_num, current_players, max_players)
                            
                            if current_players > ALERT_THRESHOLD and not info.get("alert_sent", False):
                                await channel.send(f"<@&{ARK_ROLE_ID}> 🚨 **ALERT:** Player count on **{srv_num}** is high! ({current_players} Players)")
                                monitored_servers[srv_num]["alert_sent"] = True
                            elif current_players <= ALERT_THRESHOLD:
                                monitored_servers[srv_num]["alert_sent"] = False
                                
                        except discord.NotFound:
                            del monitored_servers[srv_num]
                        except Exception as e:
                            print(f"Failed to edit message for {srv_num}: {e}")

                    vc_id = info.get("vc_id")
                    last_update = info.get("last_vc_update")
                    now = datetime.now(timezone.utc)

                    if vc_id and (now - last_update).total_seconds() > 360: 
                        vc_channel = self.bot.get_channel(vc_id)
                        if vc_channel:
                            try:
                                new_name = f"🔊 ASA #{srv_num}: {current_players}/{max_players}"
                                if vc_channel.name != new_name:
                                    await vc_channel.edit(name=new_name)
                                    monitored_servers[srv_num]["last_vc_update"] = now
                            except Exception as e:
                                print(f"Failed to update VC name for {srv_num}: {e}")

            except Exception as e:
                print(f"Error processing server {srv_num}: {e}")

    @tasks.loop(minutes=10)
    async def check_evo_event(self):
        current_rate = fetch_xp_multiplier()
        
        if not current_rate:
            return

        if self.LAST_KNOWN_RATES is None:
            self.LAST_KNOWN_RATES = current_rate
            print(f"Initialized EVO Monitor. Current rates: {current_rate}x")
            return

        if current_rate != self.LAST_KNOWN_RATES:
            channel = self.bot.get_channel(TARGET_CHANNEL_ID)
            if channel:
                try:
                    old_val = float(self.LAST_KNOWN_RATES)
                    new_val = float(current_rate)
                    if new_val > old_val:
                        msg = f"🦖 <@&{ARK_ROLE_ID}> **EVO EVENT STARTED!** Rates increased from **{old_val}x** to **{new_val}x**! Go farm!"
                    else:
                        msg = f"📉 **EVO Event Ended.** Rates returned to **{new_val}x**."
                except:
                    msg = f"⚠️ <@&{ARK_ROLE_ID}> **Server Rates Changed!** New Rate: **{current_rate}** (Was: {self.LAST_KNOWN_RATES})"

                await channel.send(msg)
            self.LAST_KNOWN_RATES = current_rate

    # =========================================
    # SLASH COMMANDS
    # =========================================

    @app_commands.command(name="server", description="Check the status of an official ASA server")
    @app_commands.describe(server_name="Type part of the server name (e.g. 2154)")
    @app_commands.autocomplete(server_name=server_autocomplete) 
    async def server(self, interaction: discord.Interaction, server_name: str):
        if interaction.channel_id != TARGET_CHANNEL_ID:
            await interaction.response.send_message(f"Please use the correct channel: <#{TARGET_CHANNEL_ID}>", ephemeral=True)
            return
        
        await interaction.response.defer(thinking=True)
        matched_server = next((s for s in CACHED_SERVERS if server_name == s['Name']), None)
        
        if not matched_server:
            await interaction.followup.send(f"No server found matching `{server_name}`.")
            return

        xp_multiplier = fetch_xp_multiplier()
        embed = discord.Embed(title="Official Server | Made by pwnedByJT", color=discord.Color.from_rgb(0, 255, 0))
        embed.add_field(name="Server Name", value=f"```{matched_server['Name']}```", inline=False)
        embed.add_field(name="Players Online", value=f"```{matched_server.get('NumPlayers', 'N/A')}```", inline=True)
        embed.add_field(name="Map", value=f"```{matched_server.get('MapName', 'Unknown')}```", inline=True)
        if 'DayTime' in matched_server:
            embed.add_field(name="Day", value=f"```{matched_server['DayTime']}```", inline=True)
        embed.add_field(name="IP", value=f"```{matched_server.get('IP', 'Unknown')}```", inline=True)
        embed.add_field(name="Port", value=f"```{matched_server.get('Port', 'N/A')}```", inline=True)
        if xp_multiplier:
            embed.add_field(name="Server Rates", value=f"```{xp_multiplier}```", inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="monitor", description="Create a live updating dashboard & voice counter")
    @app_commands.describe(server_number="The number of the server to monitor (e.g. 2154)")
    @app_commands.autocomplete(server_number=server_autocomplete) 
    async def monitor(self, interaction: discord.Interaction, server_number: str):
        if interaction.channel_id != TARGET_CHANNEL_ID:
            await interaction.response.send_message(f"Please use the correct channel: <#{TARGET_CHANNEL_ID}>", ephemeral=True)
            return

        await interaction.response.defer()
        target_server = next((s for s in CACHED_SERVERS if server_number in s['Name']), None)
        
        if not target_server:
            await interaction.followup.send(f"❌ Server matching `{server_number}` not found.", ephemeral=True)
            return

        embed = create_monitor_embed(target_server)
        msg = await interaction.followup.send(embed=embed)

        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="[ Ark ]") or interaction.channel.category

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True),
            guild.me: discord.PermissionOverwrite(connect=True, manage_channels=True)
        }
        vc_name = f"🔊 ASA #{server_number}: {target_server.get('NumPlayers')}/{target_server.get('MaxPlayers', 70)}"
        
        try:
            vc_channel = await guild.create_voice_channel(name=vc_name, category=category, overwrites=overwrites)
            vc_id = vc_channel.id
        except:
            vc_id = None

        monitored_servers[server_number] = {
            "message_id": msg.id,
            "channel_id": interaction.channel_id,
            "vc_id": vc_id,
            "last_vc_update": datetime.now(timezone.utc),
            "alert_sent": False 
        }
        
        if not self.update_dashboards.is_running():
            self.update_dashboards.start()

        await interaction.followup.send(f"✅ Monitor active for **{target_server['Name']}**.", ephemeral=True)

    @app_commands.command(name="stopmonitor", description="Stop monitoring a server")
    @app_commands.autocomplete(server_number=server_autocomplete) 
    async def stopmonitor(self, interaction: discord.Interaction, server_number: str):
        if interaction.channel_id != TARGET_CHANNEL_ID:
            await interaction.response.send_message(f"Please use the correct channel: <#{TARGET_CHANNEL_ID}>", ephemeral=True)
            return

        key_to_delete = next((k for k in monitored_servers if k in server_number), None)
        
        if not key_to_delete:
            await interaction.response.send_message(f"❌ Server **{server_number}** is not being monitored.", ephemeral=True)
            return

        server_info = monitored_servers[key_to_delete]
        if server_info.get("vc_id"):
            vc_channel = self.bot.get_channel(server_info["vc_id"])
            if vc_channel:
                try: await vc_channel.delete()
                except: pass 

        channel = self.bot.get_channel(server_info["channel_id"])
        if channel:
            try:
                msg = await channel.fetch_message(server_info["message_id"])
                await msg.delete()
            except: pass 

        del monitored_servers[key_to_delete]
        await interaction.response.send_message(f"🛑 Monitoring stopped for **{key_to_delete}**.", ephemeral=True)

    @app_commands.command(name="fav_add", description="Add a server to your favorites list")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def fav_add(self, interaction: discord.Interaction, server_number: str):
        await interaction.response.defer(ephemeral=True)
        exists = next((s for s in CACHED_SERVERS if server_number in s['Name']), None)

        if not exists:
            await interaction.followup.send(f"❌ Could not find server matching `{server_number}`.")
            return

        if update_user_favorites(interaction.user.id, server_number, "add"):
            await interaction.followup.send(f"⭐ Added **{server_number}** to your favorites!")
        else:
            await interaction.followup.send(f"⚠️ **{server_number}** is already in your favorites.")

    @app_commands.command(name="fav_remove", description="Remove a server from your favorites")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def fav_remove(self, interaction: discord.Interaction, server_number: str):
        if update_user_favorites(interaction.user.id, server_number, "remove"):
            await interaction.response.send_message(f"🗑️ Removed **{server_number}** from favorites.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ **{server_number}** was not in your list.", ephemeral=True)

    @app_commands.command(name="fav_list", description="View your favorite servers")
    async def fav_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = load_favorites_data()
        user_list = data.get(str(interaction.user.id), [])
        
        if not user_list:
            await interaction.followup.send("You have no favorites! Use `/fav_add`.", ephemeral=True)
            return

        embed = discord.Embed(title=f"⭐ {interaction.user.display_name}'s Favorites", color=discord.Color.gold())
        for fav_num in user_list:
            server_data = next((s for s in CACHED_SERVERS if fav_num in s['Name']), None)
            if server_data:
                status = "🟢" if server_data['NumPlayers'] < 70 else "🔴"
                embed.add_field(name=f"{status} {server_data['Name']}", value=f"👥 **{server_data['NumPlayers']}/70** | 🗺️ {server_data['MapName']}", inline=False)
            else:
                embed.add_field(name=f"❓ {fav_num}", value="*Offline/Not Found*", inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="topserver", description="Show the top 5 official ASA servers")
    async def topserver(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        sorted_servers = sorted(CACHED_SERVERS, key=lambda s: s.get('NumPlayers', 0), reverse=True)
        top_servers = sorted_servers[:5]
        
        embed = discord.Embed(title="Top 5 Official ASA Servers", color=discord.Color.blue())
        for idx, srv in enumerate(top_servers, start=1):
            embed.add_field(name=f"#{idx}: {srv.get('Name')}", value=f"**Players:** `{srv.get('NumPlayers')}`\n**Map:** `{srv.get('MapName')}`", inline=False)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="serverstats", description="View player history and stats for a server")
    @app_commands.describe(server_number="The server number to check stats for", hours="Hours of history (default 24)")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def serverstats(self, interaction: discord.Interaction, server_number: str, hours: int = 24):
        await interaction.response.defer()
        if hours < 1 or hours > 168:
            await interaction.followup.send("⚠️ Hours must be between 1 and 168.", ephemeral=True)
            return
        
        stats = get_server_stats(server_number, hours)
        if "error" in stats:
            await interaction.followup.send(f"❌ No data found for **{server_number}**.", ephemeral=True)
            return
        
        embed = discord.Embed(title=f"📊 Server Stats: {server_number}", color=discord.Color.blue())
        embed.add_field(name="📈 Current", value=f"```{stats['current']} players```", inline=True)
        embed.add_field(name="⏱️ Average", value=f"```{stats['avg']} players```", inline=True)
        embed.add_field(name="🔺 Peak", value=f"```{stats['peak']} players```", inline=True)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="peaktime", description="Show the busiest times for a server")
    @app_commands.describe(server_number="The server number to check peak times for", days="Days of history (default 7)")
    @app_commands.autocomplete(server_number=server_autocomplete)
    async def peaktime(self, interaction: discord.Interaction, server_number: str, days: int = 7):
        await interaction.response.defer()
        peak_data = get_peak_hours(server_number, days)
        
        if "error" in peak_data:
            await interaction.followup.send(f"❌ No data found for **{server_number}**.", ephemeral=True)
            return
        
        embed = discord.Embed(title=f"⏰ Peak Times: {server_number}", color=discord.Color.gold())
        embed.add_field(name="🔥 Busiest Hour", value=f"```{peak_data['peak_hour']:02d}:00 UTC\n{peak_data['peak_players']} avg players```", inline=False)
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    """Handshake that allows the master bot to load this module."""
    await bot.add_cog(ARKCog(bot))

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    TOKEN = os.getenv("DISCORD_TOKEN")

    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in .env file.")
        exit(1)

    class StandaloneBot(commands.Bot):
        async def setup_hook(self):
            await self.add_cog(ARKCog(self))
            await self.tree.sync()
            print("✅ Slash commands synced")

    # Initialize and run the bot
    bot = StandaloneBot(command_prefix="!", intents=discord.Intents.default())
    bot.run(TOKEN)