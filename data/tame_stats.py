"""
Module: data/tame_stats.py
Description: ASA endgame leveling guide database — hyper-concise point-dump
             strategies for alpha-tier PvP and boss content.
Author: pwnedByJT
"""

# ---------------------------------------------------------------------------
# ALIAS MAP
# ---------------------------------------------------------------------------
TAME_ALIASES: dict[str, str] = {
    "giga": "giganotosaurus",
    "giganoto": "giganotosaurus",
    "giganotosaurus": "giganotosaurus",

    "carcha": "carcharodontosaurus",
    "carch": "carcharodontosaurus",
    "carcharodontosaurus": "carcharodontosaurus",

    "theri": "therizinosaurus",
    "theriz": "therizinosaurus",
    "therizinosaurus": "therizinosaurus",

    "stego": "stegosaurus",
    "stegosaurus": "stegosaurus",

    "rex": "rex",
    "trex": "rex",
    "t-rex": "rex",
    "tyrannosaurus": "rex",

    "yuty": "yutyrannus",
    "yut": "yutyrannus",
    "yutyrannus": "yutyrannus",

    "daeodon": "daeodon",
    "daedon": "daeodon",
    "daed": "daeodon",
    "pig": "daeodon",

    "pyro": "pyromane",
    "pyromane": "pyromane",

    "rhyno": "rhyniognatha",
    "rhynio": "rhyniognatha",
    "rhyniognatha": "rhyniognatha",

    "quetz": "quetzal",
    "quetzal": "quetzal",
    "quetzalcoatlus": "quetzal",

    "anky": "ankylosaurus",
    "ankylosaurus": "ankylosaurus",

    "dunkle": "dunkleosteus",
    "dunk": "dunkleosteus",
    "dunkleosteus": "dunkleosteus",

    "paracer": "paraceratherium",
    "para": "paraceratherium",
    "paraceratherium": "paraceratherium",
}


