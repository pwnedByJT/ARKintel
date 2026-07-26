"""
Module: data/tame_stats.py
Description: ASA endgame leveling guide database for alpha-tier PvP and boss content.
             Focus: domestic level allocation strategies (88 pts post-hatch/tame),
             key game-engine thresholds, and tribal meta tips.
             Edit this file to update tame data as the meta shifts.
Author: pwnedByJT
"""

# ---------------------------------------------------------------------------
# ALIAS MAP — normalize shorthand / typo inputs to canonical keys
# ---------------------------------------------------------------------------
TAME_ALIASES: dict[str, str] = {
    # Giganotosaurus
    "giga": "giganotosaurus",
    "giganoto": "giganotosaurus",
    "giganotosaurus": "giganotosaurus",

    # Carcharodontosaurus
    "carcha": "carcharodontosaurus",
    "carch": "carcharodontosaurus",
    "carcharodontosaurus": "carcharodontosaurus",

    # Therizinosaurus
    "theri": "therizinosaurus",
    "theriz": "therizinosaurus",
    "therizinosaurus": "therizinosaurus",

    # Stegosaurus
    "stego": "stegosaurus",
    "stegosaurus": "stegosaurus",

    # Rex
    "rex": "rex",
    "trex": "rex",
    "t-rex": "rex",
    "tyrannosaurus": "rex",

    # Yutyrannus
    "yuty": "yutyrannus",
    "yut": "yutyrannus",
    "yutyrannus": "yutyrannus",

    # Daeodon
    "daeodon": "daeodon",
    "daedon": "daeodon",
    "daed": "daeodon",
    "pig": "daeodon",

    # Pyromane
    "pyro": "pyromane",
    "pyromane": "pyromane",

    # Rhyniognatha
    "rhyno": "rhyniognatha",
    "rhynio": "rhyniognatha",
    "rhyniognatha": "rhyniognatha",

    # Quetzal
    "quetz": "quetzal",
    "quetzal": "quetzal",
    "quetzalcoatlus": "quetzal",

    # Ankylosaurus
    "anky": "ankylosaurus",
    "ankylosaurus": "ankylosaurus",

    # Dunkleosteus
    "dunkle": "dunkleosteus",
    "dunk": "dunkleosteus",
    "dunkleosteus": "dunkleosteus",

    # Paraceratherium
    "paracer": "paraceratherium",
    "para": "paraceratherium",
    "paraceratherium": "paraceratherium",
}


