# 🦖 ARKintel

**The alpha-tier Discord intel bot for ARK: Survival Ascended — live server monitoring, raid calculators, boss checklists, tame guides, and more. All in one slash command.**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Discord.py](https://img.shields.io/badge/discord.py-2.3.2-blue?logo=discord)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)
![Game](https://img.shields.io/badge/game-ARK%3A%20Survival%20Ascended-orange)

---

## 📖 What is ARKintel?

**ARKintel** is a full-featured Discord bot built for serious ARK: Survival Ascended players. Whether you're a solo survivor or a mega-tribe running Official, ARKintel turns your Discord server into a real-time command center.

Stop alt-tabbing. Stop Googling recipes. Stop guessing how many C4 you need. **Just slash it.**

---

## ✨ Full Feature Set

### 📡 Live Server Monitoring
- **Live Dashboards** — Auto-updating embed messages that refresh every 60 seconds
- **Voice Channel Counters** — Locked voice channels (e.g. `🔊 ASA #2154: 45/70`) that update in real-time
- **Historical Population Analytics** — See population trends over the last 24h or longer
- **Auto EVO Alerts** — Bot pings a role the moment Official rates change (XP, Harvest, Taming, etc.)
- **One-Time Snapshots** — Quick population check without persistent monitoring

### 🦖 Tame Intelligence
- **Endgame Leveling Guides** — Exactly where to dump your 88 domestic points per tame
- **Multiple Build Variants** — Sky Freighter, Mobile Raid FOB, and more named builds per creature
- **Key Caps & Thresholds** — Weight caps, damage thresholds, and what actually matters
- **Tribe Pro-Tips** — Meta-optimized PvP and PvE tips for each creature

### ⏰ Imprint Timers
- **Hatch/Cuddle Alerts** — Set a timer in `HH:MM` and get pinged when the window opens
- **5-Minute Warning** — Pre-alert so you have time to get to the baby
- **Role Pings** — Optionally ping your tribe role instead of just yourself
- **One-Per-User** — Starting a new timer auto-cancels your previous one

### 💣 Raid Calculator
- **Explosive Requirements** — Exact C4, RPG, and Grenade counts to destroy any structure
- **Raw Material Costs** — Calculates everything you need to craft those explosives
- **Bulk Calculations** — Calculate for up to 500 structures at once
- **Wide Structure Support** — Metal Wall, Tek Wall, Vault, Heavy Turret, Tek Generator, Behemoth Gate, and more

### 🏺 Boss Preparation
- **Entry Checklists** — Artifacts, apex tributes, army composition, saddle armor floors, and HP thresholds
- **All 3 Island Bosses** — Dragon, Broodmother, Megapithecus
- **All 3 Tiers** — Gamma, Beta, and Alpha difficulties with tier-appropriate requirements
- **Wipe Risk Warnings** — Common mistakes that get tribes wiped, flagged before you go in

### 🧪 Consumables & Crafting
- **Endgame Recipe Lookup** — Ingredients, effects, spoil notes, and crafting station for every meta consumable
- **Supported Items:** Veggie Cake, Mindwipe Tonic, Shadow Steak Saute, Medical Brew, Focal Chili, Battle Tartare

### ⚙️ Utilities
- **Console Optimization String** — One-click copy-paste command to max your competitive visibility (kills shadows, foliage, fog, and bloom)
- **Personal Favorites** — Save and track your favorite servers
- **Smart Autocomplete** — Type "21" and pick from matching servers. Type "giga" and get the Giganotosaurus. No ID memorization.

---

## 🧠 Commands Reference

### 🦖 Tame Intelligence
| Command | Description |
|---|---|
| `/tame-stats tame:<name>` | Endgame leveling guide — where to allocate 88 domestic pts. Supports aliases: giga, theri, carcha, daed, paracer, dunk... |
| `/imprint creature:<name> time_remaining:<HH:MM> [ping_role:<role>]` | Hatch/cuddle timer with 5-min warning + window-open ping |
| `/imprint-cancel` | Cancel your active imprint timer |

### 🧪 Consumables & Crafting
| Command | Description |
|---|---|
| `/recipe item:<name>` | Ingredients, effects, and spoil notes for endgame consumables |

### 💣 Raid Operations
| Command | Description |
|---|---|
| `/raid-calc structure:<name> [quantity:<int>]` | Exact explosive counts + raw material costs. Default qty: 1, max: 500 |

### 🏺 Boss Preparation
| Command | Description |
|---|---|
| `/boss-check boss:<name> tier:<Gamma\|Beta\|Alpha>` | Full entry checklist — artifacts, tributes, army, thresholds, wipe risks |

### 📡 Server Monitoring
| Command | Description |
|---|---|
| `/monitor server_number:<name>` | Start a live dashboard + voice counter (auto-updates every 60s) |
| `/serverpop server_number:<name>` | One-time server population snapshot |
| `/stopmonitor server_number:<name>` | Stop tracking a server and remove its voice counter |
| `/serverstats server_number:<name> [hours:<int>]` | Historical population analytics (default: last 24 hours) |

### ⭐ Favorites & Utilities
| Command | Description |
|---|---|
| `/fav_add server_number:<name>` | Save a server to your personal favorites list |
| `/fav_list` | View all saved favorites with live status |
| `/fav_remove server_number:<name>` | Remove a server from your favorites |
| `/console` | Copy-paste console optimization command string for ASA |

### ℹ️ Help
| Command | Description |
|---|---|
| `/ark-help` | Full ARKintel command reference — all commands, parameters, and usage |

---

## 🛠️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/pwnedByJT/ARKintel.git
cd ARKintel
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your `.env` file

Create a `.env` file in the project root and add your Discord bot token:

```ini
DISCORD_TOKEN=your_discord_bot_token_here
```

### 4. Configure IDs

Open `ARK.py` and set your server-specific IDs in the configuration section:

```python
# --- CONFIGURATION ---
TARGET_CHANNEL_ID = 1178760002186526780  # Channel where commands are allowed
ARK_ROLE_ID = 1364705580064706600        # Role to ping for EVO alerts (e.g. @Ark)
# ---------------------
```

### 5. Run the bot
```bash
python ARK.py
```

---

## 🔑 Permissions Required

The bot needs these permissions in your Discord server for full functionality:

| Permission | Why |
|---|---|
| **Manage Channels** | ⚠️ Critical — creates and renames Voice Counters |
| **View Channels** | Read channel state |
| **Send Messages** | Post embeds and alerts |
| **Embed Links** | Rich embed support |
| **Use Slash Commands** | Required for all `/` commands |

> **Admin note:** `/monitor` and `/stopmonitor` are restricted to Admins/Mods to prevent spam.

---

## 📡 Data Sources

All data is pulled live from **Studio Wildcard's official infrastructure**:

| Data | Source |
|---|---|
| Server List | `cdn2.arkdedicated.com/servers/asa/officialserverlist.json` |
| Dynamic Config (EVO rates) | `cdn2.arkdedicated.com/asa/dynamicconfig.ini` |

---

## 👑 Author

**Developed by:** Justin Aaron Turner *(pwnedByJT)*

| Platform | Link |
|---|---|
| 🎮 Twitch | [twitch.tv/pwnedByJT](https://twitch.tv/pwnedByJT) |
| 🐦 Twitter | [twitter.com/pwnedByJT](https://twitter.com/pwnedByJT) |
| 💬 Discord | `pwnedByJT` |
| 💻 GitHub | [github.com/pwnedByJT](https://github.com/pwnedByJT) |

---

## 📜 License

This project is licensed under the **MIT License** — use it, fork it, build on it.
