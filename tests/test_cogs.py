"""
tests/test_cogs.py
Unit tests for ARKintel — data layer, DatabaseEngine, and cog instantiation.
No Discord token or network access required.
"""

import os
import pytest
import discord
from discord.ext import commands

from data.raid_data import (
    STRUCTURE_DATABASE,
    STRUCTURE_ALIASES,
    calculate_explosives,
    resolve_structure,
    list_structure_names,
)
from data.recipes import (
    RECIPE_DATABASE,
    resolve_recipe,
    get_recipe,
    list_recipe_names,
)
from data.tame_stats import (
    TAME_DATABASE,
    resolve_tame,
    get_tame_data,
    list_tame_display_names,
)
from data.boss_data import (
    BOSS_DATABASE,
    resolve_boss,
    get_boss_data,
    list_boss_names,
)
from ARK import DatabaseEngine, Config


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def make_bot() -> commands.Bot:
    """Minimal Bot — no intents, no token, no network."""
    return commands.Bot(command_prefix="!", intents=discord.Intents.none())


# ===========================================================================
# CONFIG
# ===========================================================================

class TestConfig:
    def test_api_urls_are_https_strings(self):
        assert isinstance(Config.OFFICIAL_API, str)
        assert Config.OFFICIAL_API.startswith("https://")
        assert isinstance(Config.EVO_API, str)
        assert Config.EVO_API.startswith("https://")

    def test_file_paths_are_absolute(self):
        assert os.path.isabs(Config.MONITORS_FILE)
        assert os.path.isabs(Config.STATS_DB)
        assert os.path.isabs(Config.FAVORITES_FILE)
        assert os.path.isabs(Config.POP_ALERTS_FILE)

    def test_alert_threshold_is_positive_int(self):
        assert isinstance(Config.ALERT_THRESHOLD, int)
        assert Config.ALERT_THRESHOLD > 0


# ===========================================================================
# DATA LAYER — synchronous, zero Discord, zero network
# ===========================================================================

class TestRaidData:
    def test_database_is_not_empty(self):
        assert len(STRUCTURE_DATABASE) > 0

    def test_list_structure_names_returns_nonempty_string_list(self):
        names = list_structure_names()
        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)

    def test_resolve_by_display_name(self):
        assert resolve_structure("Metal Wall") is not None

    def test_resolve_by_lowercase_alias(self):
        assert resolve_structure("metal wall") is not None

    def test_resolve_unknown_returns_none(self):
        assert resolve_structure("notastructure_xyz") is None

    def test_calculate_explosives_returns_required_keys(self):
        canonical = resolve_structure("Metal Wall")
        result = calculate_explosives(canonical, 1)
        assert "explosives" in result
        assert "total_hp" in result
        assert "quantity" in result
        assert result["quantity"] == 1

    def test_calculate_explosives_quantity_scales_hp(self):
        canonical = resolve_structure("Metal Wall")
        r1 = calculate_explosives(canonical, 1)
        r5 = calculate_explosives(canonical, 5)
        assert r5["total_hp"] == r1["total_hp"] * 5

    def test_all_structures_have_required_schema_keys(self):
        for key, data in STRUCTURE_DATABASE.items():
            for field in ("display_name", "hp", "notes"):
                assert field in data, f"Structure '{key}' missing field '{field}'"


class TestRecipeData:
    def test_database_is_not_empty(self):
        assert len(RECIPE_DATABASE) > 0

    def test_list_recipe_names_returns_nonempty_string_list(self):
        names = list_recipe_names()
        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)

    def test_resolve_veggie_cake(self):
        assert resolve_recipe("Veggie Cake") is not None

    def test_resolve_unknown_returns_none(self):
        assert resolve_recipe("unknownitem_xyz") is None

    def test_get_recipe_has_required_schema_keys(self):
        canonical = resolve_recipe("Veggie Cake")
        data = get_recipe(canonical)
        for key in ("display_name", "ingredients", "effects", "crafted_in", "notes"):
            assert key in data, f"Recipe missing key: '{key}'"

    def test_ingredients_is_nonempty_list(self):
        canonical = resolve_recipe("Veggie Cake")
        data = get_recipe(canonical)
        assert isinstance(data["ingredients"], list)
        assert len(data["ingredients"]) > 0

    def test_all_recipes_have_required_schema_keys(self):
        for key, data in RECIPE_DATABASE.items():
            for field in ("display_name", "ingredients", "effects", "crafted_in"):
                assert field in data, f"Recipe '{key}' missing field '{field}'"


