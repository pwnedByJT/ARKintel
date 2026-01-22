# 🦖 ARKintel

**A Discord bot that delivers real-time ARK: Survival Ascended server data.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Discord.py](https://img.shields.io/badge/discord.py-2.3.2-blue?logo=discord)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

---

## 📖 Overview

**ARKintel** is a Discord bot designed for **ARK: Survival Ascended** players who want to easily check **official server stats** right from Discord.
By using simple **slash commands**, users can:

* 🔍 Search for any official ASA server by number or name.
* 📊 View live server data (map, player count, IP, and platform).
* 🏆 See the top 5 most populated official servers in real time.

All data is pulled directly from **ARK’s official APIs**, ensuring accurate and up-to-date information for your tribe or community.

---

## ✨ Features

✅ `/server [number]` — Fetches details for a specific official server.
✅ `/topserver` — Displays the top 5 official servers sorted by player count.
✅ **Channel-Locked** — Commands are restricted to a specific channel to prevent spam.
✅ Real-time player, map, and rate information.
✅ Pulls live multipliers like **XP rates** from ARK’s dynamic config.
✅ Clean, Discord-embedded responses.
✅ Built using modern slash commands (no `!prefix` required).

---

## 🧠 Example Commands

### 🔹 `/server 1123`

> Returns information about the official server containing “1123” in its name, including map, IP, player count, and current rates.

### 🔹 `/topserver`

> Lists the five official ASA servers with the highest active player counts.

---

## 🛠️ Setup & Installation

### 1. Clone the repository

```bash
git clone [https://github.com/pwnedByJT/ARKintel.git](https://github.com/pwnedByJT/ARKintel.git)
cd ARKintel

```

### 2. Install dependencies

```bash
pip install -r requirements.txt

```

### 3. Set up your `.env` file

Create a file named `.env` in the project directory and add your Discord bot token:

```
DISCORD_TOKEN=your_discord_bot_token_here

```

### 4. Configure the Channel ID

Open `ARKintel.py` and look for the configuration section near the top:

```python
# --- CONFIGURATION ---
TARGET_CHANNEL_ID = 1178760002186526780  # <-- Replace with your Discord Channel ID
# ---------------------

```

Replace the number with the ID of the channel where you want the bot to be active.

### 5. Run the bot

```bash
python ARKintel.py

```

---

## 🔑 Permissions Required

When inviting your bot to your server, make sure it has:

* **Use Slash Commands**
* **Send Messages**
* **Embed Links**
* **Read Message History**

---

## 📡 Data Sources

* **Server List:** [cdn2.arkdedicated.com/servers/asa/officialserverlist.json](https://cdn2.arkdedicated.com/servers/asa/officialserverlist.json)
* **Dynamic Config:** [cdn2.arkdedicated.com/asa/dynamicconfig.ini](https://cdn2.arkdedicated.com/asa/dynamicconfig.ini)

All data is provided by **Studio Wildcard’s official infrastructure**.

---

## 👑 Author

**Developed by:** Justin Aaron Turner *(pwnedByJT)*

* 🌐 [Twitch](https://www.google.com/search?q=https://twitch.tv/pwnedByJT)
* 🐦 [Twitter](https://www.google.com/search?q=https://twitter.com/pwnedByJT)
* 💬 Discord: `pwnedByJT`

---

## 📜 License

This project is licensed under the **MIT License**

---

## 🚀 Future Plans

* Add `/searchmap` command to filter servers by map.
* Add uptime and ping data via BattleMetrics API.
* Create a web dashboard version using Flask or Next.js.

---
