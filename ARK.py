"""
Program name: ARKintel.py
Description: Monitors Official ARK servers with Live Dashboards, Voice Channels, Favorites, Autocomplete, and Auto-EVO Alerts.
Author: Justin Aaron Turner
Updated: 3/13/2025
"""
import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
from dotenv import load_dotenv
import os
import random
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import List 

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    exit("DISCORD_TOKEN not found in the environment variables!")

# --- CONFIGURATION ---
TARGET_CHANNEL_ID = 1178760002186526780
ARK_ROLE_ID = 1364705580064706600
FAVORITES_FILE = "favorites.json"
# ---------------------

# --- GLOBAL VARIABLES ---
monitored_servers = {} 
CACHED_SERVERS = [] 
LAST_KNOWN_RATES = None # <--- New: Stores the last XP rate to detect changes

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

# =========================================
# HELPER FUNCTIONS
# =========================================

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
# TASKS (Loops)
# =========================================

# 1. Main Cache Loop
@tasks.loop(seconds=60)
async def update_server_cache():
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

# 2. Dashboard Update Loop
@tasks.loop(seconds=60)
async def update_dashboards():
    if not monitored_servers:
        return
    
    if not CACHED_SERVERS:
        return

    for srv_num, info in list(monitored_servers.items()):
        try:
            new_data = next((s for s in CACHED_SERVERS if srv_num in s.get("Name", "")), None)

            if new_data:
                new_embed = create_monitor_embed(new_data)
                channel = bot.get_channel(info["channel_id"])
                
                if channel:
                    try:
                        message = await channel.fetch_message(info["message_id"])
                        await message.edit(embed=new_embed)
                        
                        current_players = new_data.get("NumPlayers", 0)
                        max_players = new_data.get("MaxPlayers", 70)
                        
                        if current_players > 5 and not info.get("alert_sent", False):
                            await channel.send(f"<@&{ARK_ROLE_ID}> 🚨 **ALERT:** Player count on **{srv_num}** is high! ({current_players} Players)")
                            monitored_servers[srv_num]["alert_sent"] = True
                        elif current_players <= 5:
                            monitored_servers[srv_num]["alert_sent"] = False
                            
                    except discord.NotFound:
                        del monitored_servers[srv_num]
                    except Exception as e:
                        print(f"Failed to edit message for {srv_num}: {e}")

                vc_id = info.get("vc_id")
                last_update = info.get("last_vc_update")
                now = datetime.now(timezone.utc)

                if vc_id and (now - last_update).total_seconds() > 360: 
                    vc_channel = bot.get_channel(vc_id)
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

# 3. EVO Event Monitor (New!)
@tasks.loop(minutes=10)
async def check_evo_event():
    global LAST_KNOWN_RATES
    
    current_rate = fetch_xp_multiplier()
    
    # If API failed or returned nothing, skip
    if not current_rate:
        return

    # First run: Just save the value, don't ping
    if LAST_KNOWN_RATES is None:
        LAST_KNOWN_RATES = current_rate
        print(f"Initialized EVO Monitor. Current rates: {current_rate}x")
        return

    # Logic: If rates changed, ping the channel
    if current_rate != LAST_KNOWN_RATES:
        channel = bot.get_channel(TARGET_CHANNEL_ID)
        if channel:
            # Different emoji depending on if rates went UP or DOWN
            try:
                old_val = float(LAST_KNOWN_RATES)
                new_val = float(current_rate)
                if new_val > old_val:
                    msg = f"🦖 <@&{ARK_ROLE_ID}> **EVO EVENT STARTED!** Rates increased from **{old_val}x** to **{new_val}x**! Go farm!"
                else:
                    msg = f"📉 **EVO Event Ended.** Rates returned to **{new_val}x**."
            except:
                # Fallback if rates aren't numbers
                msg = f"⚠️ <@&{ARK_ROLE_ID}> **Server Rates Changed!** New Rate: **{current_rate}** (Was: {LAST_KNOWN_RATES})"

            await channel.send(msg)
        
        # Update memory
        LAST_KNOWN_RATES = current_rate

# =========================================
# SLASH COMMANDS
# =========================================