class TestTameData:
    def test_database_is_not_empty(self):
        assert len(TAME_DATABASE) > 0

    def test_list_tame_display_names_returns_nonempty_string_list(self):
        names = list_tame_display_names()
        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)

    def test_resolve_alias_giga(self):
        assert resolve_tame("giga") is not None

    def test_resolve_alias_carcha(self):
        assert resolve_tame("carcha") is not None

    def test_resolve_alias_theri(self):
        assert resolve_tame("theri") is not None

    def test_resolve_unknown_returns_none(self):
        assert resolve_tame("unknowntame_xyz") is None

    def test_get_tame_data_has_required_schema_keys(self):
        canonical = resolve_tame("giga")
        data = get_tame_data(canonical)
        for key in ("display_name", "meta", "color", "builds", "thresholds", "tips"):
            assert key in data, f"Tame data missing key: '{key}'"

    def test_builds_list_is_nonempty(self):
        canonical = resolve_tame("giga")
        data = get_tame_data(canonical)
        assert isinstance(data["builds"], list)
        assert len(data["builds"]) > 0

    def test_each_build_has_name_and_points(self):
        for canonical in TAME_DATABASE:
            data = get_tame_data(canonical)
            for build in data["builds"]:
                assert "name" in build, f"{canonical}: build missing 'name'"
                assert "points" in build, f"{canonical}: build missing 'points'"
                assert isinstance(build["points"], list)
                assert len(build["points"]) > 0

    def test_all_builds_sum_to_88_pts(self):
        """Fixed-allocation builds must sum to exactly 88 domestic points.
        Builds that contain non-numeric entries (e.g. Rex 'Dump HP until...')
        are strategy descriptions rather than fixed allocations and are skipped."""
        for canonical in TAME_DATABASE:
            data = get_tame_data(canonical)
            for build in data["builds"]:
                try:
                    total = sum(int(pt.split()[0]) for pt in build["points"])
                except ValueError:
                    continue  # strategy-description build — not a fixed numeric allocation
                assert total == 88, (
                    f"{canonical} / '{build['name']}': "
                    f"points sum to {total}, expected 88"
                )


class TestBossData:
    def test_database_is_not_empty(self):
        assert len(BOSS_DATABASE) > 0

    def test_list_boss_names_returns_nonempty_string_list(self):
        names = list_boss_names()
        assert isinstance(names, list)
        assert len(names) > 0
        assert all(isinstance(n, str) for n in names)

    def test_resolve_broodmother(self):
        assert resolve_boss("Broodmother Lysrix") is not None

    def test_resolve_unknown_returns_none(self):
        assert resolve_boss("unknownboss_xyz") is None

    def test_get_boss_data_gamma_has_required_schema_keys(self):
        canonical = resolve_boss("Broodmother Lysrix")
        data = get_boss_data(canonical, "Gamma")
        for key in ("artifacts", "tributes", "tames", "saddle", "hp_floor", "warnings"):
            assert key in data, f"Boss data missing key: '{key}'"

    def test_all_three_tiers_exist_for_every_boss(self):
        for canonical in BOSS_DATABASE:
            for tier in ("Gamma", "Beta", "Alpha"):
                data = get_boss_data(canonical, tier)
                assert data is not None, f"{canonical} missing tier '{tier}'"

    def test_artifacts_is_nonempty_list(self):
        canonical = resolve_boss("Broodmother Lysrix")
        data = get_boss_data(canonical, "Gamma")
        assert isinstance(data["artifacts"], list)
        assert len(data["artifacts"]) > 0


# ===========================================================================
# DATABASE ENGINE — async, temp file (NOT :memory: — each method opens its
# own connection, so an in-memory DB would lose the schema between calls)
# ===========================================================================

