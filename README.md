# 🦖 ARKintel

**The alpha-tier Discord intel bot for ARK: Survival Ascended — live server monitoring, raid calculators, boss checklists, tame guides, and more. All in one slash command.**

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Discord.py](https://img.shields.io/badge/discord.py-2.3.2-blue?logo=discord)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)
![Game](https://img.shields.io/badge/game-ARK%3A%20Survival%20Ascended-orange)
![Deployed on](https://img.shields.io/badge/deployed%20on-K3s%20%E2%80%A2%20Raspberry%20Pi-informational?logo=kubernetes)

---

## What is ARKintel?

Built for ARK: Survival Ascended players who don't want to alt-tab mid-raid. Solo survivor, small tribe, mega-tribe — doesn't matter. Everything you need is a slash command away.

Stop alt-tabbing. Stop Googling recipes. Stop guessing how many C4 you need. **Just slash it.**

---

## What it does

- Live server dashboards that refresh every 60s + voice channel counters (e.g. `ASA #2154: 45/70`)
- Pop alerts — watch any server and get pinged the second it drops below a count you set
- EVO rate alerts when Official rates change
- Historical population data (24h+) — text stats via `/serverstats`, visual chart via `/popgraph`
- Tame leveling guides — exactly where to put your 88 domestic points per creature
- Hatch/cuddle timers with a 5-min heads-up ping
- Raid calculator — exact C4/RPG/grenade counts + raw material costs per structure
- Boss entry checklists — artifacts, tributes, army comp, saddle floors, HP floors, wipe risks
- Endgame recipe lookup (Veggie Cake, Mindwipe, Shadow Steak, Battle Tartare, etc.)
- Console optimization string — one copy-paste to kill shadows, fog, bloom, and foliage
- Personal server favorites with live status
- Live K3s cluster health — Pod status, restarts, uptime, node, resource usage

---

## Commands

### Tame Intel
| Command | Description |
|---|---|
| `/tame-stats tame:<name>` | Where to put your 88 domestic points. Aliases work: giga, theri, carcha, daed, paracer, dunk... |
| `/imprint creature:<name> time_remaining:<HH:MM> [ping_role:<role>]` | Cuddle timer. 5-min warning + ping when the window opens. One active per user. |
| `/imprint-cancel` | Cancel your running timer |

### Consumables
| Command | Description |
|---|---|
| `/recipe item:<name>` | Ingredients, effects, and spoil times for endgame consumables |

### Raid Calc
| Command | Description |
|---|---|
| `/raid-calc structure:<name> [quantity:<int>]` | C4/RPG/grenade counts + raw material costs. Default qty: 1, max: 500 |

### Boss Prep
| Command | Description |
|---|---|
| `/boss-check boss:<name> tier:<Gamma\|Beta\|Alpha>` | Artifacts, tributes, army comp, saddle/HP floors, and wipe risks before you portal in |

### Server Monitoring
| Command | Description |
|---|---|
| `/monitor server_number:<name>` | Live dashboard + voice counter, refreshes every 60s |
| `/serverpop server_number:<name>` | Quick one-time pop check, no persistent tracking |
| `/stopmonitor server_number:<name>` | Kill the dashboard and voice counter for a server |
| `/serverstats server_number:<name> [hours:<int>]` | Pop history and trends, default last 24h |
| `/popgraph server_number:<name> [hours:<int>]` | Visual population chart sent as an image. Needs at least 2 data points — run `/monitor` first |
| `/popwatch server_number:<name> threshold:<int>` | Pings you the moment a server's population drops below your number. Resets when pop climbs back up. |
| `/popwatch_remove server_number:<name>` | Remove a pop alert you set |

### Favorites & Utilities
| Command | Description |
|---|---|
| `/fav_add server_number:<name>` | Add a server to your personal list |
| `/fav_list` | See all your saved servers with live status |
| `/fav_remove server_number:<name>` | Drop a server from your list |
| `/console` | The full ASA optimization command string — one copy-paste to kill shadows, foliage, fog, bloom |

### Infrastructure
| Command | Description |
|---|---|
| `/cluster-status` | Live K3s Pod health: name, namespace, status, restarts, uptime, cluster IP, node, memory/CPU limits. Requires RBAC setup (see below). |

### Help
| Command | Description |
|---|---|
| `/ark-help` | Full command reference inside Discord |

---

## Architecture

ARKintel runs as a Kubernetes `Deployment` on a single-node **K3s** cluster hosted on a **Raspberry Pi (Debian 12 Bookworm)**. The container is built from `python:3.11-slim-bookworm`.

```
Raspberry Pi  →  K3s (single-node)  →  arkintel Deployment (1 replica)
                                            ↓
                                    python:3.11-slim-bookworm
                                    Env via K8s Secret (arkintel-env)
                                    Persistent data: server_stats.db (hostPath)
```

---

## Deployment (K3s)

### 1. Build the image

```bash
docker build -t arkintel:latest .
```

### 2. Import into K3s (no registry required)

```bash
docker save arkintel:latest | sudo k3s ctr images import -
```

### 3. Create the secret from your `.env`

```bash
kubectl create secret generic arkintel-env --from-env-file=.env
```

### 4. Apply RBAC (required for `/cluster-status`)

```bash
kubectl apply -f k8s/rbac.yaml
```

### 5. Deploy

```bash
kubectl apply -f deployment.yaml
```

> Your `deployment.yaml` must include `serviceAccountName: arkintel` for `/cluster-status` to have API access.

---

## K3s Management Cheat Sheet

| Task | Command |
|---|---|
| Check Pod status | `kubectl get pods -o wide` |
| Stream logs | `kubectl logs -f deployment/arkintel` |
| Restart deployment | `kubectl rollout restart deployment/arkintel` |
| Check resource usage | `kubectl top pod -l app=arkintel` |
| Re-import updated image | `docker save arkintel:latest \| sudo k3s ctr images import -` |
| Apply manifest changes | `kubectl apply -f deployment.yaml` |
| Delete and recreate | `kubectl delete deployment arkintel && kubectl apply -f deployment.yaml` |

---

## Setup (local / non-K3s)

### 1. Clone
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

## Permissions Required

The bot needs these permissions:

| Permission | Why |
|---|---|
| **Manage Channels** | ⚠️ Critical — creates and renames Voice Counters |
| **View Channels** | Read channel state |
| **Send Messages** | Post embeds and alerts |
| **Embed Links** | Rich embed support |
| **Use Slash Commands** | Required for all `/` commands |

---

## Data Sources

Pulled live from Studio Wildcard's official CDN:

| Data | Source |
|---|---|
| Server List | `cdn2.arkdedicated.com/servers/asa/officialserverlist.json` |
| Dynamic Config (EVO rates) | `cdn2.arkdedicated.com/asa/dynamicconfig.ini` |

---

## Author

**Justin Aaron Turner** *(pwnedByJT)*

| Platform | Link |
|---|---|
| 🎮 Twitch | [twitch.tv/pwnedByJT](https://twitch.tv/pwnedByJT) |
| 🐦 Twitter | [twitter.com/pwnedByJT](https://twitter.com/pwnedByJT) |
| 💬 Discord | `pwnedByJT` |
| 💻 GitHub | [github.com/pwnedByJT](https://github.com/pwnedByJT) |

---

## CI/CD & Deployment

Every push to `main` triggers an automated deployment via **GitHub Actions** running on a self-hosted runner on the Raspberry Pi.

The pipeline runs three steps in sequence:

1. **Build** — `docker build -t arkintel:latest .`
2. **Import** — `docker save arkintel:latest | sudo k3s ctr images import -` pushes the image directly into K3s's containerd store (no external registry needed)
3. **Rollout** — `sudo kubectl rollout restart deployment/arkintel` triggers a rolling restart; `kubectl rollout status` confirms the new pod is healthy within 60 seconds

The workflow file lives at `.github/workflows/deploy.yml`. The self-hosted runner must have `docker` installed, passwordless `sudo` for `k3s ctr`, and `KUBECONFIG` pointing at `/etc/rancher/k3s/k3s.yaml`.

---

## License

MIT — use it, fork it, build on it.