@bot.tree.command(name="server", description="Check the status of an official ASA server")
@app_commands.describe(server_name="Type part of the server name (e.g. 2154)")
@app_commands.autocomplete(server_name=server_autocomplete) 
async def server(interaction: discord.Interaction, server_name: str):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message(f"Please use the correct channel: <#{TARGET_CHANNEL_ID}>", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    matched_server = next((s for s in CACHED_SERVERS if server_name == s['Name']), None)
    
    if not matched_server:
        try:
            response = requests.get("https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json")
            servers = response.json()
            matched_server = next((s for s in servers if server_name in s['Name']), None)
        except:
            pass

    if not matched_server:
        await interaction.followup.send(f"No server found matching `{server_name}`.")
        return

    xp_multiplier = fetch_xp_multiplier()

    embed = discord.Embed(title="Official Server | Made by pwnedByJT", color=discord.Color(random.randint(0, 0xFFFFFF)))
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

@bot.tree.command(name="monitor", description="Create a live updating dashboard & voice counter")
@app_commands.describe(server_number="The number of the server to monitor (e.g. 2154)")
@app_commands.autocomplete(server_number=server_autocomplete) 
async def monitor(interaction: discord.Interaction, server_number: str):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message(f"Please use the correct channel: <#{TARGET_CHANNEL_ID}>", ephemeral=True)
        return

    await interaction.response.defer()

    target_server = next((s for s in CACHED_SERVERS if server_number in s['Name']), None)
    
    if not target_server:
        try:
            response = requests.get("https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json")
            servers = response.json()
            target_server = next((s for s in servers if server_number in s['Name']), None)
        except Exception as e:
            await interaction.followup.send(f"Error fetching data: {e}")
            return

    if not target_server:
        await interaction.followup.send(f"❌ Server matching `{server_number}` not found.", ephemeral=True)
        return

    embed = create_monitor_embed(target_server)
    msg = await interaction.followup.send(embed=embed)

    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="[ Ark ]")
    if not category:
        category = interaction.channel.category

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True),
        guild.me: discord.PermissionOverwrite(connect=True, manage_channels=True)
    }
    vc_name = f"🔊 ASA #{server_number}: {target_server.get('NumPlayers')}/{target_server.get('MaxPlayers', 70)}"
    
    try:
        vc_channel = await guild.create_voice_channel(name=vc_name, category=category, overwrites=overwrites)
        vc_id = vc_channel.id
    except Exception as e:
        await interaction.followup.send(f"⚠️ Dashboard created, but Voice Channel failed: {e}")
        vc_id = None

    monitored_servers[server_number] = {
        "message_id": msg.id,
        "channel_id": interaction.channel_id,
        "vc_id": vc_id,
        "last_vc_update": datetime.now(timezone.utc),
        "alert_sent": False 
    }
    
    if not update_dashboards.is_running():
        update_dashboards.start()

    await interaction.followup.send(f"✅ Monitor active for **{target_server['Name']}**.", ephemeral=True)

@bot.tree.command(name="stopmonitor", description="Stop monitoring a server")
@app_commands.autocomplete(server_number=server_autocomplete) 
async def stopmonitor(interaction: discord.Interaction, server_number: str):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message(f"Please use the correct channel: <#{TARGET_CHANNEL_ID}>", ephemeral=True)
        return

    key_to_delete = None
    if server_number in monitored_servers:
        key_to_delete = server_number
    else:
        for key in monitored_servers:
            if key in server_number: 
                key_to_delete = key
                break
    
    if not key_to_delete:
        await interaction.response.send_message(f"❌ Server **{server_number}** is not currently being monitored.", ephemeral=True)
        return

    server_info = monitored_servers[key_to_delete]
    
    if server_info.get("vc_id"):
        vc_channel = bot.get_channel(server_info["vc_id"])
        if vc_channel:
            try: await vc_channel.delete()
            except: pass 

    channel = bot.get_channel(server_info["channel_id"])
    if channel:
        try:
            msg = await channel.fetch_message(server_info["message_id"])
            await msg.delete()
        except: pass 

    del monitored_servers[key_to_delete]
    await interaction.response.send_message(f"🛑 Monitoring stopped for **{key_to_delete}**.", ephemeral=True)

