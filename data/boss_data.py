"""
Module: data/boss_data.py
Description: Island boss tribute requirements, recommended tame counts,
             and stat thresholds for ARK: Survival Ascended.
             Baseline estimates — verify artifact/tribute counts against
             current ASA patch before entering an arena.
Author: pwnedByJT
"""

# ---------------------------------------------------------------------------
# BOSS DATABASE (Island — base game)
#
# Schema per entry:
#   display_name  : str        — full boss name
#   color         : int        — hex embed color
#   tiers         : dict       — tier name -> tier block:
#       artifacts : list[str]  — required artifact names
#       tributes  : list[str]  — apex tribute items + quantities
#       tames     : str        — recommended army composition
#       saddle    : str        — minimum saddle armor requirement
#       hp_floor  : str        — minimum tame HP before entry
#       warnings  : list[str]  — max 2: hard restrictions or common wipe causes
# ---------------------------------------------------------------------------
BOSS_DATABASE: dict[str, dict] = {

    "broodmother": {
        "display_name": "Broodmother Lysrix",
        "color": 0x8E44AD,
        "tiers": {
            "Gamma": {
                "artifacts": [
                    "Artifact of the Hunter",
                    "Artifact of the Pack",
                    "Artifact of the Clever",
                ],
                "tributes": [
                    "10x  Argentavis Talon",
                    "10x  Sauropod Vertebra",
                    "10x  Sarco Skin",
                ],
                "tames": "8x Rex (19k+ HP)  |  1x Yutyrannus  |  1x Daeodon",
                "saddle": "Rex: 70+ armor  |  Yuty: 50+ armor",
                "hp_floor": "Rex: 19,000 HP minimum",
                "warnings": [
                    "• Broodmother spawns Araneomorphus adds — Daeodon must pulse constantly.",
                    "• Gamma is indoor arena. Gigas are NOT allowed — use Rexes or Megatheriums.",
                ],
            },
            "Beta": {
                "artifacts": [
                    "Artifact of the Hunter",
                    "Artifact of the Pack",
                    "Artifact of the Clever",
                ],
                "tributes": [
                    "15x  Argentavis Talon",
                    "15x  Sauropod Vertebra",
                    "15x  Sarco Skin",
                ],
                "tames": "14x Rex (25k+ HP)  |  1x Yutyrannus  |  1x Daeodon",
                "saddle": "Rex: 80+ armor  |  Yuty: 65+ armor",
                "hp_floor": "Rex: 25,000 HP minimum",
                "warnings": [
                    "• Beta spawns denser add waves. 2x Daeodon strongly recommended.",
                    "• Loss of Yuty mid-fight at Beta = high wipe risk. Keep it behind the line.",
                ],
            },
            "Alpha": {
                "artifacts": [
                    "Artifact of the Hunter",
                    "Artifact of the Pack",
                    "Artifact of the Clever",
                ],
                "tributes": [
                    "20x  Argentavis Talon",
                    "20x  Sauropod Vertebra",
                    "20x  Sarco Skin",
                ],
                "tames": "18x Rex (30k+ HP)  |  1x Yutyrannus  |  2x Daeodon",
                "saddle": "Rex: 90+ armor  |  Yuty: 80+ armor",
                "hp_floor": "Rex: 30,000 HP minimum  (19k absolute floor, 30k recommended)",
                "warnings": [
                    "• Alpha Broodmother: hardest of the three bosses. Do not attempt with sub-par Rexes.",
                    "• Alternatively: 18x Megatherium + 1 Yuty — bug bonus makes this the meta clear.",
                ],
            },
        },
    },

    "megapithecus": {
        "display_name": "Megapithecus",
        "color": 0xD35400,
        "tiers": {
            "Gamma": {
                "artifacts": [
                    "Artifact of the Strong",
                    "Artifact of the Devious",
                    "Artifact of the Massive",
                ],
                "tributes": [
                    "10x  Therizino Claw",
                    "10x  Megaloceros Antler",
                    "10x  Sauropod Vertebra",
                ],
                "tames": "8x Rex (19k+ HP)  |  1x Yutyrannus  |  1x Daeodon",
                "saddle": "Rex: 70+ armor",
                "hp_floor": "Rex: 19,000 HP minimum",
                "warnings": [
                    "• Megapithecus throws boulders — spread Rexes laterally to avoid AoE wipes.",
                    "• Spawns Mesopithecus adds — Daeodon handles healing, Yuty keeps them routed.",
                ],
            },
            "Beta": {
                "artifacts": [
                    "Artifact of the Strong",
                    "Artifact of the Devious",
                    "Artifact of the Massive",
                ],
                "tributes": [
                    "15x  Therizino Claw",
                    "15x  Megaloceros Antler",
                    "15x  Sauropod Vertebra",
                ],
                "tames": "14x Rex (25k+ HP)  |  1x Yutyrannus  |  1x Daeodon",
                "saddle": "Rex: 80+ armor",
                "hp_floor": "Rex: 25,000 HP minimum",
                "warnings": [
                    "• Boulder AoE damage increases at Beta. Keep Rexes spread — not clustered.",
                    "• Yuty roar uptime is critical — sustained +25% DPS shortens dangerous exposure.",
                ],
            },
            "Alpha": {
                "artifacts": [
                    "Artifact of the Strong",
                    "Artifact of the Devious",
                    "Artifact of the Massive",
                ],
                "tributes": [
                    "20x  Therizino Claw",
                    "20x  Megaloceros Antler",
                    "20x  Sauropod Vertebra",
                ],
                "tames": "18x Rex (30k+ HP)  |  1x Yutyrannus  |  2x Daeodon",
                "saddle": "Rex: 90+ armor",
                "hp_floor": "Rex: 30,000 HP minimum",
                "warnings": [
                    "• Alpha boulders hit a wide cone. Position Yuty at extreme rear.",
                    "• 2x Daeodon mandatory — sustained healing is the only way through Alpha.",
                ],
            },
        },
    },

    "dragon": {
        "display_name": "Dragon",
        "color": 0xE74C3C,
        "tiers": {
            "Gamma": {
                "artifacts": [
                    "Artifact of the Clever",
                    "Artifact of the Sky",
                    "Artifact of the Immune",
                ],
                "tributes": [
                    "10x  Argentavis Talon",
                    "10x  Pteranodon Talon",
                    "10x  Quetzal Feather",
                ],
                "tames": "8x Therizinosaurus (19k+ HP)  |  1x Yutyrannus  |  1x Daeodon",
                "saddle": "Theri: 70+ armor  |  Yuty: 50+ armor",
                "hp_floor": "Theri: 19,000 HP minimum",
                "warnings": [
                    "• DO NOT bring Rexes — Dragon fire instantly destroys them.",
                    "• Theri melee bypasses fire resistance. This is the correct tame.",
                ],
            },
            "Beta": {
                "artifacts": [
                    "Artifact of the Clever",
                    "Artifact of the Sky",
                    "Artifact of the Immune",
                ],
                "tributes": [
                    "15x  Argentavis Talon",
                    "15x  Pteranodon Talon",
                    "15x  Quetzal Feather",
                ],
                "tames": "14x Therizinosaurus (25k+ HP)  |  1x Yutyrannus  |  1x Daeodon",
                "saddle": "Theri: 80+ armor  |  Yuty: 65+ armor",
                "hp_floor": "Theri: 25,000 HP minimum",
                "warnings": [
                    "• Beta Dragon flies more often — Theris can't reach it. Wait for land phases.",
                    "• Veggie Cakes: bring 8–10 per Theri. Cake heals cap at 21k HP.",
                ],
            },
            "Alpha": {
                "artifacts": [
                    "Artifact of the Clever",
                    "Artifact of the Sky",
                    "Artifact of the Immune",
                ],
                "tributes": [
                    "20x  Argentavis Talon",
                    "20x  Pteranodon Talon",
                    "20x  Quetzal Feather",
                ],
                "tames": "19x Therizinosaurus (30k+ HP)  |  1x Yutyrannus  |  2x Daeodon",
                "saddle": "Theri: 90+ armor  |  Yuty: 80+ armor",
                "hp_floor": "Theri: 30,000 HP minimum  (19k absolute floor)",
                "warnings": [
                    "• Alpha Dragon has 15-minute timer. Exceed it = automatic boss disappear + no loot.",
                    "• Maximize Yuty roar uptime — faster kills reduce fire exposure window.",
                ],
            },
        },
    },
}

