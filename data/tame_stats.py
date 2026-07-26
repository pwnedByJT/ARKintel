"""
Module: data/tame_stats.py
Description: ASA endgame/meta tame stat allocation database for alpha-tier PvP and boss content.
             All stat targets are baseline estimates for fully mutated (20/20) lines at max
             imprint on official rates. Edit values here as the meta evolves.
Author: pwnedByJT
"""

# ---------------------------------------------------------------------------
# ALIAS MAP — normalize shorthand/typo inputs to canonical keys
# ---------------------------------------------------------------------------
TAME_ALIASES: dict[str, str] = {
    # Giganotosaurus
    "giga": "giganotosaurus",
    "giganoto": "giganotosaurus",
    "giganotosaurus": "giganotosaurus",

    # Therizinosaurus
    "theri": "therizinosaurus",
    "theriz": "therizinosaurus",
    "therizinosaurus": "therizinosaurus",

    # Carcharodontosaurus
    "carcha": "carcharodontosaurus",
    "carch": "carcharodontosaurus",
    "carcharodontosaurus": "carcharodontosaurus",

    # Rex
    "rex": "rex",
    "trex": "rex",
    "t-rex": "rex",
    "tyrannosaurus": "rex",

    # Yutyrannus
    "yuty": "yutyrannus",
    "yut": "yutyrannus",
    "yutyrannus": "yutyrannus",

    # Daedon
    "daed": "daedon",
    "daedon": "daedon",
    "pig": "daedon",

    # Stegosaurus
    "stego": "stegosaurus",
    "stegosaurus": "stegosaurus",

    # Rhyniognatha
    "rhyno": "rhyniognatha",
    "rhyniognatha": "rhyniognatha",
    "rhynio": "rhyniognatha",

    # Pyromane
    "pyro": "pyromane",
    "pyromane": "pyromane",

    # Megatherium
    "meg": "megatherium",
    "megatherium": "megatherium",
    "giant sloth": "megatherium",

    # Ankylosaurus
    "anky": "ankylosaurus",
    "ankylosaurus": "ankylosaurus",

    # Doedicurus
    "doed": "doedicurus",
    "doedicurus": "doedicurus",

    # Shadowmane
    "shadow": "shadowmane",
    "shadowmane": "shadowmane",

    # Managarmr
    "mana": "managarmr",
    "managarmr": "managarmr",
}


