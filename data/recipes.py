"""
Module: data/recipes.py
Description: Endgame consumable crafting data for ARK: Survival Ascended.
             Quantities are baseline estimates — verify against current patch notes.
Author: pwnedByJT
"""

# ---------------------------------------------------------------------------
# RECIPE DATABASE
#
# Schema per entry:
#   display_name : str        — shown in embed title
#   color        : int        — hex embed color
#   crafted_in   : str        — crafting station
#   ingredients  : list[str]  — exact ingredient lines (qty x item)
#   effects      : list[str]  — max 3: combat/utility effects + cooldown
#   notes        : list[str]  — max 2: decay, timing, deployment tips
# ---------------------------------------------------------------------------
RECIPE_DATABASE: dict[str, dict] = {

    "veggie_cake": {
        "display_name": "Veggie Cake",
        "color": 0x27AE60,
        "crafted_in": "Industrial Cooker  (requires water source)",
        "ingredients": [
            "5x  Sap",
            "4x  Giant Bee Honey",
            "20x Fiber",
            "10x Longrass",
            "10x Rockarrot",
            "10x Citronal",
            "10x Savoroot",
            "1x  Cooked Meat",
        ],
        "effects": [
            "• Heals 10% max HP (cap: 2,100 HP) over 30 seconds.",
            "• Provides herbivore food replenishment — reduces starvation during boss fights.",
            "• 30-second cooldown between uses per creature.",
        ],
        "notes": [
            "• Spoils in 5h (inventory) / 20h (trough) / 2d (Preserving Bin).",
            "• Primary healing item for boss Therizinos. Stock 5–10 per tame per fight.",
        ],
    },

    "mindwipe": {
        "display_name": "Mindwipe Tonic",
        "color": 0x8E44AD,
        "crafted_in": "Cooking Pot or Industrial Cooker  (requires water source)",
        "ingredients": [
            "2x  Narcotic",
            "2x  Stimulant",
            "20x Mejoberry",
            "10x Tintoberry",
            "10x Azulberry",
            "10x Amarberry",
            "5x  Rare Flower",
            "5x  Rare Mushroom",
            "1x  Cooked Prime Meat",
            "2x  Cooked Prime Fish Meat",
        ],
        "effects": [
            "• Resets ALL domestic stat points and engrams — full respec.",
            "• Character level is NOT reset. Only spent points are returned.",
            "• 1-use per player (cooldown resets daily at midnight UTC).",
        ],
        "notes": [
            "• Spoils in 5 minutes in player inventory — use immediately after crafting.",
            "• Use before boss runs to optimize survivor stats (Health > Stamina).",
        ],
    },

    "shadow_steak": {
        "display_name": "Shadow Steak Saute",
        "color": 0x1A1A2E,
        "crafted_in": "Cooking Pot or Industrial Cooker  (requires water source)",
        "ingredients": [
            "4x  Cooked Prime Meat",
            "4x  Cooked Prime Fish Meat",
            "10x Rockarrot",
            "10x Longrass",
            "10x Savoroot",
            "10x Citronal",
            "20x Mejoberry",
            "10x Rare Mushroom",
            "2x  Giant Bee Honey",
        ],
        "effects": [
            "• Grants Night Vision effect for 180 seconds.",
            "• Increases hypothermal insulation (+50) and hypothermal insulation (+50).",
            "• Reduces weapon sway — improved accuracy at range for 3 minutes.",
        ],
        "notes": [
            "• Spoils in 5 minutes (inventory) / 20 minutes (Preserving Bin).",
            "• Essential for night raids — full vision without torch (no position give-away).",
        ],
    },

    "medical_brew": {
        "display_name": "Medical Brew",
        "color": 0xE74C3C,
        "crafted_in": "Cooking Pot or Industrial Cooker  (requires water source)",
        "ingredients": [
            "20x Tintoberry",
            "2x  Narcotic",
        ],
        "effects": [
            "• Heals player 40 HP over 5 seconds.",
            "• Stacks with multiple consecutive uses — spammable.",
            "• No buff timer — instant consume, instant tick.",
        ],
        "notes": [
            "• Spoils in 2 hours (inventory). Craft in large batches and store in fridge.",
            "• Carry 20+ per raid. Fastest player heal available outside of Daeodon.",
        ],
    },

    "focal_chili": {
        "display_name": "Focal Chili",
        "color": 0xE67E22,
        "crafted_in": "Cooking Pot or Industrial Cooker  (requires water source)",
        "ingredients": [
            "9x  Cooked Meat",
            "10x Citronal",
            "10x Rockarrot",
            "10x Savoroot",
            "10x Longrass",
            "20x Amarberry",
        ],
        "effects": [
            "• +25% crafting speed for 15 minutes.",
            "• Reduces crafting skill investment needed — stack with stat allocation.",
            "• Also provides minor hypothermal insulation (+50).",
        ],
        "notes": [
            "• Spoils in 5 minutes (inventory). Craft fresh before long crafting sessions.",
            "• Use before mass-crafting explosives, saddles, or tek gear.",
        ],
    },

    "battle_tartare": {
        "display_name": "Battle Tartare",
        "color": 0xC0392B,
        "crafted_in": "Cooking Pot or Industrial Cooker  (requires water source)",
        "ingredients": [
            "5x  Raw Prime Meat",
            "5x  Raw Prime Fish Meat",
            "10x Mejoberry",
            "10x Narcoberry",
            "10x Stimberry",
            "2x  Giant Bee Honey",
            "5x  Rare Flower",
        ],
        "effects": [
            "• +60% melee damage for 180 seconds.",
            "• +40 movement speed.",
            "• Health drain: -0.45 HP/sec for duration — do NOT use if already injured.",
        ],
        "notes": [
            "• Spoils in 5 minutes. Only consume at full health before initiating a fight.",
            "• Stack with Yuty courage roar (+25%) for maximum burst DPS window.",
        ],
    },
}

# Alias map for autocomplete normalization
RECIPE_ALIASES: dict[str, str] = {
    "veggie cake": "veggie_cake",
    "veggie_cake": "veggie_cake",
    "cake": "veggie_cake",
    "vc": "veggie_cake",

    "mindwipe": "mindwipe",
    "mindwipe tonic": "mindwipe",
    "respec": "mindwipe",

    "shadow steak": "shadow_steak",
    "shadow_steak": "shadow_steak",
    "shadow steak saute": "shadow_steak",
    "shadow": "shadow_steak",
    "steak": "shadow_steak",

    "medical brew": "medical_brew",
    "medical_brew": "medical_brew",
    "med brew": "medical_brew",
    "medbrew": "medical_brew",

    "focal chili": "focal_chili",
    "focal_chili": "focal_chili",
    "chili": "focal_chili",

    "battle tartare": "battle_tartare",
    "battle_tartare": "battle_tartare",
    "tartare": "battle_tartare",
    "tart": "battle_tartare",
}

# Validation
for _key, _data in RECIPE_DATABASE.items():
    assert len(_data.get("effects", [])) <= 3,  f"recipes/{_key}: effects > 3"
    assert len(_data.get("notes", [])) <= 2,    f"recipes/{_key}: notes > 2"
    assert len(_data.get("ingredients", [])) > 0, f"recipes/{_key}: no ingredients"


def resolve_recipe(query: str) -> str | None:
    return RECIPE_ALIASES.get(query.strip().lower())


def get_recipe(key: str) -> dict | None:
    return RECIPE_DATABASE.get(key)


def list_recipe_names() -> list[str]:
    return [v["display_name"] for v in RECIPE_DATABASE.values()]