BOSS_ALIASES: dict[str, str] = {
    "broodmother": "broodmother",
    "brood": "broodmother",
    "spider": "broodmother",
    "lysrix": "broodmother",

    "megapithecus": "megapithecus",
    "mega": "megapithecus",
    "monkey": "megapithecus",
    "gorilla": "megapithecus",

    "dragon": "dragon",
    "drag": "dragon",
}

TIER_ALIASES: dict[str, str] = {
    "gamma": "Gamma",
    "g": "Gamma",
    "easy": "Gamma",

    "beta": "Beta",
    "b": "Beta",
    "medium": "Beta",

    "alpha": "Alpha",
    "a": "Alpha",
    "hard": "Alpha",
}

# Validation
for _key, _data in BOSS_DATABASE.items():
    for _tier, _block in _data["tiers"].items():
        assert len(_block.get("warnings", [])) <= 2, f"boss/{_key}/{_tier}: warnings > 2"


def resolve_boss(query: str) -> str | None:
    return BOSS_ALIASES.get(query.strip().lower())


def resolve_tier(query: str) -> str | None:
    return TIER_ALIASES.get(query.strip().lower())


def get_boss_data(boss_key: str, tier: str) -> dict | None:
    boss = BOSS_DATABASE.get(boss_key)
    if not boss:
        return None
    tier_block = boss["tiers"].get(tier)
    if not tier_block:
        return None
    return {
        "display_name": boss["display_name"],
        "color": boss["color"],
        "tier": tier,
        **tier_block,
    }


def list_boss_names() -> list[str]:
    return [v["display_name"] for v in BOSS_DATABASE.values()]
