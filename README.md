This update documents the **Live Monitor**, **Voice Channels**, **Favorites System**, **Auto-EVO Alerts**, and **Autocomplete** features we just built.

Copy the code below and replace your `README.md` file content with it.

```markdown
# 🦖 ARKintel

**A Discord bot that delivers real-time ARK: Survival Ascended server data with live monitoring and alerts.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Discord.py](https://img.shields.io/badge/discord.py-2.3.2-blue?logo=discord)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

---

## 📖 Overview

**ARKintel** is a feature-rich Discord bot designed for **ARK: Survival Ascended** players. Beyond just checking stats, it turns your Discord into a live command center for Official servers.

It features **Live Dashboards** that update every minute, **Voice Channel Counters** for quick checking, **Personal Favorites lists**, and **Automatic Alerts** when EVO events start or server rates change.

---

## ✨ Features

### 🖥️ Live Monitoring
✅ **/monitor [server]** — Creates a **Live Dashboard** message that updates every 60 seconds.
✅ **Voice Counters** — Automatically creates a locked Voice Channel (e.g., `🔊 ASA #2154: 45/70`) that updates with the server population.
✅ **Admin Controls** — Monitor commands are restricted to Admins/Mods to prevent spam.

### ⭐ Personalization & Utilities
✅ **Favorites System** — Users can save servers to their personal list (`/fav_add`) for quick access.
✅ **Smart Autocomplete** — No need to memorize IDs! Type "21" and pick from a list of matching servers.
✅ **Auto-EVO Alerts** — The bot automatically pings a role when **Official Server Rates** (XP, Harvest, etc.) change.

### 📊 Core Data
✅ **/server** — Fetches detailed stats (IP, Map, Day, Pop) for any official server.
✅ **/topserver** — Displays the top 5 most populated servers globally.
✅ **Real-Time Data** — Pulls directly from Studio Wildcard's API.

---

## 🧠 Commands List

### 🛠️ Admin / Monitoring
* `/monitor [server]` — Starts a live dashboard & voice counter for a server.
* `/stopmonitor [server]` — Stops tracking a server and cleans up the channels.

### ⭐ Favorites
* `/fav_add [server]` — Save a server to your personal favorites.
* `/fav_list` — View a clean summary of all your favorite servers.
* `/fav_remove [server]` — Remove a server from your list.

### 🔍 General
* `/server [name/number]` — Lookup stats for a specific server.
* `/topserver` — Show the top 5 highest population servers.

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

```ini
DISCORD_TOKEN=your_discord_bot_token_here

```

### 4. Configure IDs

Open `ARK.py` and look for the configuration section near the top. You must set these for the bot to work:

```python
# --- CONFIGURATION ---
TARGET_CHANNEL_ID = 1178760002186526780  # Channel where commands are allowed
ARK_ROLE_ID = 1364705580064706600        # Role to ping for Alerts (e.g. @Ark)
# ---------------------

```

### 5. Run the bot

```bash
python ARK.py

```

---

## 🔑 Permissions Required

For the **Live Monitor** and **Voice Channels** to work, the bot needs these permissions in your Discord server:

* **Manage Channels** (Critical for creating/renaming the Voice Counters)
* **View Channels**
* **Send Messages**
* **Embed Links**
* **Use Slash Commands**

---

## 📡 Data Sources

* **Server List:** `cdn2.arkdedicated.com/servers/asa/officialserverlist.json`
* **Dynamic Config:** `cdn2.arkdedicated.com/asa/dynamicconfig.ini`

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

```

```