# ---------------------------------------------------------------------------
# TAME DATABASE
# Structure per tame:
#   display_name  : str  — pretty-printed name shown in embeds
#   color         : int  — hex embed color (Red=aggressive, Green=tank, Blue=utility)
#   roles         : dict — role name -> stat block (must include "General Meta")
#
# Stat block keys:
#   priority      : str  — ordered stat priority e.g. "Melee > Health > Stamina"
#   target_stats  : dict — stat label -> human-readable target string
#   level_split   : str  — domestic point allocation guidance (88 pts post-tame)
#   tips          : list[str] — pro tips, gear requirements, meta notes
# ---------------------------------------------------------------------------
TAME_DATABASE: dict[str, dict] = {

    # ===================================================================
    # GIGANOTOSAURUS  — primary alpha PvP/raid mount
    # ===================================================================
    "giganotosaurus": {
        "display_name": "Giganotosaurus",
        "color": 0xE74C3C,  # Red — aggressive apex predator
        "roles": {
            "General Meta": {
                "priority": "Melee > Health >> Stamina",
                "target_stats": {
                    "Health":    "38,000 – 45,000 HP  (fully mutated)",
                    "Stamina":   "2,000 – 3,000  (minimal investment)",
                    "Melee":     "1,800% – 2,400%  (20+20 mut stacks)",
                    "Weight":    "Default — no domestic investment",
                },
                "level_split": (
                    "44 pts → Melee  |  40 pts → Health  |  4 pts → Stamina\n"
                    "Mutation priority: Melee line first (20 mat / 20 pat), then HP line."
                ),
                "tips": [
                    "Ascendant saddle (90+ armor) is non-negotiable — unprotected Gigas melt.",
                    "RAGE MECHANIC: Giga turns on rider if HP drops below ~40%. "
                    "Keep it above 25% or dismount before it flips.",
                    "Post-tame HP is drastically lower than wild HP (~17-18k at 150). "
                    "All your effective HP comes from mutations + domestic levels.",
                    "Full imprint grants ~30% bonus — never deploy an unimprinted Giga.",
                    "Avoid Tek Caves — restricted and rider can be launched off on tight geometry.",
                    "Counter: Carcharodontosaurus with blood-rage active can out-DPS a Giga. "
                    "Never let a Carcha stack freely.",
                ],
            },
            "PvP Main": {
                "priority": "Melee > Health >> Stamina",
                "target_stats": {
                    "Health":  "40,000+ HP",
                    "Stamina": "2,500  (emergency retreat buffer)",
                    "Melee":   "2,200%+ (absolute floor for alpha-tier)",
                    "Weight":  "Default",
                },
                "level_split": (
                    "50 pts → Melee  |  34 pts → Health  |  4 pts → Stamina\n"
                    "PvP variant favors raw melee output over health padding."
                ),
                "tips": [
                    "Keep a Yutyrannus courage-roar active for +25% melee during raids.",
                    "Pair with a pocket Daedon for on-demand HP regen between engagements.",
                    "Watch stamina drain during extended fights — dismount to regen if >60% depleted.",
                    "Rider stays mounted: micro-manage HP via HUD; bail before rage threshold.",
                ],
            },
            "Boss / Raiding": {
                "priority": "Health > Melee > Stamina",
                "target_stats": {
                    "Health":  "45,000+ HP  (boss AOE survival)",
                    "Stamina": "2,000",
                    "Melee":   "1,800%+",
                    "Weight":  "Default",
                },
                "level_split": (
                    "44 pts → Health  |  40 pts → Melee  |  4 pts → Stamina\n"
                    "Boss variant prioritizes survival over raw DPS."
                ),
                "tips": [
                    "Bring backup Rexes — Gigas are NOT ideal for all boss arenas due to rage risk.",
                    "ASC saddle MANDATORY for boss encounters.",
                    "Broodmother: Gigas are banned in official boss arenas — use Megatheriums.",
                    "Dragon Boss: use Therizinos (fire damage negation via melee).",
                ],
            },
        },
    },

    # ===================================================================
    # THERIZINOSAURUS  — boss DPS + harvest utility
    # ===================================================================
    "therizinosaurus": {
        "display_name": "Therizinosaurus",
        "color": 0xE67E22,  # Orange — aggressive utility
        "roles": {
            "General Meta": {
                "priority": "Melee > Health > Weight",
                "target_stats": {
                    "Health":  "35,000 – 45,000 HP",
                    "Stamina": "1,500  (moderate for multi-phase bosses)",
                    "Melee":   "1,400% – 1,800%",
                    "Weight":  "2,500 – 4,000  (harvest variant only)",
                },
                "level_split": (
                    "44 pts → Melee  |  38 pts → Health  |  4 pts → Stamina  |  2 pts → Weight\n"
                    "Harvest variant: 30 pts → Weight, 30 pts → Melee, 24 pts → Health, 4 pts → Stam."
                ),
                "tips": [
                    "Ideal for Dragon Boss — melee bypasses fire damage reduction that kills Rexes.",
                    "Highest damage-per-swing of any herbivore; outperforms Rexes in Dragon arena.",
                    "Set attack mode: Delicate (fiber/berries), Regular (wood/thatch), Power (stone/hide).",
                    "Saddle requirement: 70+ armor minimum; 90+ for boss runs.",
                    "Full imprint mandatory — unimprinted Theris underperform significantly.",
                ],
            },
            "Boss / Raiding": {
                "priority": "Melee > Health > Stamina",
                "target_stats": {
                    "Health":  "40,000 – 50,000 HP",
                    "Stamina": "2,000",
                    "Melee":   "1,600%+",
                    "Weight":  "Default",
                },
                "level_split": "50 pts → Melee  |  34 pts → Health  |  4 pts → Stamina",
                "tips": [
                    "Dragon Boss: 19+ Therizinos with 19k+ HP is the official alpha meta.",
                    "Pair with Yutyrannus courage buff — mandatory for Dragon run.",
                    "Avoid Melee-stacking in favor of balanced HP for multi-wipe prevention.",
                ],
            },
            "Harvest / Utility": {
                "priority": "Weight > Melee > Health",
                "target_stats": {
                    "Health":  "20,000 – 25,000 HP",
                    "Stamina": "Default",
                    "Melee":   "600% – 900%  (harvest efficiency)",
                    "Weight":  "4,000 – 6,000",
                },
                "level_split": "44 pts → Weight  |  30 pts → Melee  |  14 pts → Health",
                "tips": [
                    "Use Delicate mode for berries/fiber; Power mode for stone harvest.",
                    "Combine with Ankylosaurus/Doed for multi-resource trips.",
                    "Weight Theris don't need mutations — breed for weight-line tames separately.",
                ],
            },
        },
    },

    # ===================================================================
    # CARCHARODONTOSAURUS  — blood-rage DPS monster
    # ===================================================================
    "carcharodontosaurus": {
        "display_name": "Carcharodontosaurus",
        "color": 0xC0392B,  # Dark Red — highest threat predator
        "roles": {
            "General Meta": {
                "priority": "Melee > Health > Stamina",
                "target_stats": {
                    "Health":  "30,000 – 40,000 HP",
                    "Stamina": "2,500  (sustain blood-rage stacking)",
                    "Melee":   "1,500% – 2,000%  (base; rage multiplies this)",
                    "Weight":  "Default",
                },
                "level_split": (
                    "44 pts → Melee  |  40 pts → Health  |  4 pts → Stamina\n"
                    "Blood-rage mechanic multiplies effective melee — invest more in survivability."
                ),
                "tips": [
                    "BLOOD RAGE: Each kill grants a stacking melee/speed buff. "
                    "At max stacks Carcha's DPS surpasses Giganotosaurus.",
                    "Rage stacks decay — keep chaining kills to maintain buff in extended fights.",
                    "Hard counter to Gigas when rage-stacked. Route Carcha into enemy tame lines first.",
                    "Can harvest organic polymer (jellyfish) and is immune to jellyfish damage.",
                    "Saddle requirement: 70+ armor; ASC if available.",
                    "Weak against coordinated dismount attempts — protect the rider.",
                ],
            },
            "PvP Main": {
                "priority": "Melee > Stamina > Health",
                "target_stats": {
                    "Health":  "28,000 – 35,000 HP",
                    "Stamina": "3,000  (sustain aggression chains)",
                    "Melee":   "1,800%+  (pre-rage base)",
                    "Weight":  "Default",
                },
                "level_split": "50 pts → Melee  |  30 pts → Health  |  8 pts → Stamina",
                "tips": [
                    "Open with 3-5 kills to pre-stack rage before engaging primary targets.",
                    "Stay mobile — speed buff from rage makes kiting very effective.",
                    "Combo with Yutyrannus fear roar to freeze enemy mounts while Carcha shreds.",
                ],
            },
        },
    },

    # ===================================================================
    # REX  — boss army staple
    # ===================================================================
    "rex": {
        "display_name": "Rex (Tyrannosaurus)",
        "color": 0xD35400,  # Dark Orange
        "roles": {
            "General Meta": {
                "priority": "Health > Melee > Stamina",
                "target_stats": {
                    "Health":  "30,000 – 40,000 HP  (19k+ is boss minimum)",
                    "Stamina": "1,500  (enough for full boss phase)",
                    "Melee":   "1,000% – 1,400%",
                    "Weight":  "Default",
                },
                "level_split": (
                    "44 pts → Health  |  40 pts → Melee  |  4 pts → Stamina\n"
                    "Boss meta: 19k HP floor is hard minimum for alpha-tier boss runs."
                ),
                "tips": [
                    "19k HP is the widely accepted alpha tribe minimum for boss fights. "
                    "Below this, a single AOE wipe can kill your entire army.",
                    "Saddle requirement: 90+ armor MANDATORY for alpha boss runs.",
                    "Rex army composition: 18 Rexes + 1 Yutyrannus = standard alpha boss meta.",
                    "Dragon Boss: REPLACE Rexes with Therizinos — fire damage will destroy Rexes.",
                    "Imprint: +30% stats when fully imprinted. Never bring unimprinted.",
                    "Mutation priority: HP line (survive AOE), then Melee.",
                ],
            },
            "Boss / Raiding": {
                "priority": "Health > Melee > Stamina",
                "target_stats": {
                    "Health":  "40,000+ HP  (alpha tier)",
                    "Stamina": "1,500",
                    "Melee":   "1,200%+",
                    "Weight":  "Default",
                },
                "level_split": "50 pts → Health  |  34 pts → Melee  |  4 pts → Stamina",
                "tips": [
                    "Alpha Broodmother: 19 Rexes minimum. 30k+ HP recommended.",
                    "Alpha Megapithecus: standard Rex army works well.",
                    "Alpha Dragon: DO NOT use Rexes. Use Therizinos.",
                    "Overseer: Rexes + Yutyrannus is viable on Island.",
                ],
            },
        },
    },

    # ===================================================================
    # YUTYRANNUS  — commander/support (mandatory boss support)
    # ===================================================================
    "yutyrannus": {
        "display_name": "Yutyrannus",
        "color": 0x3498DB,  # Blue — support/utility
        "roles": {
            "General Meta": {
                "priority": "Health > Stamina > Melee",
                "target_stats": {
                    "Health":  "30,000 – 50,000 HP  (tank boss splash)",
                    "Stamina": "3,000 – 4,000  (sustain multiple roars)",
                    "Melee":   "700% – 1,000%  (secondary priority)",
                    "Weight":  "Default",
                },
                "level_split": (
                    "44 pts → Health  |  30 pts → Stamina  |  14 pts → Melee\n"
                    "Stamina is critical — Yuty needs to sustain roars throughout the entire boss fight."
                ),
                "tips": [
                    "COURAGE ROAR: Grants +25% damage buff to all nearby tames + feared enemies flee.",
                    "FEAR ROAR: Makes wild creatures flee. Invaluable for controlling adds in boss arenas.",
                    "1 Yutyrannus per boss team = mandatory in all alpha-tier boss strategies.",
                    "Rider MUST spam courage roar on cooldown throughout the entire fight.",
                    "Position Yuty behind the Rex army — it provides buff at range, not frontline.",
                    "Yuty does NOT need ASC saddle — 70+ armor is sufficient for support role.",
                    "Keep Daedon nearby — Yuty takes splash damage and needs heals during Broodmother.",
                ],
            },
            "Boss / Raiding": {
                "priority": "Health > Stamina > Melee",
                "target_stats": {
                    "Health":  "40,000 – 55,000 HP",
                    "Stamina": "4,000+",
                    "Melee":   "800%",
                    "Weight":  "Default",
                },
                "level_split": "44 pts → Health  |  40 pts → Stamina  |  4 pts → Melee",
                "tips": [
                    "Invest heavily in stamina — Alpha Megapithecus fight requires sustained roaring.",
                    "Dragon Boss: Yuty IS viable alongside Therizinos; buff is still critical.",
                ],
            },
        },
    },

    # ===================================================================
    # DAEDON  — tribal healer
    # ===================================================================
    "daedon": {
        "display_name": "Daedon",
        "color": 0x2ECC71,  # Green — healer/support
        "roles": {
            "General Meta": {
                "priority": "Health > Food > Stamina",
                "target_stats": {
                    "Health":  "25,000 – 40,000 HP  (absorb splash while healing)",
                    "Food":    "12,000+  (sustain healing output without force-feeding)",
                    "Stamina": "1,500  (minimal)",
                    "Melee":   "Default — no investment",
                },
                "level_split": (
                    "44 pts → Health  |  30 pts → Food  |  14 pts → Stamina\n"
                    "Food investment critical — Daedon burns food extremely fast while healing."
                ),
                "tips": [
                    "HEALING PULSE: Heals all nearby creatures for 800 HP/tick — "
                    "drains food ~2,000/sec at full heal rate.",
                    "Bring cooked meat stacks or raw prime — force feed to maintain healing uptime.",
                    "Place Daedon at center of Rex army during boss for maximum heal reach.",
                    "1-2 Daedons per boss run; 2 recommended for alpha-tier reliability.",
                    "Healing activates only when creature is below 100% HP. Pre-stage during adds phase.",
                    "Force Heal (enable healing toggle) to pre-position before boss damage spikes.",
                    "Daedon does NOT need combat stats — full utility build only.",
                ],
            },
            "Boss / Raiding": {
                "priority": "Health > Food > Stamina",
                "target_stats": {
                    "Health":  "40,000+ HP",
                    "Food":    "15,000+",
                    "Stamina": "Default",
                    "Melee":   "Default",
                },
                "level_split": "44 pts → Health  |  40 pts → Food  |  4 pts → Stamina",
                "tips": [
                    "Alpha boss: bring 500+ cooked meat per Daedon.",
                    "Rider should exclusively force-feed Daedon — do not dismount.",
                    "Enable heal pulse before boss spawns to avoid reaction delay.",
                ],
            },
        },
    },

    # ===================================================================
    # STEGOSAURUS  — soaker / turret-walking / utility
    # ===================================================================
    "stegosaurus": {
        "display_name": "Stegosaurus",
        "color": 0x27AE60,  # Dark Green — tank/soaker
        "roles": {
            "General Meta": {
                "priority": "Health > Stamina > Weight",
                "target_stats": {
                    "Health":  "25,000 – 40,000 HP  (soak ammo / absorb shots)",
                    "Stamina": "2,500  (retreat and repeat)",
                    "Melee":   "400% – 700%  (stego plate damage on hit)",
                    "Weight":  "1,500 – 3,000  (carry soaked ammo loot)",
                },
                "level_split": (
                    "44 pts → Health  |  30 pts → Stamina  |  10 pts → Weight  |  4 pts → Melee\n"
                    "Soaker role: maximize HP and stamina for repeated turret-walk attempts."
                ),
                "tips": [
                    "PLATE MODES: Hard (damage reduction, slower), Sharpened (damage spike on hit), "
                    "Rounded (knockback). Use Hard mode when soaking; Sharpened for PvP.",
                    "Stego natural armor plating provides passive damage reduction — "
                    "stack HP and rely on the reduction to stretch survival.",
                    "Ideal for solo soaking auto-turrets — tank turrets while team demolishes.",
                    "Platform saddle allows structure placement for raiding operations.",
                    "Saddle: 60+ armor sufficient for soaker role; 90+ for advanced scenarios.",
                    "Pair with Yutyrannus fear roar to clear wild tames from soak path.",
                ],
            },
            "Soaker": {
                "priority": "Health > Stamina > Melee",
                "target_stats": {
                    "Health":  "40,000+ HP  (absolute priority)",
                    "Stamina": "3,000  (walk-in, walk-out, repeat)",
                    "Melee":   "Default",
                    "Weight":  "Default",
                },
                "level_split": "60 pts → Health  |  24 pts → Stamina  |  4 pts → Melee",
                "tips": [
                    "Rotate 3+ Stegos to prevent any single death — turrets reload between passes.",
                    "Hard plate mode ONLY when soaking. Switch after if going offensive.",
                    "Count turret shots to estimate ammo depletion — coordinate with demolition team.",
                ],
            },
        },
    },

    # ===================================================================
    # MEGATHERIUM  — Broodmother specialist
    # ===================================================================
    "megatherium": {
        "display_name": "Megatherium",
        "color": 0x9B59B6,  # Purple — specialist boss role
        "roles": {
            "General Meta": {
                "priority": "Melee > Health > Stamina",
                "target_stats": {
                    "Health":  "25,000 – 35,000 HP",
                    "Stamina": "2,000",
                    "Melee":   "1,200% – 1,600%  (pre-bug-bonus; ~3,000%+ effective vs insects)",
                    "Weight":  "Default",
                },
                "level_split": (
                    "44 pts → Melee  |  40 pts → Health  |  4 pts → Stamina\n"
                    "Bug-kill bonus multiplies effective melee — melee investment returns "
                    "250%+ bonus damage in Broodmother arena."
                ),
                "tips": [
                    "BUG BONUS: Killing an insect grants ~2.5x melee multiplier buff temporarily. "
                    "Broodmother's spiderlings constantly trigger this — Megatherium DPS is unmatched there.",
                    "MANDATORY for alpha Broodmother — no other tame compares in that arena.",
                    "Saddle: 70+ armor minimum; 90+ for alpha tier.",
                    "Pair with Yutyrannus courage roar — +25% damage stacks additively with bug bonus.",
                    "NOT recommended for Dragon or Megapithecus — use Rex/Theri for those.",
                    "Gathers organic polymer passively; useful for organic poly farming runs.",
                ],
            },
            "Boss / Raiding": {
                "priority": "Melee > Health > Stamina",
                "target_stats": {
                    "Health":  "30,000 – 40,000 HP",
                    "Stamina": "2,000",
                    "Melee":   "1,500%+",
                    "Weight":  "Default",
                },
                "level_split": "50 pts → Melee  |  34 pts → Health  |  4 pts → Stamina",
                "tips": [
                    "Alpha Broodmother: 19 Megatheriums + 1 Yutyrannus = standard alpha meta.",
                    "Ensure all Megatheriums are fully imprinted — bonus is critical here.",
                ],
            },
        },
    },

    # ===================================================================
    # RHYNIOGNATHA  — stealth saboteur / unique utility
    # ===================================================================
    "rhyniognatha": {
        "display_name": "Rhyniognatha",
        "color": 0x1ABC9C,  # Teal — unique/stealth utility
        "roles": {
            "General Meta": {
                "priority": "Health > Stamina > Melee",
                "target_stats": {
                    "Health":  "15,000 – 25,000 HP",
                    "Stamina": "3,000+  (sustained flight and repositioning)",
                    "Melee":   "800% – 1,200%",
                    "Weight":  "Default",
                },
                "level_split": (
                    "40 pts → Stamina  |  30 pts → Health  |  18 pts → Melee\n"
                    "Stealth utility role — stamina enables sustained aerial operations."
                ),
                "tips": [
                    "IMPLANT MECHANIC: Can implant larva inside players/tames — "
                    "triggers damage over time effect. Unique sabotage tool in PvP.",
                    "Immune to most trap-based containment — bypasses gates via flight.",
                    "Fast aerial mount for scouting, escaping, and infiltration.",
                    "NOT a frontline DPS mount — strictly utility/disruption role.",
                    "Breed for high base stamina; most domestic levels into stamina.",
                    "Saddle provides rider protection — prioritize getting one early.",
                ],
            },
        },
    },

    # ===================================================================
    # PYROMANE  — fire AOE / sustained damage dealer
    # ===================================================================
    "pyromane": {
        "display_name": "Pyromane",
        "color": 0xE67E22,  # Orange — fire damage specialist
        "roles": {
            "General Meta": {
                "priority": "Melee > Health > Stamina",
                "target_stats": {
                    "Health":  "20,000 – 30,000 HP",
                    "Stamina": "2,000",
                    "Melee":   "1,200% – 1,600%  (amplifies fire breath damage)",
                    "Weight":  "Default",
                },
                "level_split": (
                    "44 pts → Melee  |  40 pts → Health  |  4 pts → Stamina\n"
                    "Fire breath damage scales with melee — prioritize heavily."
                ),
                "tips": [
                    "Fire breath deals sustained DOT (burn) — melee amplifies both impact and burn ticks.",
                    "Highly effective against wooden and thatch structures in raids.",
                    "AOE fire spread — position carefully to avoid friendly fire on structures.",
                    "Pyromane is a relatively new meta tame; data may evolve with patches.",
                    "Saddle: 70+ armor recommended for frontline use.",
                    "Combine with Giga or Carcha for fire-softening before melee engagement.",
                ],
            },
            "PvP Main": {
                "priority": "Melee > Stamina > Health",
                "target_stats": {
                    "Health":  "25,000 HP",
                    "Stamina": "2,500  (sustained fire breath)",
                    "Melee":   "1,500%+",
                    "Weight":  "Default",
                },
                "level_split": "50 pts → Melee  |  30 pts → Stamina  |  8 pts → Health",
                "tips": [
                    "Strafe around structures — fire breath has arc coverage.",
                    "Pair with Carcha: Pyromane softens targets, Carcha closes for melee finish.",
                ],
            },
        },
    },

    # ===================================================================
    # ANKYLOSAURUS  — metal / crystal / obsidian harvest
    # ===================================================================
    "ankylosaurus": {
        "display_name": "Ankylosaurus",
        "color": 0x7F8C8D,  # Gray — resource utility
        "roles": {
            "General Meta": {
                "priority": "Weight > Melee > Health",
                "target_stats": {
                    "Health":  "15,000 – 20,000 HP  (survivability en route)",
                    "Stamina": "Default",
                    "Melee":   "600% – 1,000%  (harvest yield multiplier)",
                    "Weight":  "5,000 – 8,000  (carry heavy ore loads)",
                },
                "level_split": (
                    "50 pts → Weight  |  24 pts → Melee  |  14 pts → Health\n"
                    "Harvest role: weight is king. Melee secondary for yield."
                ),
                "tips": [
                    "Harvests metal, crystal, obsidian, and oil at high efficiency.",
                    "Tail swing has small attack radius — position directly on nodes.",
                    "Requires an Argentavis or Quetzal to transport (too slow to self-deliver).",
                    "Anky does NOT need mutations for a farm role — straight breed for weight stat.",
                    "Pair with Doedicurus for full stone + metal farming operation.",
                    "Use on metal-rich mountains: Volcano (Island), mountain ranges (Aberration).",
                ],
            },
            "Harvest / Utility": {
                "priority": "Weight > Melee > Health",
                "target_stats": {
                    "Health":  "12,000 HP",
                    "Stamina": "Default",
                    "Melee":   "800%+",
                    "Weight":  "8,000+",
                },
                "level_split": "60 pts → Weight  |  20 pts → Melee  |  8 pts → Health",
                "tips": [
                    "Dedicated farm Anky: max weight line tames only.",
                    "Stack x Ankys for raid supply — 3 trips fills a vault with metal.",
                ],
            },
        },
    },

    # ===================================================================
    # DOEDICURUS  — stone / flint harvest specialist
    # ===================================================================
    "doedicurus": {
        "display_name": "Doedicurus",
        "color": 0x95A5A6,  # Light Gray — resource utility
        "roles": {
            "General Meta": {
                "priority": "Weight > Melee > Health",
                "target_stats": {
                    "Health":  "10,000 – 15,000 HP",
                    "Stamina": "Default  (Doed rolls — no stamina drain)",
                    "Melee":   "500% – 800%  (stone yield multiplier)",
                    "Weight":  "5,000 – 8,000",
                },
                "level_split": (
                    "60 pts → Weight  |  20 pts → Melee  |  8 pts → Health\n"
                    "Pure farm role — weight dominates."
                ),
                "tips": [
                    "Stone harvest best in class — no other creature comes close for stone efficiency.",
                    "ROLLING MECHANIC: Doed rolls into a ball for defense; also allows cargo transport.",
                    "Pair with Argentavis carry to transport Doed to remote stone-rich zones.",
                    "Use near base for auto-stone collection from rock nodes.",
                    "Does NOT need mutations — breed for a clean weight stat line.",
                    "Combine with Ankylosaurus for full mineral operations (stone + metal).",
                ],
            },
            "Harvest / Utility": {
                "priority": "Weight > Melee",
                "target_stats": {
                    "Health":  "10,000 HP",
                    "Stamina": "Default",
                    "Melee":   "600%+",
                    "Weight":  "8,000+",
                },
                "level_split": "70 pts → Weight  |  14 pts → Melee  |  4 pts → Health",
                "tips": [
                    "Dedicated farm Doed: max weight line only. No mutations needed.",
                ],
            },
        },
    },

    # ===================================================================
    # SHADOWMANE  — stealth assassin / alpha disruption
    # ===================================================================
    "shadowmane": {
        "display_name": "Shadowmane",
        "color": 0x8E44AD,  # Purple — stealth/assassin
        "roles": {
            "General Meta": {
                "priority": "Melee > Health > Stamina",
                "target_stats": {
                    "Health":  "20,000 – 30,000 HP",
                    "Stamina": "2,500  (teleport/sprint stamina cost is high)",
                    "Melee":   "1,200% – 1,800%",
                    "Weight":  "Default",
                },
                "level_split": (
                    "44 pts → Melee  |  36 pts → Health  |  8 pts → Stamina\n"
                    "Teleport ability drains stamina heavily — invest accordingly."
                ),
                "tips": [
                    "TELEPORT STRIKE: Instant-gap-close blink strike — can one-shot dismount riders.",
                    "Stealth mode (swimming/submerging) grants invisibility — ideal for ambushes.",
                    "Shadowmane pack bonus: each additional Shadowmane nearby increases stats.",
                    "Requires fish to tame — passive tame only (sleep feeding).",
                    "Gender-specific buff: males provide group buff, females provide stealth uptime.",
                    "Counter to Shadowmane: turrets on render — they bypass walls.",
                ],
            },
            "PvP Main": {
                "priority": "Melee > Stamina > Health",
                "target_stats": {
                    "Health":  "22,000 HP",
                    "Stamina": "3,000",
                    "Melee":   "1,600%+",
                    "Weight":  "Default",
                },
                "level_split": "50 pts → Melee  |  30 pts → Stamina  |  8 pts → Health",
                "tips": [
                    "Pack of 5+ Shadowmanes with stacked pack bonus = alpha-tier raid disruption.",
                    "Target enemy riders first — teleport strike dismounts reliably.",
                    "Retreat into water to re-stealth and re-engage.",
                ],
            },
        },
    },

    # ===================================================================
    # MANAGARMR  — aerial hyper-mobility
    # ===================================================================
    "managarmr": {
        "display_name": "Managarmr",
        "color": 0x2980B9,  # Dark Blue — mobility/aerial
        "roles": {
            "General Meta": {
                "priority": "Stamina > Melee > Health",
                "target_stats": {
                    "Health":  "15,000 – 25,000 HP",
                    "Stamina": "4,000+  (ice dash / jump charges rely on stamina)",
                    "Melee":   "1,000% – 1,400%  (ice breath scales with melee)",
                    "Weight":  "Default",
                },
                "level_split": (
                    "50 pts → Stamina  |  24 pts → Melee  |  14 pts → Health\n"
                    "Stamina is the primary stat — Mana is useless without sustained dash charges."
                ),
                "tips": [
                    "ICE BREATH: Freezes targets in place — invaluable for pin-down PvP.",
                    "Triple-jump + long-distance dash enables vertical combat no other mount matches.",
                    "Weak in stamina-drained state — stay above 50% stamina for emergency escape.",
                    "Extremely effective for sniping riders off enemy tames mid-fight.",
                    "ASA nerf awareness: confirm current dash/freeze behavior in live patch notes.",
                    "Best paired with a base-line ground mount (Giga/Carcha) — Mana is support/disrupt.",
                    "Saddle: 50+ armor; not a frontline tank mount.",
                ],
            },
            "PvP Main": {
                "priority": "Stamina > Melee > Health",
                "target_stats": {
                    "Health":  "20,000 HP",
                    "Stamina": "5,000+",
                    "Melee":   "1,200%+",
                    "Weight":  "Default",
                },
                "level_split": "60 pts → Stamina  |  20 pts → Melee  |  8 pts → Health",
                "tips": [
                    "Recharge stamina by landing — never hover static in combat.",
                    "Ice breath spam into Carcha charge = devastating freeze-into-shred combo.",
                ],
            },
        },
    },
}


