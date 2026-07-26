"""
Module: data/raid_data.py
Description: ASA structure HP and explosive damage values for /raid-calc.
             All values are baseline estimates for official rates.
             VERIFY against current patch — ASA values may differ from ASE.
Author: pwnedByJT
"""

import math

# ---------------------------------------------------------------------------
# STRUCTURE DATABASE
#
# Schema per entry:
#   display_name : str  — shown in embed
#   hp           : int  — structure HP on official rates
#   notes        : str  — single-line context (material type, resistance notes)
# ---------------------------------------------------------------------------
STRUCTURE_DATABASE: dict[str, dict] = {
    "metal_wall": {
        "display_name": "Metal Wall",
        "hp": 10_000,
        "notes": "Standard metal tier. Most common raid target.",
    },
    "tek_wall": {
        "display_name": "Tek Wall",
        "hp": 100_000,
        "notes": "10x durability vs metal. Dominant in alpha bases.",
    },
    "metal_ceiling": {
        "display_name": "Metal Ceiling",
        "hp": 10_000,
        "notes": "Same as Metal Wall. Roof breach entry point.",
    },
    "metal_foundation": {
        "display_name": "Metal Foundation",
        "hp": 15_000,
        "notes": "Slightly tankier than walls. Floor breach.",
    },
    "metal_door": {
        "display_name": "Metal Door",
        "hp": 3_000,
        "notes": "Weakest metal tier piece. Always breach here first.",
    },
    "metal_gate": {
        "display_name": "Metal Dino Gate",
        "hp": 50_000,
        "notes": "High HP. Prioritize C4 for large gate breaches.",
    },
    "vault": {
        "display_name": "Metal Vault",
        "hp": 50_000,
        "notes": "Extremely slow to destroy. Allocate C4, not RPGs.",
    },
    "heavy_turret": {
        "display_name": "Heavy Auto Turret",
        "hp": 10_000,
        "notes": "Disabled by EMP grenades. C4 or RPG recommended.",
    },
    "auto_turret": {
        "display_name": "Auto Turret",
        "hp": 5_000,
        "notes": "Weaker than heavy. One-shot viable with 5x C4.",
    },
    "tek_turret": {
        "display_name": "Tek Turret",
        "hp": 20_000,
        "notes": "High HP, high DPS. Must be a priority target.",
    },
    "tek_generator": {
        "display_name": "Tek Generator",
        "hp": 100_000,
        "notes": "Destroying this cuts Tek Turrets and Tek doors.",
    },
    "behemoth_gate": {
        "display_name": "Behemoth Metal Gate",
        "hp": 60_000,
        "notes": "Largest gate variant. Primary base perimeter access.",
    },
}

# ---------------------------------------------------------------------------
# EXPLOSIVE DATABASE
#
# Schema per entry:
#   display_name   : str  — shown in embed
#   damage         : int  — damage per detonation vs structures (official rates)
#   materials      : dict — raw material cost to CRAFT one unit
#   notes          : str  — one-line context
#
# VERIFY damage values against current ASA patch before live use.
# ---------------------------------------------------------------------------
EXPLOSIVE_DATABASE: dict[str, dict] = {
    "c4": {
        "display_name": "C4 Charge",
        "damage": 1_050,
        "materials": {
            "Polymer":     10,
            "Gunpowder":   50,
            "Crystal":     10,
            "Fiber":       50,
            "Cementing Paste": 1,
        },
        "notes": "Most cost-efficient vs static structures.",
    },
    "rpg": {
        "display_name": "Rocket Propelled Grenade",
        "damage": 1_050,
        "materials": {
            "Polymer":       2,
            "Metal Ingot":   15,
            "Gunpowder":     60,
            "Crystal":       2,
            "Cementing Paste": 5,
            "Gasoline":      1,
        },
        "notes": "Same damage as C4. Better for mobile targets.",
    },
    "grenade": {
        "display_name": "Grenade",
        "damage": 375,
        "materials": {
            "Metal Ingot":  5,
            "Gunpowder":    20,
            "Fiber":        20,
            "Flint":        2,
        },
        "notes": "Low damage — use only for turret ammo drain or player kills.",
    },
}

# Alias maps
STRUCTURE_ALIASES: dict[str, str] = {
    "metal wall": "metal_wall",
    "metal_wall": "metal_wall",
    "wall": "metal_wall",

    "tek wall": "tek_wall",
    "tek_wall": "tek_wall",

    "metal ceiling": "metal_ceiling",
    "metal_ceiling": "metal_ceiling",
    "ceiling": "metal_ceiling",

    "metal foundation": "metal_foundation",
    "metal_foundation": "metal_foundation",
    "foundation": "metal_foundation",

    "metal door": "metal_door",
    "metal_door": "metal_door",
    "door": "metal_door",

    "metal gate": "metal_gate",
    "metal_gate": "metal_gate",
    "dino gate": "metal_gate",

    "vault": "vault",
    "metal vault": "vault",

    "heavy turret": "heavy_turret",
    "heavy_turret": "heavy_turret",
    "heavy": "heavy_turret",

    "auto turret": "auto_turret",
    "auto_turret": "auto_turret",
    "turret": "auto_turret",

    "tek turret": "tek_turret",
    "tek_turret": "tek_turret",

    "tek generator": "tek_generator",
    "tek_generator": "tek_generator",
    "generator": "tek_generator",

    "behemoth gate": "behemoth_gate",
    "behemoth_gate": "behemoth_gate",
    "behemoth": "behemoth_gate",
}


# ---------------------------------------------------------------------------
# CALCULATOR
# ---------------------------------------------------------------------------

def calculate_explosives(structure_key: str, quantity: int) -> dict | None:
    """
    Returns a breakdown of all explosive options to destroy `quantity`
    of the given structure, plus raw material totals for each option.
    Returns None if structure_key is invalid.
    """
    structure = STRUCTURE_DATABASE.get(structure_key)
    if not structure:
        return None

    total_hp = structure["hp"] * quantity
    results = {}

    for exp_key, exp in EXPLOSIVE_DATABASE.items():
        count = math.ceil(total_hp / exp["damage"])
        raw = {mat: amt * count for mat, amt in exp["materials"].items()}
        results[exp_key] = {
            "display_name": exp["display_name"],
            "count": count,
            "raw_materials": raw,
            "notes": exp["notes"],
        }

    return {
        "structure": structure,
        "quantity": quantity,
        "total_hp": total_hp,
        "explosives": results,
    }


def resolve_structure(query: str) -> str | None:
    return STRUCTURE_ALIASES.get(query.strip().lower())


def list_structure_names() -> list[str]:
    return [v["display_name"] for v in STRUCTURE_DATABASE.values()]