# ---------------------------------------------------------------------------
# TAME DATABASE
#
# Schema per entry:
#   display_name : str        — shown in embed title
#   meta         : str        — ONE LINE core purpose statement
#   color        : int        — hex embed color
#   builds       : list[dict] — named builds, each has:
#       name     : str        — e.g. "Full Aggro"
#       points   : list[str]  — point dump lines e.g. "80 Pts → Weight"
#   thresholds   : list[str]  — MAX 2. Hard caps / engine limits / exact targets only.
#   tips         : list[str]  — MAX 2. Punchy action items only.
# ---------------------------------------------------------------------------
TAME_DATABASE: dict[str, dict] = {

    "giganotosaurus": {
        "display_name": "Giganotosaurus",
        "meta": "Alpha PvP & Raid — frontline apex DPS. Irreplaceable for ground assaults.",
        "color": 0xE74C3C,
        "builds": [
            {
                "name": "Full Aggro (Raid)",
                "points": ["73 Pts → Melee", "15 Pts → Health"],
            },
            {
                "name": "Balanced Raider",
                "points": ["50 Pts → Melee", "34 Pts → Health", "4 Pts  → Stamina"],
            },
        ],
        "thresholds": [
            "• Rage triggers at ~40% post-tame HP — dismount before this or lose control.",
            "• Post-tame HP ~17–18k at lvl 150. All usable HP comes from mutations + domestic levels.",
        ],
        "tips": [
            "• ASC saddle 90+ armor. Non-negotiable.",
            "• Yuty courage roar active + pocket Daeodon before first engagement.",
        ],
    },

    "carcharodontosaurus": {
        "display_name": "Carcharodontosaurus",
        "meta": "Blood-rage DPS scaler — surpasses Giga at max kill stacks.",
        "color": 0xC0392B,
        "builds": [
            {
                "name": "Blood Frenzied (Pure DPS)",
                "points": ["88 Pts → Melee"],
            },
            {
                "name": "Sustained Aggressor",
                "points": ["70 Pts → Melee", "14 Pts → Health", "4 Pts  → Stamina"],
            },
        ],
        "thresholds": [
            "• Blood rage caps at ~10–15 kills. Stacks decay — never stop chaining.",
            "• Max-stack Carcha out-DPS a Giga. Intercept enemy Carchas before they stack.",
        ],
        "tips": [
            "• Pre-stack rage on wild dinos before engaging enemy tames.",
            "• Yuty fear roar scatters enemies — creates easy kill chains to hold stacks.",
        ],
    },

    "therizinosaurus": {
        "display_name": "Therizinosaurus",
        "meta": "Dragon Boss DPS + berry/fiber harvest — mandatory for Dragon arena.",
        "color": 0xE67E22,
        "builds": [
            {
                "name": "Dragon Slayer (Boss)",
                "points": ["88 Pts → Melee"],
            },
            {
                "name": "Balanced Fighter",
                "points": ["60 Pts → Melee", "24 Pts → Health", "4 Pts  → Stamina"],
            },
            {
                "name": "Berry Farmer",
                "points": ["60 Pts → Weight", "20 Pts → Melee", "8 Pts  → Health"],
            },
        ],
        "thresholds": [
            "• HP target: 21,000 max for boss builds (Veggie Cake efficiency ceiling).",
            "• Dragon Boss: Theri melee bypasses fire resistance — Rexes do not survive.",
        ],
        "tips": [
            "• 19+ Theris + 1 Yuty = alpha Dragon meta. No Rexes in that arena.",
            "• RMB to cycle attack mode: Delicate (berries/fiber) / Power (stone/hide).",
        ],
    },

    "stegosaurus": {
        "display_name": "Stegosaurus",
        "meta": "Turret soaker & platform raider — core raid support on every breach.",
        "color": 0x27AE60,
        "builds": [
            {
                "name": "Hardened Plate Tank (Soaker)",
                "points": ["80 Pts → Health", "8 Pts  → Stamina"],
            },
            {
                "name": "Rider Carry",
                "points": ["60 Pts → Health", "24 Pts → Stamina", "4 Pts  → Weight"],
            },
        ],
        "thresholds": [
            "• Hard Plate mode only when soaking — reduces incoming damage passively.",
            "• Sharpened Plate = damage return on attacker hit. Switch mode for PvP offense.",
        ],
        "tips": [
            "• Rotate 3+ Stegos. One soaks while two regen stamina and HP.",
            "• Platform saddle: deploy turrets + beds for active raid operations.",
        ],
    },

    "rex": {
        "display_name": "Rex (Tyrannosaurus)",
        "meta": "Universal boss army staple — 18 Rexes + 1 Yuty is the alpha boss meta.",
        "color": 0xD35400,
        "builds": [
            {
                "name": "Alpha Boss Runner",
                "points": ["Dump HP until base ~19,000, then 100% Melee"],
            },
            {
                "name": "Pure DPS Rex",
                "points": ["88 Pts → Melee  (only with high mutation HP line)"],
            },
        ],
        "thresholds": [
            "• HP floor: 19,000 before any boss arena. Single AOE below this = army wipe.",
            "• Dragon Boss: DO NOT bring Rexes. Fire destroys them — use Therizinos.",
        ],
        "tips": [
            "• Saddle 90+ armor. Mutation order: HP to 19k floor first, then Melee.",
            "• Daeodon center-mass + Yuty rear = standard alpha boss formation.",
        ],
    },

    "yutyrannus": {
        "display_name": "Yutyrannus",
        "meta": "Battle commander — mandatory for every boss run. One per team.",
        "color": 0x3498DB,
        "builds": [
            {
                "name": "Battle Commander (Boss)",
                "points": ["60 Pts → Stamina", "24 Pts → Health", "4 Pts  → Melee"],
            },
            {
                "name": "Roar Support (Sustained)",
                "points": ["80 Pts → Stamina", "8 Pts  → Health"],
            },
        ],
        "thresholds": [
            "• Courage roar: +25% damage to all nearby tames. Cooldown ~10s — spam it.",
            "• Losing Yuty mid-fight = instant -25% army DPS. Keep it alive at all costs.",
        ],
        "tips": [
            "• Position rear of army. Rider's only job: spam roar. Never engage in combat.",
            "• Saddle 70+ armor sufficient. Keep Daeodon adjacent for splash damage heals.",
        ],
    },

    "daeodon": {
        "display_name": "Daeodon",
        "meta": "AoE tribal healer — sustains the entire boss army passively.",
        "color": 0x2ECC71,
        "builds": [
            {
                "name": "Sustain Healer",
                "points": ["50 Pts → Food", "34 Pts → Health", "4 Pts  → Stamina"],
            },
            {
                "name": "Heal Bomb",
                "points": ["88 Pts → Food  (max pulse uptime; HP from mutations only)"],
            },
        ],
        "thresholds": [
            "• Heal pulse burns ~2,000 Food/sec at full output. Zero Food investment = burns in seconds.",
            "• Pulse only fires when nearby creatures are below 100% HP — enable before damage starts.",
        ],
        "tips": [
            "• Enable heal BEFORE boss spawns. Bring 500+ cooked meat to force-feed mid-fight.",
            "• 2 Daedons per alpha run. Position center-mass of Rex army for full AoE radius.",
        ],
    },

    "pyromane": {
        "display_name": "Pyromane",
        "meta": "Fire-breath AOE raider — structure destruction and sustained burn DoT.",
        "color": 0xF39C12,
        "builds": [
            {
                "name": "Incendiary Raider",
                "points": ["88 Pts → Melee"],
            },
            {
                "name": "Frontline Bruiser",
                "points": ["60 Pts → Melee", "24 Pts → Health", "4 Pts  → Stamina"],
            },
        ],
        "thresholds": [
            "• Fire breath DoT ticks scale directly with Melee — 100% Melee = max burn output.",
            "• AOE cone width is fixed. Melee changes tick damage, not spread radius.",
        ],
        "tips": [
            "• Prioritize wood/thatch targets. Metal requires sustained prolonged exposure.",
            "• Combo: Pyromane burns, Carcha closes for melee finish while DoT ticks.",
        ],
    },

    "rhyniognatha": {
        "display_name": "Rhyniognatha",
        "meta": "Aerial infiltrator — implant saboteur and deep-strike scout.",
        "color": 0x1ABC9C,
        "builds": [
            {
                "name": "Shadow Infiltrator",
                "points": ["88 Pts → Stamina"],
            },
            {
                "name": "Combat Flyer",
                "points": ["60 Pts → Stamina", "24 Pts → Melee", "4 Pts  → Health"],
            },
        ],
        "thresholds": [
            "• Stamina gates all operations. Grounded Rhynio = dead Rhynio.",
            "• Speed advantage is in tame selection (wild level), NOT domestic levels.",
        ],
        "tips": [
            "• Primary target: enemy Yuty. Implant shuts down their +25% courage buff.",
            "• Scout only — never frontline. One focused counter = instant loss.",
        ],
    },

    "quetzal": {
        "display_name": "Quetzal",
        "meta": "Primary heavy logistics & aerial FOB — platform saddle backbone.",
        "color": 0x16A085,
        "builds": [
            {
                "name": "Sky Freighter",
                "points": ["80 Pts → Weight", "8 Pts  → Stamina"],
            },
            {
                "name": "Mobile Raid FOB",
                "points": ["60 Pts → Weight", "24 Pts → Stamina", "4 Pts  → Health"],
            },
        ],
        "thresholds": [
            "• Weight is multiplicative — highest point-for-point return on Quetzal.",
            "• Does not eat while rider-controlled in flight. Land periodically.",
        ],
        "tips": [
            "• Hover above metal nodes — Anky rider mines and transfers directly to Quetzal.",
            "• FOB build: 10–20 auto-turrets + bed + generator on platform saddle.",
        ],
    },

    "ankylosaurus": {
        "display_name": "Ankylosaurus",
        "meta": "Metal, crystal & obsidian harvest — must be ferried via Quetzal.",
        "color": 0x7F8C8D,
        "builds": [
            {
                "name": "Metal Mule",
                "points": ["80 Pts → Weight", "8 Pts  → Melee"],
            },
            {
                "name": "Yield Maximizer",
                "points": ["50 Pts → Weight", "38 Pts → Melee"],
            },
        ],
        "thresholds": [
            "• Weight = trips per hour. Melee = ore per swing. Zero other investment.",
            "• Cannot self-transport. Requires Quetzal platform or Argy carry.",
        ],
        "tips": [
            "• Hover Quetzal above nodes — direct mid-harvest inventory transfer.",
            "• Never dump into Stamina. No mutations needed — breed high base Weight lines.",
        ],
    },

    "dunkleosteus": {
        "display_name": "Dunkleosteus",
        "meta": "Deep-sea oil & silica pearl harvesting — fully aquatic, no Oxygen needed.",
        "color": 0x2471A3,
        "builds": [
            {
                "name": "Oil Baron",
                "points": ["80 Pts → Weight", "8 Pts  → Melee"],
            },
            {
                "name": "Pearl Diver",
                "points": ["60 Pts → Weight", "28 Pts → Melee"],
            },
        ],
        "thresholds": [
            "• Oxygen: invest zero. Weight = dive efficiency. Only two stats matter.",
            "• Innate damage reduction vs Mosasaurus & Megalodons — hold its own if contested.",
        ],
        "tips": [
            "• Escort with Basilosaurus for deep-sea predator protection.",
            "• Surface at 50% rider oxygen unless running scuba kit.",
        ],
    },

    "paraceratherium": {
        "display_name": "Paraceratherium",
        "meta": "Rolling FOB & turret platform — mobile forward raid asset.",
        "color": 0x8E44AD,
        "builds": [
            {
                "name": "Rolling FOB",
                "points": ["60 Pts → Health", "24 Pts → Weight", "4 Pts  → Stamina"],
            },
            {
                "name": "Turret Soaker",
                "points": ["88 Pts → Health"],
            },
        ],
        "thresholds": [
            "• Platform saddle: turrets, beds, forges, and generators all viable on back.",
            "• Larger frame absorbs more turret hits than Stego before critical HP.",
        ],
        "tips": [
            "• Stego soaks incoming fire while Paracer advances turret platform into range.",
            "• Place bed + sleeping bag on platform for mid-raid respawn.",
        ],
    },
}