# ---------------------------------------------------------------------------
# TAME DATABASE
#
# Schema per entry:
#   display_name  : str        — shown in embed title
#   color         : int        — hex embed color
#                               Red/Orange = aggressive | Green = tank/support
#                               Blue = utility | Purple = specialist
#   builds        : list[dict] — named build options, each has:
#       name      : str        — e.g. "Full Aggro", "Balanced Raider"
#       split     : str        — domestic point dump e.g. "73 → Melee | 15 → HP"
#   thresholds    : list[str]  — game-engine caps, mechanics, optimal trigger points
#   tips          : list[str]  — saddle reqs, synergy, tribe usage notes
# ---------------------------------------------------------------------------
TAME_DATABASE: dict[str, dict] = {

    # ===================================================================
    # GIGANOTOSAURUS  — alpha PvP / raid apex
    # ===================================================================
    "giganotosaurus": {
        "display_name": "Giganotosaurus",
        "color": 0xE74C3C,
        "builds": [
            {
                "name": "Full Aggro (Raid)",
                "split": "73 pts → Melee  |  15 pts → Health",
            },
            {
                "name": "Balanced Raider",
                "split": "50 pts → Melee  |  34 pts → Health  |  4 pts → Stamina",
            },
        ],
        "thresholds": [
            "RAGE: Giga turns on rider when HP falls below ~40% of its post-tame max. "
            "Dismount or retreat before this threshold.",
            "POST-TAME HP DROP: Wild Giga HP (~80k) tanks to ~17–18k after taming at lvl 150. "
            "All usable HP comes from domestic levels + mutation stacks.",
            "MUTATION CAP: 20 maternal + 20 paternal per stat line. Stack Melee first, then HP.",
            "IMPRINT: Full imprint grants ~30% across all stats — mandatory before deployment.",
            "Saddle armor directly reduces incoming damage. Sub-90 armor Gigas are fragile.",
        ],
        "tips": [
            "Ascendant saddle (90+ armor) is non-negotiable. No exceptions.",
            "Pocket a Daeodon rider behind the Giga — force-feed cooked meat to top HP between engagements.",
            "Yutyrannus courage roar: +25% damage. Always have a Yuty buffing before first contact.",
            "Counter-play: Carcha with full blood-rage stacks can out-DPS a Giga. Intercept Carchas first.",
            "Never deploy in boss arenas where Giga is restricted (Broodmother arena).",
        ],
    },

    # ===================================================================
    # CARCHARODONTOSAURUS  — blood-rage DPS scaler
    # ===================================================================
    "carcharodontosaurus": {
        "display_name": "Carcharodontosaurus",
        "color": 0xC0392B,
        "builds": [
            {
                "name": "Blood Frenzied (Pure DPS)",
                "split": "88 pts → Melee  (rage mechanic makes HP secondary)",
            },
            {
                "name": "Sustained Aggressor",
                "split": "70 pts → Melee  |  14 pts → Health  |  4 pts → Stamina",
            },
        ],
        "thresholds": [
            "BLOOD RAGE: Each kill grants stacking Melee + Speed buff. Caps at ~10–15 stacks. "
            "At max stacks, effective DPS exceeds a Giganotosaurus.",
            "RAGE DECAY: Stacks bleed off over time. Must chain kills to maintain the buff — "
            "avoid long gaps between targets.",
            "Speed increases with each rage stack — kiting becomes extremely effective at cap.",
            "IMPRINT: +30% stat bonus at full imprint. Never deploy unimprinted.",
        ],
        "tips": [
            "Pre-stack rage on nearby wild dinos (Parasaurs, Trikes) before engaging enemy tames.",
            "Use Yutyrannus fear roar to scatter enemy tames and create easy kill-chain targets.",
            "Hard counter to Gigas — route Carcha into enemy Giga pack first, not their riders.",
            "Saddle: 70+ armor minimum. ASC if available — Carcha needs to survive long enough to stack.",
            "Protect the rider — coordinated dismount attempts shut down Carcha.",
        ],
    },

    # ===================================================================
    # THERIZINOSAURUS  — Dragon boss DPS + harvest
    # ===================================================================
    "therizinosaurus": {
        "display_name": "Therizinosaurus",
        "color": 0xE67E22,
        "builds": [
            {
                "name": "Dragon Slayer (Boss)",
                "split": "88 pts → Melee  (damage output is everything in Dragon arena)",
            },
            {
                "name": "Balanced Fighter",
                "split": "60 pts → Melee  |  24 pts → Health  |  4 pts → Stamina",
            },
            {
                "name": "Berry Farmer",
                "split": "60 pts → Weight  |  20 pts → Melee  |  8 pts → Health",
            },
        ],
        "thresholds": [
            "VEGGIE CAKE: Each cake heals a flat ~2,000 HP. At 21,000 HP base, one cake per "
            "cycle is sustainable — going far above this wastes cake efficiency per point invested.",
            "ATTACK MODES: Delicate (berries/fiber), Regular (wood/thatch/meat), "
            "Power (stone/hide). Swap with RMB before each gather type.",
            "FIRE RESISTANCE: Theri melee damage bypasses Dragon's fire resistance that kills Rexes.",
            "IMPRINT: Full imprint mandatory for boss runs — +30% across stats.",
            "Saddle: 70+ armor minimum; 90+ for alpha Dragon.",
        ],
        "tips": [
            "MANDATORY for Dragon Boss. 19+ Therizinos + 1 Yutyrannus = alpha Dragon meta.",
            "Pair with Yuty courage roar — +25% damage multiplier throughout the fight.",
            "Never bring Rexes to Dragon — fire will destroy them. Theri or nothing.",
            "Farm Theris double as boss fighters if leveled for Melee. Breed separate weight lines.",
            "Highest damage-per-swing of any herbivore when fully mutated.",
        ],
    },

    # ===================================================================
    # STEGOSAURUS  — soaker / rider carry / platform
    # ===================================================================
    "stegosaurus": {
        "display_name": "Stegosaurus",
        "color": 0x27AE60,
        "builds": [
            {
                "name": "Hardened Plate Tank (Soaker)",
                "split": "80 pts → Health  |  8 pts → Stamina  (absolute HP is all that matters)",
            },
            {
                "name": "Rider Carry",
                "split": "60 pts → Health  |  24 pts → Stamina  |  4 pts → Weight",
            },
        ],
        "thresholds": [
            "PLATE MODE — Hard: Passive damage reduction. Use this mode 100% of the time when soaking.",
            "PLATE MODE — Sharpened: Deals damage to attackers on contact. Switch for PvP offense.",
            "PLATE MODE — Rounded: Knockback on hit. Situational — use to push enemies off doors/ramps.",
            "Stego has natural damage reduction from plating — HP investment stretches further than "
            "on other tames. Do not underestimate a well-leveled Stego.",
            "Platform saddle enables structure deployment — turrets, beds, fabricators on back.",
        ],
        "tips": [
            "Turret soak rotation: cycle 3+ Stegos. One walks while two regen. Track turret ammo.",
            "Hard Plate mode ONLY when soaking turrets. Never forget to switch modes.",
            "Coordinate with demolition team — give them breach window as Stego soaks last shots.",
            "Stego pairs well with Paracer for multi-layer forward assault (Paracer holds turrets, "
            "Stego soaks incoming fire).",
            "Saddle: 60+ armor for soaking. 90+ for active PvP engagements.",
        ],
    },

    # ===================================================================
    # REX  — universal boss army staple
    # ===================================================================
    "rex": {
        "display_name": "Rex (Tyrannosaurus)",
        "color": 0xD35400,
        "builds": [
            {
                "name": "Alpha Boss Runner",
                "split": "Dump HP until base reaches ~19,000, then 100% Melee for remaining pts.",
            },
            {
                "name": "Pure DPS Rex",
                "split": "88 pts → Melee  (only viable with very high mutation HP line)",
            },
        ],
        "thresholds": [
            "19,000 HP: Alpha-tier tribe minimum before entering any boss arena. "
            "Below this, a single AOE wipe kills your entire army.",
            "ARMY COMPOSITION: 18 Rexes + 1 Yutyrannus = standard alpha boss team.",
            "DRAGON EXCEPTION: Do NOT bring Rexes to Dragon Boss. Fire destroys them. Use Therizinos.",
            "IMPRINT: Full imprint = +30% stats. Every unimprinted Rex is a liability.",
            "Saddle: 90+ armor MANDATORY for alpha boss. No exceptions.",
        ],
        "tips": [
            "Mutation priority: HP line first (reach 19k floor), then Melee. Never skip HP.",
            "Alpha Megapithecus and Alpha Broodmother: standard Rex army works. Dragon: swap to Theri.",
            "Use Daeodon positioned center-mass of Rex army for continuous AoE healing.",
            "Position Yutyrannus at the rear — spam courage roar on cooldown for entire fight duration.",
            "Keep 1–2 backup Rexes available. Losing 2+ in a run is a wipe risk.",
        ],
    },

    # ===================================================================
    # YUTYRANNUS  — battle commander / courage buffer
    # ===================================================================
    "yutyrannus": {
        "display_name": "Yutyrannus",
        "color": 0x3498DB,
        "builds": [
            {
                "name": "Battle Commander (Boss)",
                "split": "60 pts → Stamina  |  24 pts → Health  |  4 pts → Melee",
            },
            {
                "name": "Roar Support (Sustained)",
                "split": "80 pts → Stamina  |  8 pts → Health  (pure uptime on roars)",
            },
        ],
        "thresholds": [
            "COURAGE ROAR: +25% damage buff applied to all nearby tames + fear effect on wild creatures. "
            "Mandatory uptime for every boss fight.",
            "ROAR COOLDOWN: ~10 seconds between courage roars. Rider must spam this on cooldown "
            "for the full fight duration — do not neglect it.",
            "Stamina is the gating stat. Running out mid-fight means a damage gap. "
            "Invest stamina heavily.",
            "Losing Yuty mid-fight effectively cuts your army's DPS by 25%.",
        ],
        "tips": [
            "Position: rear of the Rex/Theri army. It buffs at range — never frontline.",
            "Rider job is 100% roar management. Do not engage in combat — keep Yuty alive.",
            "Saddle: 70+ armor sufficient. Yuty is support, not a tank.",
            "Pair with Daeodon nearby — Yuty takes splash damage during Broodmother adds phase.",
            "Fear Roar: scatter adds (spiderlings, Megapithecus boulders can't be feared, but "
            "wild dinos around boss entrances can be cleared quickly).",
        ],
    },

    # ===================================================================
    # DAEODON  — tribal healer / passive AoE sustain
    # ===================================================================
    "daeodon": {
        "display_name": "Daeodon",
        "color": 0x2ECC71,
        "builds": [
            {
                "name": "Sustain Healer",
                "split": "50 pts → Food  |  34 pts → Health  |  4 pts → Stamina",
            },
            {
                "name": "Emergency Heal Bomb",
                "split": "88 pts → Food  (max pulse uptime; HP comes from mutations only)",
            },
        ],
        "thresholds": [
            "HEAL PULSE: Heals all nearby creatures at ~800 HP/tick. Drains Food at ~2,000/sec "
            "at full output. A 0-Food-investment Daeodon burns out in seconds.",
            "HEAL TRIGGER: Pulse only fires when nearby creatures are below 100% HP. "
            "Enable before boss phases, not after damage starts.",
            "FOOD SCALE: Each domestic pt in Food meaningfully extends pulse uptime. "
            "Food investment is directly proportional to sustained healing.",
            "2 Daedons per boss team is the alpha-tier standard — redundancy covers the event "
            "one runs dry mid-fight.",
        ],
        "tips": [
            "Bring 500+ cooked meat per Daeodon into boss arenas for force-feeding mid-fight.",
            "Enable heal pulse BEFORE boss spawns — not after. Reaction delay costs lives.",
            "Rider job: exclusively force-feed Daeodon. Never dismount for any reason.",
            "Position Daeodon at the center of the Rex/Theri army for maximum AoE heal radius.",
            "Daeodon needs zero Melee investment. It is a pure utility tame.",
        ],
    },

    # ===================================================================
    # PYROMANE  — fire-breath AOE raider
    # ===================================================================
    "pyromane": {
        "display_name": "Pyromane",
        "color": 0xF39C12,
        "builds": [
            {
                "name": "Incendiary Raider",
                "split": "88 pts → Melee  (fire breath DOT scales directly with Melee)",
            },
            {
                "name": "Frontline Bruiser",
                "split": "60 pts → Melee  |  24 pts → Health  |  4 pts → Stamina",
            },
        ],
        "thresholds": [
            "FIRE BREATH DOT: Each burn tick scales with Melee. 100% Melee investment = maximum "
            "sustained damage output on structures and players.",
            "AOE RADIUS: Fire spread is a fixed cone — Melee changes tick damage, not spread width.",
            "STRUCTURE DAMAGE: Pyromane excels at wood and thatch. Metal requires sustained exposure.",
            "Pyromane is a newer ASA tame — verify current damage values match latest patch.",
        ],
        "tips": [
            "Prioritize wooden and thatch structure destruction before switching to stone/metal targets.",
            "AOE fire can friendly-fire your own structures — position carefully during base raids.",
            "Combo: Pyromane burns the target; Carcha closes for melee finish while burn ticks continue.",
            "Saddle: 70+ armor for frontline. Keep backup rider for dismount recovery.",
            "Pair with Giga for sequential breaches — Pyromane opens, Giga clears defenders.",
        ],
    },

    # ===================================================================
    # RHYNIOGNATHA  — aerial infiltrator / saboteur
    # ===================================================================
    "rhyniognatha": {
        "display_name": "Rhyniognatha",
        "color": 0x1ABC9C,
        "builds": [
            {
                "name": "Shadow Infiltrator",
                "split": "88 pts → Stamina  (flight duration is everything)",
            },
            {
                "name": "Combat Flyer",
                "split": "60 pts → Stamina  |  24 pts → Melee  |  4 pts → Health",
            },
        ],
        "thresholds": [
            "IMPLANT MECHANIC: Can implant larva inside players and tames — applies a "
            "damage-over-time effect. Unique PvP disruption tool with no direct counter.",
            "AERIAL SPEED: Among the fastest fliers in ASA. Raw speed advantage is in tame "
            "selection (high-level wild), not domestic level investment.",
            "Stamina gates all operations — a grounded Rhynio is dead. Never let stamina deplete.",
            "Does not have a conventional saddle slot in all builds — verify current ASA status.",
        ],
        "tips": [
            "Primary target: enemy Yutyrannus. Implanting the Yuty shuts down the enemy's courage buff.",
            "Secondary target: enemy Daedon riders — dismount or DoT the healer to collapse their sustain.",
            "Use for scouting: fast enough to survey enemy bases and escape before turrets render.",
            "Rhynio is NOT a frontline DPS mount. One focused enemy counter = dead Rhynio.",
            "Breed for the highest base stamina you can find — this is your stat line to prioritize.",
        ],
    },

    # ===================================================================
    # QUETZAL  — aerial platform / logistics / FOB
    # ===================================================================
    "quetzal": {
        "display_name": "Quetzal",
        "color": 0x16A085,
        "builds": [
            {
                "name": "Sky Freighter",
                "split": "80 pts → Weight  |  8 pts → Stamina",
            },
            {
                "name": "Platform FOB",
                "split": "60 pts → Weight  |  24 pts → Stamina  |  4 pts → Health",
            },
        ],
        "thresholds": [
            "WEIGHT SCALING: Each point in Weight adds to the base weight multiplied by tame bonus. "
            "Weight investment is the #1 return-on-investment stat for Quetzal.",
            "PLATFORM SADDLE: Allows permanent structure placement on Quetzal's back — "
            "turrets, generators, vaults, forges, and beds are all viable.",
            "Quetzal does NOT eat while in flight if rider-controlled. Land periodically or "
            "leave on wander to avoid starvation.",
            "Slow flight speed means heavy turret fire exposure. Stamp requires Stamina investment "
            "for retreat maneuvers.",
        ],
        "tips": [
            "Place 10–20 auto-turrets on platform saddle for a mobile raid support platform.",
            "Use with Ankylosaurus: hover Quetzal low while Anky rider mines — "
            "transfer metal directly to Quetzal inventory between swings.",
            "Pair with Argentavis (weight-leveled) for rapid metal runs — "
            "Argy transfers metal to hovering Quetz.",
            "FOB setup: place a bed + generator + industrial forge on Quetzal for a "
            "forward operating base during extended siege operations.",
            "Never invest in Melee — Quetzal is a logistics mount, not a combat mount.",
        ],
    },

    # ===================================================================
    # ANKYLOSAURUS  — metal / crystal / obsidian harvest
    # ===================================================================
    "ankylosaurus": {
        "display_name": "Ankylosaurus",
        "color": 0x7F8C8D,
        "builds": [
            {
                "name": "Metal Mule",
                "split": "80 pts → Weight  |  8 pts → Melee  (pure carry volume)",
            },
            {
                "name": "Yield Maximizer",
                "split": "50 pts → Weight  |  38 pts → Melee  (higher ore per swing, fewer trips)",
            },
        ],
        "thresholds": [
            "WEIGHT CAP: Determines trip efficiency. Higher weight = fewer return trips = "
            "more metal per hour. This is the primary stat.",
            "MELEE scales harvest yield per tail swing — every point increases ore count per hit.",
            "Anky cannot carry itself (too slow, no saddle air transport). MUST be ferried "
            "via Quetzal platform or Argentavis carry.",
            "Stamina investment is wasted — Anky sits on a platform or gets carried.",
        ],
        "tips": [
            "Hover Quetzal above metal nodes — Anky rider mines, transfers to Quetz inventory "
            "on the fly. Most efficient metal farming loop in the game.",
            "3 Anky trips to a Quetzal-ferried vault fills it with enough metal for a raid supply.",
            "Anky does NOT need mutations for farm role. Breed high base weight lines only.",
            "Works on metal, crystal, obsidian, oil, and stone nodes. Best on metal-rich mountains.",
            "Pair Anky + Dunkleosteus for a complete surface-and-deep resource pipeline.",
        ],
    },

    # ===================================================================
    # DUNKLEOSTEUS  — deep-sea oil / silica pearl harvesting
    # ===================================================================
    "dunkleosteus": {
        "display_name": "Dunkleosteus",
        "color": 0x2471A3,
        "builds": [
            {
                "name": "Oil Baron",
                "split": "80 pts → Weight  |  8 pts → Melee  (weight = more oil per dive)",
            },
            {
                "name": "Pearl Diver",
                "split": "60 pts → Weight  |  28 pts → Melee  (melee increases silica yield)",
            },
        ],
        "thresholds": [
            "OXYGEN: Irrelevant — Dunkleosteus is fully aquatic, invest zero points.",
            "WEIGHT: Primary stat. Deep-sea runs are limited by carry capacity, not dive time.",
            "MELEE: Increases harvest yield per bite on oil rocks and silica pearl nodes.",
            "COMBAT DAMAGE REDUCTION: Dunkleosteus has innate damage reduction against "
            "Mosasaurus and Megalodon — it can hold its own in combat if needed.",
            "Rider oxygen IS limited — surface every 2–3 minutes or bring a scuba tank.",
        ],
        "tips": [
            "Deep-sea drop zones yield massive oil and silica pearls — invest in Weight for volume.",
            "Escort with Basilosaurus: Basilos protect against aggressive Mosas/Squids "
            "and do not traumatize the rider.",
            "Position Dunkleosteus over oil rock clusters — chained bites harvest rapidly.",
            "Surface periodically at oxygen half-point (if not scuba-equipped) to avoid blackout.",
            "Pair with Ankylosaurus pipeline: Dunk covers underwater resources, Anky covers surface.",
            "Does NOT need mutations for farm role — breed high base Weight and Melee lines.",
        ],
    },

    # ===================================================================
    # PARACERATHERIUM  — rolling FOB / turret platform / soaker
    # ===================================================================
    "paraceratherium": {
        "display_name": "Paraceratherium",
        "color": 0x8E44AD,
        "builds": [
            {
                "name": "Rolling FOB",
                "split": "60 pts → Health  |  24 pts → Weight  |  4 pts → Stamina",
            },
            {
                "name": "Turret Soaker",
                "split": "88 pts → Health  (maximum survivability under sustained turret fire)",
            },
        ],
        "thresholds": [
            "PLATFORM SADDLE: Structures, turrets, generators, and beds can all be placed "
            "on Paracer's back — making it a mobile forward operating base.",
            "WEIGHT: Secondary priority for FOB role — heavier platform holds more structure "
            "inventory and deployed ammunition.",
            "Paracer is slower than Stego but larger — it can sustain more turret hits before "
            "reaching critical HP. Use Paracer for opening breaches, Stego for sustained soak.",
            "STRUCTURE LIMIT: Platform saddle has a structure cap — plan turret layout efficiently.",
        ],
        "tips": [
            "FOB build: deploy 10–20 auto-turrets on Paracer's platform before a base assault. "
            "Walk it into range and let the turrets engage while the enemy is distracted.",
            "Pair with Stego soaker line: Stegos absorb turret fire while Paracer advances "
            "its own turret platform into range.",
            "Place a bed + sleeping bag on the platform for rapid respawn during active raids.",
            "Deploy industrial forge on Paracer for on-the-fly ammunition smelting during siege.",
            "Keep a dedicated rider managing platform structure repairs mid-assault.",
        ],
    },
}


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def resolve_tame(query: str) -> str | None:
    """
    Normalize user input → canonical tame key via alias map.
    Returns None if no match.
    """
    normalized = query.strip().lower()
    canonical = TAME_ALIASES.get(normalized)
    if canonical and canonical in TAME_DATABASE:
        return canonical
    return None


def get_tame_data(key: str) -> dict | None:
    """
    Return the full data dict for a tame by canonical key.
    Returns None if the key doesn't exist.
    """
    return TAME_DATABASE.get(key)


def list_tame_display_names() -> list[str]:
    """All canonical display names (for error messages)."""
    return [v["display_name"] for v in TAME_DATABASE.values()]


def search_tames(query: str) -> list[str]:
    """
    Substring search across alias keys and display names.
    Returns matching display names for autocomplete suggestions.
    """
    q = query.strip().lower()
    matches: list[str] = []
    seen: set[str] = set()
    for key, data in TAME_DATABASE.items():
        if (q in key or q in data["display_name"].lower()) and key not in seen:
            matches.append(data["display_name"])
            seen.add(key)
    return matches