# ---------------------------------------------------------------------------
# VALID ROLE CHOICES  — exposed to app_commands.Choice list
# ---------------------------------------------------------------------------
VALID_ROLES: list[str] = [
    "General Meta",
    "PvP Main",
    "Boss / Raiding",
    "Harvest / Utility",
    "Soaker",
]


# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def resolve_tame(query: str) -> str | None:
    """
    Normalize a user input string to a canonical tame key.
    Returns None if no match found.
    """
    normalized = query.strip().lower()
    canonical = TAME_ALIASES.get(normalized)
    if canonical and canonical in TAME_DATABASE:
        return canonical
    return None


def get_tame_data(key: str, role: str = "General Meta") -> dict | None:
    """
    Retrieve the stat block for a given canonical tame key + role.
    Falls back to 'General Meta' if the requested role isn't defined for that tame.
    Returns None if the tame key doesn't exist.
    """
    tame = TAME_DATABASE.get(key)
    if not tame:
        return None

    roles = tame["roles"]
    role_data = roles.get(role) or roles.get("General Meta")
    return {
        "display_name": tame["display_name"],
        "color": tame["color"],
        "role": role if role in roles else "General Meta",
        **role_data,
    }


def list_tame_display_names() -> list[str]:
    """Return all canonical display names (for autocomplete)."""
    return [v["display_name"] for v in TAME_DATABASE.values()]


def search_tames(query: str) -> list[str]:
    """
    Fuzzy-ish search: return display names whose key or display_name
    contains the query substring. Used for autocomplete suggestions.
    """
    q = query.strip().lower()
    matches = []
    for key, data in TAME_DATABASE.items():
        if q in key or q in data["display_name"].lower():
            matches.append(data["display_name"])
    return matches