# ---------------------------------------------------------------------------
# VALIDATION (runs at import time — catches data errors before bot starts)
# ---------------------------------------------------------------------------
for _key, _data in TAME_DATABASE.items():
    assert "meta" in _data,         f"{_key}: missing 'meta'"
    assert "builds" in _data,       f"{_key}: missing 'builds'"
    assert len(_data["builds"]) > 0, f"{_key}: builds list is empty"
    for _b in _data["builds"]:
        assert "name" in _b and "points" in _b, f"{_key}: build missing name/points"
        assert len(_b["points"]) > 0,           f"{_key}: build '{_b['name']}' has no points"
    assert len(_data.get("thresholds", [])) <= 2, f"{_key}: thresholds exceeds max 2"
    assert len(_data.get("tips", [])) <= 2,       f"{_key}: tips exceeds max 2"


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def resolve_tame(query: str) -> str | None:
    normalized = query.strip().lower()
    canonical = TAME_ALIASES.get(normalized)
    if canonical and canonical in TAME_DATABASE:
        return canonical
    return None


def get_tame_data(key: str) -> dict | None:
    return TAME_DATABASE.get(key)


def list_tame_display_names() -> list[str]:
    return [v["display_name"] for v in TAME_DATABASE.values()]


def search_tames(query: str) -> list[str]:
    q = query.strip().lower()
    matches: list[str] = []
    seen: set[str] = set()
    for key, data in TAME_DATABASE.items():
        if (q in key or q in data["display_name"].lower()) and key not in seen:
            matches.append(data["display_name"])
            seen.add(key)
    return matches