@bot.tree.command(name="fav_add", description="Add a server to your favorites list")
@app_commands.autocomplete(server_number=server_autocomplete)
async def fav_add(interaction: discord.Interaction, server_number: str):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message(f"Wrong channel: <#{TARGET_CHANNEL_ID}>", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    
    exists = next((s for s in CACHED_SERVERS if server_number in s['Name']), None)
    if not exists:
        try:
            response = requests.get("https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json")
            servers = response.json()
            exists = next((s for s in servers if server_number in s['Name']), None)
        except: pass

    if not exists:
        await interaction.followup.send(f"❌ Could not find server matching `{server_number}`.")
        return

    if update_user_favorites(interaction.user.id, server_number, "add"):
        await interaction.followup.send(f"⭐ Added **{server_number}** to your favorites!")
    else:
        await interaction.followup.send(f"⚠️ **{server_number}** is already in your favorites.")

@bot.tree.command(name="fav_remove", description="Remove a server from your favorites")
@app_commands.autocomplete(server_number=server_autocomplete)
async def fav_remove(interaction: discord.Interaction, server_number: str):
    if update_user_favorites(interaction.user.id, server_number, "remove"):
        await interaction.response.send_message(f"🗑️ Removed **{server_number}** from favorites.", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ **{server_number}** was not in your list.", ephemeral=True)

@bot.tree.command(name="fav_list", description="View your favorite servers")
async def fav_list(interaction: discord.Interaction):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message(f"Wrong channel: <#{TARGET_CHANNEL_ID}>", ephemeral=True)
        return

    await interaction.response.defer()
    
    data = load_favorites_data()
    user_list = data.get(str(interaction.user.id), [])
    
    if not user_list:
        await interaction.followup.send("You have no favorites! Use `/fav_add`.", ephemeral=True)
        return

    source_list = CACHED_SERVERS if CACHED_SERVERS else requests.get("https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json").json()

    embed = discord.Embed(title=f"⭐ {interaction.user.display_name}'s Favorites", color=discord.Color.gold())
    
    found_count = 0
    for fav_num in user_list:
        server_data = next((s for s in source_list if fav_num in s['Name']), None)
        
        if server_data:
            found_count += 1
            status = "🟢" if server_data['NumPlayers'] < 70 else "🔴"
            embed.add_field(
                name=f"{status} {server_data['Name']}",
                value=f"👥 **{server_data['NumPlayers']}/70** | 🗺️ {server_data['MapName']}",
                inline=False
            )
        else:
            embed.add_field(name=f"❓ {fav_num}", value="*Offline/Not Found*", inline=False)
    
    embed.set_footer(text=f"Showing {found_count}/{len(user_list)} servers")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="topserver", description="Show the top 5 official ASA servers")
async def topserver(interaction: discord.Interaction):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message(f"Wrong channel: <#{TARGET_CHANNEL_ID}>", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    
    source_list = CACHED_SERVERS if CACHED_SERVERS else requests.get("https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json").json()

    sorted_servers = sorted(source_list, key=lambda s: s.get('NumPlayers', 0), reverse=True)
    top_servers = sorted_servers[:5]
    
    embed = discord.Embed(title="Top 5 Official ASA Servers by Player Count", color=discord.Color(random.randint(0, 0xFFFFFF)))
    for idx, server in enumerate(top_servers, start=1):
        name = server.get("Name", "Unknown")
        players = server.get("NumPlayers", "N/A")
        map_name = server.get("MapName", "Unknown")
        embed.add_field(name=f"#{idx}: {name}", value=(f"**Players:** `{players}`\n**Map:** `{map_name}`"), inline=False)
    
    embed.set_footer(text="Made by pwnedByJT")
    await interaction.followup.send(embed=embed)

@bot.command()
async def sync(ctx):
    bot.tree.copy_global_to(guild=ctx.guild)
    await bot.tree.sync(guild=ctx.guild)
    await ctx.send(f"✅ Synced commands to **{ctx.guild.name}**!")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    if not update_server_cache.is_running():
        update_server_cache.start()
        print("✅ Server Cache Loop Started")
        
    if not update_dashboards.is_running():
        update_dashboards.start()
        print("✅ Dashboard Monitor Loop Started")

    if not check_evo_event.is_running():
        check_evo_event.start()
        print("✅ Auto-EVO Monitor Started")

bot.run(TOKEN)