"""
Program name: ARKintel.py

This script enables users to check the status of official 
ARK servers by entering a server number through Discord slash commands.

Author: Justin Aaron Turner
Creation Date: 3/13/2025
"""

import discord
from discord.ext import commands
from discord import app_commands
import requests
from dotenv import load_dotenv
import os
import random

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Exit if the token isn't found
if not TOKEN:
    exit("DISCORD_TOKEN not found in the environment variables!")

# Set up bot intents (permissions), enabling reading message content
intents = discord.Intents.default()
intents.message_content = True

# Define a custom bot class
class MyBot(commands.Bot):
    def __init__(self):
        # Use mentions as the command prefix
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self):
        # Sync slash commands with Discord
        await self.tree.sync()

# Create an instance of the bot
bot = MyBot()

# Helper function to format platforms like 'Steam+Xbox' into bolded text
def format_platforms(platform_str):
    return " ".join(f"**{p.strip()}**" for p in platform_str.split("+"))

# Fetch the XP multiplier from ASA's dynamic server config
def fetch_xp_multiplier():
    try:
        response = requests.get("https://cdn2.arkdedicated.com/asa/dynamicconfig.ini")
        response.raise_for_status()
        data = response.text

        # Search line-by-line for "XPMultiplier"
        for line in data.splitlines():
            if "XPMultiplier" in line:
                key, value = line.split('=', 1)
                return value.strip()

        return None  # Return None if not found

    except Exception as e:
        return None  # Handle errors silently

# Slash command to get details about a specific official ASA server
@bot.tree.command(name="server", description="Check the status of an official ASA server by its number")
@app_commands.describe(server_number="The number or part of the server name to search for")
async def server(interaction: discord.Interaction, server_number: str):
    await interaction.response.defer(thinking=True)  # Let user know we're working on it

    try:
        # Fetch the official ASA server list
        response = requests.get("https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json")
        response.raise_for_status()
        servers = response.json()

        # Try to find a server that matches the given number/name
        matched_server = next((s for s in servers if server_number in s['Name']), None)

        if not matched_server:
            await interaction.followup.send(f"No server found matching `{server_number}`.")
            return

        # Get the current XP multiplier
        xp_multiplier = fetch_xp_multiplier()

        # Create an embed to display server info
        embed = discord.Embed(
            title="Official Server | Made by King Hittz",
            color=discord.Color(random.randint(0, 0xFFFFFF))  # Random embed color
        )
        embed.add_field(name="Server Name", value=f"```{matched_server['Name']}```", inline=False)
        embed.add_field(name="Players Online", value=f"```{matched_server.get('NumPlayers', 'N/A')}```", inline=True)
        embed.add_field(name="Map", value=f"```{matched_server.get('MapName', 'Unknown')}```", inline=True)

        # Include daytime info if available
        if 'DayTime' in matched_server:
            embed.add_field(name="Day", value=f"```{matched_server['DayTime']}```", inline=True)

        # Add IP and Port
        embed.add_field(name="IP", value=f"```{matched_server.get('IP', 'Unknown')}```", inline=True)
        embed.add_field(name="Port", value=f"```{matched_server.get('Port', 'N/A')}```", inline=True)

        # Add the XP multiplier if it was fetched
        if xp_multiplier:
            embed.add_field(name="Server Rates", value=f"```{xp_multiplier}```", inline=False)

        # Display the platform(s) at the bottom
        platform_display = format_platforms(matched_server.get("PlatformType", "Unknown"))
        embed.add_field(name="Platforms", value=platform_display or "Unknown", inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error fetching server stats: {e}")

# Slash command to display the top 5 servers based on player count
@bot.tree.command(name="topserver", description="Show the top 5 official ASA servers by player count")
async def topserver(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)  # Let user know we're processing

    try:
        # Fetch the list of all official ASA servers
        response = requests.get("https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json")
        response.raise_for_status()
        servers = response.json()

        # Sort the list by NumPlayers in descending order
        sorted_servers = sorted(
            servers,
            key=lambda s: s.get('NumPlayers', 0),
            reverse=True
        )

        # Get the top 5 servers
        top_servers = sorted_servers[:5]

        # Create an embed to show the top servers
        embed = discord.Embed(
            title="Top 5 Official ASA Servers by Player Count",
            color=discord.Color(random.randint(0, 0xFFFFFF))
        )

        # Add server details to the embed
        for idx, server in enumerate(top_servers, start=1):
            name = server.get("Name", "Unknown")
            players = server.get("NumPlayers", "N/A")
            map_name = server.get("MapName", "Unknown")
            platform = format_platforms(server.get("PlatformType", "Unknown"))
            embed.add_field(
                name=f"#{idx}: {name}",
                value=(f"**Players:** `{players}`\n"
                       f"**Map:** `{map_name}`\n"
                       f"**Platform:** {platform}"),
                inline=False
            )

        embed.set_footer(text="Made by King Hittz")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f"Error fetching top servers: {e}")

# Start the bot using the token from environment variables
bot.run(TOKEN)