class TestDatabaseEngine:

    @pytest.fixture
    def db_path(self, tmp_path):
        return str(tmp_path / "test_stats.db")

    async def test_initialize_creates_server_stats_table(self, db_path):
        import aiosqlite
        db = DatabaseEngine(db_path)
        await db.initialize()
        async with aiosqlite.connect(db_path) as conn:
            async with conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='server_stats'"
            ) as cur:
                row = await cur.fetchone()
        assert row is not None, "server_stats table was not created"

    async def test_initialize_creates_index(self, db_path):
        import aiosqlite
        db = DatabaseEngine(db_path)
        await db.initialize()
        async with aiosqlite.connect(db_path) as conn:
            async with conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_server_time'"
            ) as cur:
                row = await cur.fetchone()
        assert row is not None, "idx_server_time index was not created"

    async def test_record_and_retrieve_stats(self, db_path):
        db = DatabaseEngine(db_path)
        await db.initialize()
        await db.record_stats("TestServer", 42, 70)
        stats = await db.get_stats("TestServer", hours=24)
        assert stats is not None
        assert stats["current"] == 42
        assert stats["peak"] == 42
        assert stats["low"] == 42
        assert stats["samples"] == 1

    async def test_get_stats_aggregates_multiple_samples(self, db_path):
        db = DatabaseEngine(db_path)
        await db.initialize()
        for count in [10, 30, 50]:
            await db.record_stats("AggServer", count, 70)
        stats = await db.get_stats("AggServer", hours=24)
        assert stats["peak"] == 50
        assert stats["low"] == 10
        assert stats["current"] == 50
        assert stats["samples"] == 3
        assert stats["avg"] == round((10 + 30 + 50) / 3, 1)

    async def test_get_stats_returns_none_for_unknown_server(self, db_path):
        db = DatabaseEngine(db_path)
        await db.initialize()
        result = await db.get_stats("DoesNotExist", hours=24)
        assert result is None

    async def test_get_timeseries_returns_none_for_empty_server(self, db_path):
        db = DatabaseEngine(db_path)
        await db.initialize()
        result = await db.get_timeseries("EmptyServer", hours=24)
        assert result is None

    async def test_get_timeseries_returns_ordered_rows(self, db_path):
        db = DatabaseEngine(db_path)
        await db.initialize()
        await db.record_stats("PopServer", 10, 70)
        await db.record_stats("PopServer", 20, 70)
        rows = await db.get_timeseries("PopServer", hours=24)
        assert rows is not None
        assert len(rows) == 2
        counts = [r[1] for r in rows]
        assert counts == [10, 20], "Timeseries should be ordered oldest-first"

    async def test_get_timeseries_excludes_old_data(self, db_path):
        """Rows older than the requested window should not appear."""
        import aiosqlite
        db = DatabaseEngine(db_path)
        await db.initialize()
        # Insert a row timestamped 48 hours ago manually
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute(
                "INSERT INTO server_stats (server_name, player_count, max_players, timestamp) "
                "VALUES (?, ?, ?, datetime('now', '-48 hours'))",
                ("StaleServer", 99, 70),
            )
            await conn.commit()
        result = await db.get_timeseries("StaleServer", hours=24)
        assert result is None, "Old rows outside the window should be excluded"


# ===========================================================================
# COG INSTANTIATION — only cogs that don't call tasks.start() in __init__
# ARKCog is excluded: its __init__ fires network task loops immediately
# ===========================================================================

class TestCogInstantiation:

    def test_tame_stats_cog_instantiates(self):
        from cogs.tame_stats_cog import TameStatsCog
        bot = make_bot()
        cog = TameStatsCog(bot)
        assert cog.bot is bot

    def test_recipe_cog_instantiates(self):
        from cogs.recipe_cog import RecipeCog
        bot = make_bot()
        cog = RecipeCog(bot)
        assert cog.bot is bot

    def test_raid_calc_cog_instantiates(self):
        from cogs.raid_calc_cog import RaidCalcCog
        bot = make_bot()
        cog = RaidCalcCog(bot)
        assert cog.bot is bot

    def test_boss_check_cog_instantiates(self):
        from cogs.boss_check_cog import BossCheckCog
        bot = make_bot()
        cog = BossCheckCog(bot)
        assert cog.bot is bot

    def test_help_cog_instantiates(self):
        from cogs.help_cog import HelpCog
        bot = make_bot()
        cog = HelpCog(bot)
        assert cog.bot is bot

    def test_all_cogs_have_no_shared_bot_state(self):
        """Each cog should hold a reference to its own bot instance."""
        from cogs.tame_stats_cog import TameStatsCog
        from cogs.recipe_cog import RecipeCog
        bot_a = make_bot()
        bot_b = make_bot()
        cog_a = TameStatsCog(bot_a)
        cog_b = RecipeCog(bot_b)
        assert cog_a.bot is bot_a
        assert cog_b.bot is bot_b
        assert cog_a.bot is not cog_b.bot
