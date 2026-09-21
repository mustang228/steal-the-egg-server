import os
import json
import sqlite3
from pathlib import Path
from datetime import date, datetime, timedelta
# =========================================================
# DATABASE PATH
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
# Путь к базе можно задать переменной окружения DB_PATH
# (например /data/players.db на постоянном диске Render).
DB_PATH = Path(
    os.getenv(
        "DB_PATH",
        str(BASE_DIR / "players.db")
    )
)
DB_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)
# =========================================================
# CONNECTION
# =========================================================
def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30
    )
    conn.row_factory = sqlite3.Row
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )
    return conn
# =========================================================
# HELPERS
# =========================================================
def _table_exists(conn, table_name):
    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,)
    ).fetchone()
    return row is not None
def _column_exists(
    conn,
    table_name,
    column_name
):
    if not _table_exists(
        conn,
        table_name
    ):
        return False
    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()
    return any(
        column["name"] == column_name
        for column in columns
    )
def _add_column(
    conn,
    table_name,
    column_definition
):
    column_name = (
        column_definition
        .split()[0]
    )
    if not _column_exists(
        conn,
        table_name,
        column_name
    ):
        conn.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_definition}
            """
        )
# =========================================================
# DATABASE INITIALIZATION
# =========================================================
def init_database():
    conn = get_connection()
    try:
        # =================================================
        # PLAYERS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                tap_coins INTEGER NOT NULL DEFAULT 0,
                egg_coins INTEGER NOT NULL DEFAULT 0,
                username TEXT DEFAULT '',
                blocked INTEGER NOT NULL DEFAULT 0,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 1,
                login_streak INTEGER NOT NULL DEFAULT 0,
                last_login TEXT,
                daily_bonus_date TEXT,
                task_date TEXT,
                task_taps INTEGER NOT NULL DEFAULT 0,
                task_games INTEGER NOT NULL DEFAULT 0,
                task_eggs INTEGER NOT NULL DEFAULT 0,
                boss_damage INTEGER NOT NULL DEFAULT 0,
                avatar TEXT DEFAULT '🥚'
            )
            """
        )
        # =================================================
        # PLAYERS MIGRATIONS
        # =================================================
        _add_column(
            conn,
            "players",
            "tap_coins INTEGER NOT NULL DEFAULT 0"
        )
        _add_column(
            conn,
            "players",
            "egg_coins INTEGER NOT NULL DEFAULT 0"
        )
        _add_column(
            conn,
            "players",
            "username TEXT DEFAULT ''"
        )
        _add_column(
            conn,
            "players",
            "blocked INTEGER NOT NULL DEFAULT 0"
        )
        _add_column(
            conn,
            "players",
            "xp INTEGER NOT NULL DEFAULT 0"
        )
        _add_column(
            conn,
            "players",
            "level INTEGER NOT NULL DEFAULT 1"
        )
        _add_column(
            conn,
            "players",
            "login_streak INTEGER NOT NULL DEFAULT 0"
        )
        _add_column(
            conn,
            "players",
            "last_login TEXT"
        )
        _add_column(
            conn,
            "players",
            "daily_bonus_date TEXT"
        )
        _add_column(
            conn,
            "players",
            "task_date TEXT"
        )
        _add_column(
            conn,
            "players",
            "task_taps INTEGER NOT NULL DEFAULT 0"
        )
        _add_column(
            conn,
            "players",
            "task_games INTEGER NOT NULL DEFAULT 0"
        )
        _add_column(
            conn,
            "players",
            "task_eggs INTEGER NOT NULL DEFAULT 0"
        )
        _add_column(
            conn,
            "players",
            "boss_damage INTEGER NOT NULL DEFAULT 0"
        )
        _add_column(
            conn,
            "players",
            "avatar TEXT DEFAULT '🥚'"
        )
        # =================================================
        # PLAYER EGGS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_eggs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                egg_id INTEGER NOT NULL
            )
            """
        )
        # =================================================
        # PLAYER ITEMS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL
            )
            """
        )
        # =================================================
        # ACHIEVEMENTS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                achievement_id INTEGER NOT NULL
            )
            """
        )
        # =================================================
        # DAILY TASK CLAIMS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_task_claims (
                user_id INTEGER NOT NULL,
                task_date TEXT NOT NULL,
                task_id TEXT NOT NULL,
                PRIMARY KEY (
                    user_id,
                    task_date,
                    task_id
                )
            )
            """
        )
        # =================================================
        # EGG TYPES
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS egg_types (
                egg_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                rarity_order INTEGER NOT NULL DEFAULT 0,
                marketable INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        # =================================================
        # PLAYER CHESTS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_chests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chest_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # =================================================
        # PET TYPES
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pets (
                pet_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                rarity TEXT NOT NULL,
                bonus_type TEXT NOT NULL,
                bonus_value REAL NOT NULL DEFAULT 0
            )
            """
        )
        # =================================================
        # PLAYER PETS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS player_pets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pet_id INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # =================================================
        # MARKET
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                egg_id INTEGER NOT NULL,
                price INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                buyer_id INTEGER,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                sold_at TEXT
            )
            """
        )
        # =================================================
        # STEAL ATTEMPTS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS steal_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thief_id INTEGER NOT NULL,
                victim_id INTEGER NOT NULL,
                egg_id INTEGER NOT NULL,
                success INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # =================================================
        # EGG PROTECTION
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS egg_protection (
                user_id INTEGER PRIMARY KEY,
                protection_until INTEGER NOT NULL
            )
            """
        )
        # =================================================
        # BOSS EVENT
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS boss_event (
                id INTEGER PRIMARY KEY,
                boss_name TEXT NOT NULL,
                max_hp INTEGER NOT NULL,
                current_hp INTEGER NOT NULL,
                started_at INTEGER NOT NULL,
                ends_at INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                reward_claimed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # =================================================
        # BOSS PARTICIPANTS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS boss_participants (
                user_id INTEGER PRIMARY KEY,
                damage INTEGER NOT NULL DEFAULT 0,
                reward_claimed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # =================================================
        # EGG PASS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS egg_pass (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER NOT NULL DEFAULT 0,
                level INTEGER NOT NULL DEFAULT 0,
                premium INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # =================================================
        # EGG PASS CLAIMS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS egg_pass_claims (
                user_id INTEGER NOT NULL,
                level INTEGER NOT NULL,
                track TEXT NOT NULL,
                PRIMARY KEY (
                    user_id,
                    level,
                    track
                )
            )
            """
        )
        # =================================================
        # DAILY QUESTS
        # =================================================
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_date TEXT NOT NULL,
                quest_id TEXT NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                target INTEGER NOT NULL,
                reward_type TEXT NOT NULL,
                reward_amount INTEGER NOT NULL,
                claimed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # =================================================
        # INDEXES
        # =================================================
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_player_eggs_user
            ON player_eggs(user_id)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_player_items_user
            ON player_items(user_id)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_player_pets_user
            ON player_pets(user_id)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_market_status
            ON market_listings(status)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_steal_thief
            ON steal_attempts(thief_id)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_steal_victim
            ON steal_attempts(victim_id)
            """
        )
        # =================================================
        # DEFAULT EGG TYPES
        # =================================================
        egg_types = [
            (
                1,
                '🥚 Обычное яйцо',
                '⚪ Обычное',
                1,
                1
            ),
            (
                2,
                '🥈 Серебряное яйцо',
                '🟢 Необычное',
                2,
                1
            ),
            (
                3,
                '🥇 Золотое яйцо',
                '🔵 Редкое',
                3,
                1
            ),
            (
                4,
                '💎 Алмазное яйцо',
                '🟣 Эпическое',
                4,
                1
            ),
            (
                5,
                '🔥 Огненное яйцо',
                '🟣 Эпическое',
                4,
                1
            ),
            (
                6,
                '❄️ Ледяное яйцо',
                '🟡 Легендарное',
                5,
                1
            ),
            (
                7,
                '🌌 Космическое яйцо',
                '🟡 Легендарное',
                5,
                1
            ),
            (
                8,
                '👑 Королевское яйцо',
                '🔴 Мифическое',
                6,
                1
            ),
            (
                9,
                '⚡ Молниевое яйцо',
                '🔴 Мифическое',
                6,
                1
            ),
            (
                10,
                '🌑 Тёмное яйцо',
                '🔴 Мифическое',
                6,
                1
            ),
            (
                11,
                '☀️ Солнечное яйцо',
                '💠 Божественное',
                7,
                1
            ),
            (
                12,
                '🪐 Галактическое яйцо',
                '💠 Божественное',
                7,
                1
            ),
            (
                13,
                '🧿 Проклятое яйцо',
                '🌈 Секретное',
                8,
                1
            ),
            (
                14,
                '🪽 Небесное яйцо',
                '🌈 Секретное',
                8,
                1
            ),
            (
                15,
                '👾 Глитч-яйцо',
                '🌈 Секретное',
                8,
                1
            ),
            (
                16,
                '🌋 Магмовое яйцо',
                '🟡 Легендарное',
                5,
                1
            ),
            (
                17,
                '🌊 Океанское яйцо',
                '🔴 Мифическое',
                6,
                1
            ),
            (
                18,
                '🌳 Древнее яйцо',
                '💠 Божественное',
                7,
                1
            ),
            (
                19,
                '👻 Призрачное яйцо',
                '🔴 Мифическое',
                6,
                1
            ),
            (
                20,
                '🩸 Тёмно-красное яйцо',
                '💠 Божественное',
                7,
                1
            )
        ]
        for egg in egg_types:
            conn.execute(
                """
                INSERT OR IGNORE INTO egg_types (
                    egg_id,
                    name,
                    rarity,
                    rarity_order,
                    marketable
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                egg
            )
        # =================================================
        # DEFAULT PETS
        # =================================================
        pets = [
            (
                1,
                '🐹 Яичный хомяк',
                '⚪ Обычное',
                'egg_coins',
                0.05
            ),
            (
                2,
                '🐱 Космо-кот',
                '🟢 Необычное',
                'egg_coins',
                0.08
            ),
            (
                3,
                '🦊 Огненный лис',
                '🔵 Редкое',
                'egg_coins',
                0.10
            ),
            (
                4,
                '🐉 Маленький дракон',
                '🟣 Эпическое',
                'egg_coins',
                0.15
            ),
            (
                5,
                '🦄 Неоновый единорог',
                '🟡 Легендарное',
                'egg_coins',
                0.20
            ),
            (
                6,
                '👑 Королевский дракон',
                '🔴 Мифическое',
                'egg_coins',
                0.30
            ),
            (
                7,
                '👾 Глитч-питомец',
                '💠 Божественное',
                'egg_coins',
                0.40
            )
        ]
        for pet in pets:
            conn.execute(
                """
                INSERT OR IGNORE INTO pets (
                    pet_id,
                    name,
                    rarity,
                    bonus_type,
                    bonus_value
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                pet
            )
        # =================================================
        # DEFAULT BOSS
        # =================================================
        boss = conn.execute(
            """
            SELECT id
            FROM boss_event
            WHERE id = 1
            """
        ).fetchone()
        if not boss:
            now = int(
                datetime.now().timestamp()
            )
            conn.execute(
                """
                INSERT INTO boss_event (
                    id,
                    boss_name,
                    max_hp,
                    current_hp,
                    started_at,
                    ends_at,
                    active,
                    reward_claimed
                )
                VALUES (
                    1,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    1,
                    0
                )
                """,
                (
                    'Король Яиц',
                    100000,
                    100000,
                    now,
                    now + 86400
                )
            )
        conn.commit()
    finally:
        conn.close()
# =========================================================
# PLAYER
# =========================================================
def create_player(
    user_id,
    username=None,
    avatar='🥚'
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO players (
                user_id,
                username,
                avatar
            )
            VALUES (?, ?, ?)
            """,
            (
                int(user_id),
                username or '',
                avatar or '🥚'
            )
        )
        conn.commit()
    finally:
        conn.close()
def ensure_player(
    user_id,
    username=None,
    first_name=None
):
    user_id = int(
        user_id
    )
    conn = get_connection()
    try:
        player = conn.execute(
            """
            SELECT *
            FROM players
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()
        display_name = (
            username
            or first_name
            or ''
        )
        if not player:
            conn.execute(
                """
                INSERT INTO players (
                    user_id,
                    username,
                    avatar
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    display_name,
                    '🥚'
                )
            )
        elif display_name:
            conn.execute(
                """
                UPDATE players
                SET username = ?
                WHERE user_id = ?
                """,
                (
                    display_name,
                    user_id
                )
            )
        conn.commit()
    finally:
        conn.close()
    return get_player(
        user_id
    )
def get_player(user_id):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM players
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
    finally:
        conn.close()
def update_username(
    user_id,
    username
):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE players
            SET username = ?
            WHERE user_id = ?
            """,
            (
                username or '',
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
# =========================================================
# BALANCE
# =========================================================
def get_tap_coins(user_id):
    player = get_player(
        user_id
    )
    if not player:
        return 0
    return int(
        player['tap_coins']
    )
def add_tap_coins(
    user_id,
    amount
):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE players
            SET tap_coins =
                MAX(
                    0,
                    tap_coins + ?
                )
            WHERE user_id = ?
            """,
            (
                int(amount),
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def remove_tap_coins(
    user_id,
    amount
):
    amount = int(
        amount
    )
    if amount <= 0:
        return False
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE players
            SET tap_coins =
                tap_coins - ?
            WHERE user_id = ?
              AND tap_coins >= ?
            """,
            (
                amount,
                int(user_id),
                amount
            )
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
def get_egg_coins(user_id):
    player = get_player(
        user_id
    )
    if not player:
        return 0
    return int(
        player['egg_coins']
    )
def add_egg_coins(
    user_id,
    amount
):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE players
            SET egg_coins =
                MAX(
                    0,
                    egg_coins + ?
                )
            WHERE user_id = ?
            """,
            (
                int(amount),
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def remove_egg_coins(
    user_id,
    amount
):
    amount = int(
        amount
    )
    if amount <= 0:
        return False
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE players
            SET egg_coins =
                egg_coins - ?
            WHERE user_id = ?
              AND egg_coins >= ?
            """,
            (
                amount,
                int(user_id),
                amount
            )
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
def get_balance(user_id):
    return (
        get_tap_coins(user_id),
        get_egg_coins(user_id)
    )
# =========================================================
# EGGS
# =========================================================
def add_egg(
    user_id,
    egg_id
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO player_eggs (
                user_id,
                egg_id
            )
            VALUES (?, ?)
            """,
            (
                int(user_id),
                int(egg_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def get_player_eggs(
    user_id
):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT egg_id
            FROM player_eggs
            WHERE user_id = ?
            ORDER BY id
            """,
            (int(user_id),)
        ).fetchall()
        return [
            int(row['egg_id'])
            for row in rows
        ]
    finally:
        conn.close()
def get_egg_count(
    user_id,
    egg_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM player_eggs
            WHERE user_id = ?
              AND egg_id = ?
            """,
            (
                int(user_id),
                int(egg_id)
            )
        ).fetchone()
        return int(
            row['count']
        )
    finally:
        conn.close()
def remove_one_egg(
    user_id,
    egg_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id
            FROM player_eggs
            WHERE user_id = ?
              AND egg_id = ?
            ORDER BY id
            LIMIT 1
            """,
            (
                int(user_id),
                int(egg_id)
            )
        ).fetchone()
        if not row:
            return False
        conn.execute(
            """
            DELETE FROM player_eggs
            WHERE id = ?
            """,
            (
                int(row['id']),
            )
        )
        conn.commit()
        return True
    finally:
        conn.close()
def get_steal_candidates(
    exclude_id,
    limit=30
):
    """Игроки, у которых есть яйца (кроме самого вора)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                p.user_id AS user_id,
                p.username AS username,
                p.avatar AS avatar,
                COUNT(e.id) AS eggs
            FROM players p
            JOIN player_eggs e
                ON e.user_id = p.user_id
            WHERE p.user_id != ?
              AND p.blocked = 0
            GROUP BY p.user_id
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (
                int(exclude_id),
                int(limit)
            )
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
def get_total_eggs(
    user_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM player_eggs
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
        return int(
            row['count']
        )
    finally:
        conn.close()
# =========================================================
# EGG TYPES
# =========================================================
def add_egg_type(
    egg_id,
    name,
    rarity,
    rarity_order=0,
    marketable=1
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO egg_types (
                egg_id,
                name,
                rarity,
                rarity_order,
                marketable
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(egg_id),
                name,
                rarity,
                int(rarity_order),
                int(marketable)
            )
        )
        conn.commit()
    finally:
        conn.close()
def get_egg_type(
    egg_id
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM egg_types
            WHERE egg_id = ?
            """,
            (int(egg_id),)
        ).fetchone()
    finally:
        conn.close()
def get_all_egg_types():
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM egg_types
            ORDER BY rarity_order, egg_id
            """
        ).fetchall()
    finally:
        conn.close()
# =========================================================
# XP / LEVEL
# =========================================================
def get_progress(
    user_id
):
    player = get_player(
        user_id
    )
    if not player:
        return (
            0,
            1
        )
    return (
        int(
            player['xp']
        ),
        int(
            player['level']
        )
    )
def add_xp(
    user_id,
    amount
):
    amount = max(
        0,
        int(amount)
    )
    conn = get_connection()
    try:
        player = conn.execute(
            """
            SELECT xp
            FROM players
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
        if not player:
            return
        new_xp = (
            int(player['xp'])
            + amount
        )
        new_level = max(
            1,
            min(
                1000,
                new_xp // 100 + 1
            )
        )
        conn.execute(
            """
            UPDATE players
            SET xp = ?,
                level = ?
            WHERE user_id = ?
            """,
            (
                new_xp,
                new_level,
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
# =========================================================
# LOGIN
# =========================================================
def get_login_streak(
    user_id
):
    player = get_player(
        user_id
    )
    if not player:
        return 0
    return int(
        player['login_streak']
    )
def get_login_status(
    user_id
):
    player = get_player(
        user_id
    )
    if not player:
        return {
            'last_login':
                None,
            'streak':
                0
        }
    return {
        'last_login':
            player['last_login'],
        'streak':
            int(
                player['login_streak']
            )
    }
def get_login_info(
    user_id
):
    player = get_player(
        user_id
    )
    if not player:
        return (
            0,
            None
        )
    return (
        int(
            player['login_streak']
        ),
        player['last_login']
    )
def update_login(
    user_id
):
    user_id = int(
        user_id
    )
    today = date.today()
    conn = get_connection()
    try:
        player = conn.execute(
            """
            SELECT
                login_streak,
                last_login
            FROM players
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()
        if not player:
            return 1
        last_login = player[
            'last_login'
        ]
        streak = int(
            player['login_streak']
        )
        if last_login == today.isoformat():
            return streak
        if last_login:
            try:
                previous = date.fromisoformat(
                    last_login
                )
                if (
                    today - previous
                ).days == 1:
                    streak += 1
                else:
                    streak = 1
            except ValueError:
                streak = 1
        else:
            streak = 1
        conn.execute(
            """
            UPDATE players
            SET login_streak = ?,
                last_login = ?
            WHERE user_id = ?
            """,
            (
                streak,
                today.isoformat(),
                user_id
            )
        )
        conn.commit()
        return streak
    finally:
        conn.close()
def set_daily_login(
    user_id
):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE players
            SET last_login = ?
            WHERE user_id = ?
            """,
            (
                date.today().isoformat(),
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
# =========================================================
# DAILY BONUS
# =========================================================
def get_daily_bonus_date(
    user_id
):
    player = get_player(
        user_id
    )
    if not player:
        return None
    return player[
        'daily_bonus_date'
    ]
def set_daily_bonus_date(
    user_id
):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE players
            SET daily_bonus_date = ?
            WHERE user_id = ?
            """,
            (
                date.today().isoformat(),
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
# =========================================================
# DAILY TASKS
# =========================================================
def _reset_tasks_if_needed(
    conn,
    user_id
):
    today = date.today().isoformat()
    player = conn.execute(
        """
        SELECT task_date
        FROM players
        WHERE user_id = ?
        """,
        (int(user_id),)
    ).fetchone()
    if not player:
        return
    if player['task_date'] != today:
        conn.execute(
            """
            UPDATE players
            SET task_date = ?,
                task_taps = 0,
                task_games = 0,
                task_eggs = 0
            WHERE user_id = ?
            """,
            (
                today,
                int(user_id)
            )
        )
def get_daily_tasks(
    user_id
):
    conn = get_connection()
    try:
        _reset_tasks_if_needed(
            conn,
            user_id
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT
                task_taps,
                task_games,
                task_eggs
            FROM players
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
        if not row:
            return (
                0,
                0,
                0
            )
        return (
            int(
                row['task_taps']
            ),
            int(
                row['task_games']
            ),
            int(
                row['task_eggs']
            )
        )
    finally:
        conn.close()
def add_task_tap(
    user_id,
    amount=1
):
    conn = get_connection()
    try:
        _reset_tasks_if_needed(
            conn,
            user_id
        )
        conn.execute(
            """
            UPDATE players
            SET task_taps =
                task_taps + ?
            WHERE user_id = ?
            """,
            (
                int(amount),
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def add_task_game(
    user_id,
    amount=1
):
    conn = get_connection()
    try:
        _reset_tasks_if_needed(
            conn,
            user_id
        )
        conn.execute(
            """
            UPDATE players
            SET task_games =
                task_games + ?
            WHERE user_id = ?
            """,
            (
                int(amount),
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def add_task_egg(
    user_id,
    amount=1
):
    conn = get_connection()
    try:
        _reset_tasks_if_needed(
            conn,
            user_id
        )
        conn.execute(
            """
            UPDATE players
            SET task_eggs =
                task_eggs + ?
            WHERE user_id = ?
            """,
            (
                int(amount),
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def has_daily_task_claim(
    user_id,
    task_id
):
    today = date.today().isoformat()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT 1
            FROM daily_task_claims
            WHERE user_id = ?
              AND task_date = ?
              AND task_id = ?
            """,
            (
                int(user_id),
                today,
                str(task_id)
            )
        ).fetchone()
        return row is not None
    finally:
        conn.close()
def add_daily_task_claim(
    user_id,
    task_id
):
    today = date.today().isoformat()
    conn = get_connection()
    try:
        try:
            conn.execute(
                """
                INSERT INTO daily_task_claims (
                    user_id,
                    task_date,
                    task_id
                )
                VALUES (?, ?, ?)
                """,
                (
                    int(user_id),
                    today,
                    str(task_id)
                )
            )
        except sqlite3.IntegrityError:
            conn.rollback()
            return False
        conn.commit()
        return True
    finally:
        conn.close()
# =========================================================
# ADVANCED DAILY QUESTS
# =========================================================
def clear_old_daily_quests(
    user_id
):
    today = date.today().isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """
            DELETE FROM daily_quests
            WHERE user_id = ?
              AND task_date != ?
            """,
            (
                int(user_id),
                today
            )
        )
        conn.commit()
    finally:
        conn.close()
def get_daily_quests(
    user_id
):
    clear_old_daily_quests(
        user_id
    )
    today = date.today().isoformat()
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM daily_quests
            WHERE user_id = ?
              AND task_date = ?
            ORDER BY id
            """,
            (
                int(user_id),
                today
            )
        ).fetchall()
    finally:
        conn.close()
def create_daily_quest(
    user_id,
    quest_id,
    target,
    reward_type,
    reward_amount
):
    today = date.today().isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO daily_quests (
                user_id,
                task_date,
                quest_id,
                target,
                reward_type,
                reward_amount
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                today,
                str(quest_id),
                int(target),
                str(reward_type),
                int(reward_amount)
            )
        )
        conn.commit()
    finally:
        conn.close()
def update_daily_quest(
    user_id,
    quest_id,
    amount=1
):
    today = date.today().isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE daily_quests
            SET progress =
                MIN(
                    target,
                    progress + ?
                )
            WHERE user_id = ?
              AND task_date = ?
              AND quest_id = ?
              AND claimed = 0
            """,
            (
                int(amount),
                int(user_id),
                today,
                str(quest_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def claim_daily_quest(
    user_id,
    quest_id
):
    today = date.today().isoformat()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM daily_quests
            WHERE user_id = ?
              AND task_date = ?
              AND quest_id = ?
              AND claimed = 0
            """,
            (
                int(user_id),
                today,
                str(quest_id)
            )
        ).fetchone()
        if not row:
            return None
        if int(
            row['progress']
        ) < int(
            row['target']
        ):
            return None
        conn.execute(
            """
            UPDATE daily_quests
            SET claimed = 1
            WHERE id = ?
            """,
            (
                int(row['id']),
            )
        )
        conn.commit()
        return dict(
            row
        )
    finally:
        conn.close()
# =========================================================
# ACHIEVEMENTS
# =========================================================
def has_achievement(
    user_id,
    achievement_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT 1
            FROM achievements
            WHERE user_id = ?
              AND achievement_id = ?
            LIMIT 1
            """,
            (
                int(user_id),
                int(achievement_id)
            )
        ).fetchone()
        return row is not None
    finally:
        conn.close()
def add_achievement(
    user_id,
    achievement_id
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO achievements (
                user_id,
                achievement_id
            )
            VALUES (?, ?)
            """,
            (
                int(user_id),
                int(achievement_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def get_achievements(
    user_id
):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT achievement_id
            FROM achievements
            WHERE user_id = ?
            ORDER BY achievement_id
            """,
            (int(user_id),)
        ).fetchall()
        return [
            int(
                row['achievement_id']
            )
            for row in rows
        ]
    finally:
        conn.close()
# =========================================================
# ITEMS
# =========================================================
def add_item(
    user_id,
    item_id
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO player_items (
                user_id,
                item_id
            )
            VALUES (?, ?)
            """,
            (
                int(user_id),
                int(item_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def get_item_count(
    user_id,
    item_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM player_items
            WHERE user_id = ?
              AND item_id = ?
            """,
            (
                int(user_id),
                int(item_id)
            )
        ).fetchone()
        return int(
            row['count']
        )
    finally:
        conn.close()
def remove_item(
    user_id,
    item_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id
            FROM player_items
            WHERE user_id = ?
              AND item_id = ?
            ORDER BY id
            LIMIT 1
            """,
            (
                int(user_id),
                int(item_id)
            )
        ).fetchone()
        if not row:
            return False
        conn.execute(
            """
            DELETE FROM player_items
            WHERE id = ?
            """,
            (
                int(row['id']),
            )
        )
        conn.commit()
        return True
    finally:
        conn.close()
def get_player_items(
    user_id
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM player_items
            WHERE user_id = ?
            ORDER BY id
            """,
            (int(user_id),)
        ).fetchall()
    finally:
        conn.close()
# =========================================================
# CHESTS
# =========================================================
def add_chest(
    user_id,
    chest_id
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO player_chests (
                user_id,
                chest_id
            )
            VALUES (?, ?)
            """,
            (
                int(user_id),
                int(chest_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def get_chest_count(
    user_id,
    chest_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM player_chests
            WHERE user_id = ?
              AND chest_id = ?
            """,
            (
                int(user_id),
                int(chest_id)
            )
        ).fetchone()
        return int(
            row['count']
        )
    finally:
        conn.close()
def get_player_chests(
    user_id
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM player_chests
            WHERE user_id = ?
            ORDER BY id
            """,
            (int(user_id),)
        ).fetchall()
    finally:
        conn.close()
def remove_chest(
    user_id,
    chest_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id
            FROM player_chests
            WHERE user_id = ?
              AND chest_id = ?
            ORDER BY id
            LIMIT 1
            """,
            (
                int(user_id),
                int(chest_id)
            )
        ).fetchone()
        if not row:
            return False
        conn.execute(
            """
            DELETE FROM player_chests
            WHERE id = ?
            """,
            (
                int(row['id']),
            )
        )
        conn.commit()
        return True
    finally:
        conn.close()
# =========================================================
# PETS
# =========================================================
def add_pet_type(
    pet_id,
    name,
    rarity,
    bonus_type,
    bonus_value
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO pets (
                pet_id,
                name,
                rarity,
                bonus_type,
                bonus_value
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(pet_id),
                name,
                rarity,
                bonus_type,
                float(bonus_value)
            )
        )
        conn.commit()
    finally:
        conn.close()
def get_pet_type(
    pet_id
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM pets
            WHERE pet_id = ?
            """,
            (int(pet_id),)
        ).fetchone()
    finally:
        conn.close()
def get_all_pets():
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM pets
            ORDER BY pet_id
            """
        ).fetchall()
    finally:
        conn.close()
def add_pet(
    user_id,
    pet_id
):
    conn = get_connection()
    try:
        existing = conn.execute(
            """
            SELECT id
            FROM player_pets
            WHERE user_id = ?
              AND pet_id = ?
            LIMIT 1
            """,
            (
                int(user_id),
                int(pet_id)
            )
        ).fetchone()
        if existing:
            return False
        conn.execute(
            """
            INSERT INTO player_pets (
                user_id,
                pet_id,
                active
            )
            VALUES (?, ?, 0)
            """,
            (
                int(user_id),
                int(pet_id)
            )
        )
        conn.commit()
        return True
    finally:
        conn.close()
def get_player_pets(
    user_id
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT
                pp.*,
                p.name,
                p.rarity,
                p.bonus_type,
                p.bonus_value
            FROM player_pets pp
            LEFT JOIN pets p
                ON p.pet_id = pp.pet_id
            WHERE pp.user_id = ?
            ORDER BY pp.id
            """,
            (int(user_id),)
        ).fetchall()
    finally:
        conn.close()
def get_active_pet(
    user_id
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT
                pp.*,
                p.name,
                p.rarity,
                p.bonus_type,
                p.bonus_value
            FROM player_pets pp
            LEFT JOIN pets p
                ON p.pet_id = pp.pet_id
            WHERE pp.user_id = ?
              AND pp.active = 1
            LIMIT 1
            """,
            (int(user_id),)
        ).fetchone()
    finally:
        conn.close()
def set_active_pet(
    user_id,
    player_pet_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id
            FROM player_pets
            WHERE id = ?
              AND user_id = ?
            """,
            (
                int(player_pet_id),
                int(user_id)
            )
        ).fetchone()
        if not row:
            return False
        conn.execute(
            """
            UPDATE player_pets
            SET active = 0
            WHERE user_id = ?
            """,
            (
                int(user_id),
            )
        )
        conn.execute(
            """
            UPDATE player_pets
            SET active = 1
            WHERE id = ?
              AND user_id = ?
            """,
            (
                int(player_pet_id),
                int(user_id)
            )
        )
        conn.commit()
        return True
    finally:
        conn.close()
def remove_pet(
    user_id,
    player_pet_id
):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            DELETE FROM player_pets
            WHERE id = ?
              AND user_id = ?
            """,
            (
                int(player_pet_id),
                int(user_id)
            )
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
# =========================================================
# MARKET
# =========================================================
def create_market_listing(
    seller_id,
    egg_id,
    price
):
    seller_id = int(
        seller_id
    )
    egg_id = int(
        egg_id
    )
    price = int(
        price
    )
    if price <= 0:
        raise ValueError(
            'Цена должна быть больше 0.'
        )
    conn = get_connection()
    try:
        egg_type = conn.execute(
            """
            SELECT marketable
            FROM egg_types
            WHERE egg_id = ?
            """,
            (egg_id,)
        ).fetchone()
        if (
            egg_type
            and not int(
                egg_type['marketable']
            )
        ):
            raise ValueError(
                'Это яйцо нельзя продавать.'
            )
        egg = conn.execute(
            """
            SELECT id
            FROM player_eggs
            WHERE user_id = ?
              AND egg_id = ?
            ORDER BY id
            LIMIT 1
            """,
            (
                seller_id,
                egg_id
            )
        ).fetchone()
        if not egg:
            raise ValueError(
                'У тебя нет такого яйца.'
            )
        conn.execute(
            """
            DELETE FROM player_eggs
            WHERE id = ?
            """,
            (
                int(egg['id']),
            )
        )
        cursor = conn.execute(
            """
            INSERT INTO market_listings (
                seller_id,
                egg_id,
                price,
                status
            )
            VALUES (?, ?, ?, 'active')
            """,
            (
                seller_id,
                egg_id,
                price
            )
        )
        listing_id = cursor.lastrowid
        conn.commit()
        return listing_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
def get_market_listings(
    egg_id=None,
    limit=50
):
    conn = get_connection()
    try:
        if egg_id is None:
            return conn.execute(
                """
                SELECT *
                FROM market_listings
                WHERE status = 'active'
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    int(limit),
                )
            ).fetchall()
        return conn.execute(
            """
            SELECT *
            FROM market_listings
            WHERE status = 'active'
              AND egg_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                int(egg_id),
                int(limit)
            )
        ).fetchall()
    finally:
        conn.close()
def get_market_listing(
    listing_id
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM market_listings
            WHERE id = ?
            """,
            (int(listing_id),)
        ).fetchone()
    finally:
        conn.close()
def cancel_market_listing(
    seller_id,
    listing_id
):
    seller_id = int(
        seller_id
    )
    listing_id = int(
        listing_id
    )
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM market_listings
            WHERE id = ?
              AND seller_id = ?
              AND status = 'active'
            """,
            (
                listing_id,
                seller_id
            )
        ).fetchone()
        if not row:
            return False
        conn.execute(
            """
            UPDATE market_listings
            SET status = 'cancelled'
            WHERE id = ?
              AND seller_id = ?
              AND status = 'active'
            """,
            (
                listing_id,
                seller_id
            )
        )
        conn.execute(
            """
            INSERT INTO player_eggs (
                user_id,
                egg_id
            )
            VALUES (?, ?)
            """,
            (
                seller_id,
                int(row['egg_id'])
            )
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
def buy_market_listing(
    buyer_id,
    listing_id
):
    buyer_id = int(
        buyer_id
    )
    listing_id = int(
        listing_id
    )
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM market_listings
            WHERE id = ?
              AND status = 'active'
            """,
            (listing_id,)
        ).fetchone()
        if not row:
            return None
        seller_id = int(
            row['seller_id']
        )
        if seller_id == buyer_id:
            return None
        price = int(
            row['price']
        )
        fee = max(
            1,
            int(
                price * 0.05
            )
        )
        total = (
            price + fee
        )
        # Сначала атомарно снимаем
        # деньги у покупателя.
        cursor = conn.execute(
            """
            UPDATE players
            SET egg_coins =
                egg_coins - ?
            WHERE user_id = ?
              AND egg_coins >= ?
            """,
            (
                total,
                buyer_id,
                total
            )
        )
        if cursor.rowcount <= 0:
            conn.rollback()
            return None
        # Проверяем, что лот всё ещё активен.
        cursor = conn.execute(
            """
            UPDATE market_listings
            SET status = 'sold',
                buyer_id = ?,
                sold_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND status = 'active'
            """,
            (
                buyer_id,
                listing_id
            )
        )
        if cursor.rowcount <= 0:
            conn.rollback()
            return None
        # Продавец получает полную цену.
        conn.execute(
            """
            UPDATE players
            SET egg_coins =
                egg_coins + ?
            WHERE user_id = ?
            """,
            (
                price,
                seller_id
            )
        )
        # Яйцо получает покупатель.
        conn.execute(
            """
            INSERT INTO player_eggs (
                user_id,
                egg_id
            )
            VALUES (?, ?)
            """,
            (
                buyer_id,
                int(row['egg_id'])
            )
        )
        conn.commit()
        return {
            'price':
                price,
            'fee':
                fee,
            'seller_reward':
                price,
            'egg_id':
                int(
                    row['egg_id']
                )
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
def get_player_market_listings(
    user_id
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM market_listings
            WHERE seller_id = ?
            ORDER BY id DESC
            """,
            (int(user_id),)
        ).fetchall()
    finally:
        conn.close()
# =========================================================
# EGG PROTECTION
# =========================================================
def set_egg_protection(
    user_id,
    seconds
):
    until = int(
        datetime.now().timestamp()
        + max(
            0,
            int(seconds)
        )
    )
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO egg_protection (
                user_id,
                protection_until
            )
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                protection_until =
                    excluded.protection_until
            """,
            (
                int(user_id),
                until
            )
        )
        conn.commit()
    finally:
        conn.close()
def is_egg_protected(
    user_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT protection_until
            FROM egg_protection
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
        if not row:
            return False
        until = int(
            row['protection_until']
        )
        now = int(
            datetime.now().timestamp()
        )
        if until <= now:
            conn.execute(
                """
                DELETE FROM egg_protection
                WHERE user_id = ?
                """,
                (int(user_id),)
            )
            conn.commit()
            return False
        return True
    finally:
        conn.close()
# =========================================================
# STEAL
# =========================================================
def add_steal_attempt(
    thief_id,
    victim_id,
    egg_id,
    success
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO steal_attempts (
                thief_id,
                victim_id,
                egg_id,
                success
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                int(thief_id),
                int(victim_id),
                int(egg_id),
                1 if success else 0
            )
        )
        conn.commit()
    finally:
        conn.close()
def get_last_steal_attempt(
    thief_id
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM steal_attempts
            WHERE thief_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (int(thief_id),)
        ).fetchone()
    finally:
        conn.close()
def get_steal_attempts_today(
    thief_id
):
    today = date.today().isoformat()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM steal_attempts
            WHERE thief_id = ?
              AND DATE(created_at) = ?
            """,
            (
                int(thief_id),
                today
            )
        ).fetchone()
        return int(
            row['count']
        )
    finally:
        conn.close()
def transfer_stolen_egg(
    thief_id,
    victim_id,
    egg_id
):
    thief_id = int(
        thief_id
    )
    victim_id = int(
        victim_id
    )
    egg_id = int(
        egg_id
    )
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT id
            FROM player_eggs
            WHERE user_id = ?
              AND egg_id = ?
            ORDER BY id
            LIMIT 1
            """,
            (
                victim_id,
                egg_id
            )
        ).fetchone()
        if not row:
            return False
        conn.execute(
            """
            DELETE FROM player_eggs
            WHERE id = ?
            """,
            (
                int(row['id']),
            )
        )
        conn.execute(
            """
            INSERT INTO player_eggs (
                user_id,
                egg_id
            )
            VALUES (?, ?)
            """,
            (
                thief_id,
                egg_id
            )
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
# =========================================================
# BOSS
# =========================================================
def start_boss_event(
    boss_name='Король Яиц',
    max_hp=100000,
    duration_seconds=86400
):
    now = int(
        datetime.now().timestamp()
    )
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO boss_event (
                id,
                boss_name,
                max_hp,
                current_hp,
                started_at,
                ends_at,
                active,
                reward_claimed
            )
            VALUES (
                1,
                ?,
                ?,
                ?,
                ?,
                ?,
                1,
                0
            )
            """,
            (
                boss_name,
                int(max_hp),
                int(max_hp),
                now,
                now + int(duration_seconds)
            )
        )
        conn.execute(
            """
            DELETE FROM boss_participants
            """
        )
        conn.execute(
            """
            UPDATE players
            SET boss_damage = 0
            """
        )
        conn.commit()
    finally:
        conn.close()
def get_boss_event():
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM boss_event
            WHERE id = 1
            """
        ).fetchone()
        if not row:
            return None
        now = int(
            datetime.now().timestamp()
        )
        current_hp = int(
            row['current_hp']
        )
        ends_at = int(
            row['ends_at']
        )
        active = int(
            row['active']
        )
        if (
            active == 1
            and ends_at <= now
        ):
            conn.execute(
                """
                UPDATE boss_event
                SET active = 0
                WHERE id = 1
                """
            )
            conn.commit()
            row = conn.execute(
                """
                SELECT *
                FROM boss_event
                WHERE id = 1
                """
            ).fetchone()
        return row
    finally:
        conn.close()
def damage_boss(
    user_id,
    amount
):
    amount = max(
        0,
        int(amount)
    )
    if amount <= 0:
        return 0
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT *
            FROM boss_event
            WHERE id = 1
            """
        ).fetchone()
        if not row:
            return 0
        now = int(
            datetime.now().timestamp()
        )
        if int(
            row['active']
        ) != 1:
            return 0
        if int(
            row['ends_at']
        ) <= now:
            conn.execute(
                """
                UPDATE boss_event
                SET active = 0
                WHERE id = 1
                """
            )
            conn.commit()
            return 0
        current_hp = int(
            row['current_hp']
        )
        if current_hp <= 0:
            return 0
        actual_damage = min(
            amount,
            current_hp
        )
        new_hp = (
            current_hp
            - actual_damage
        )
        conn.execute(
            """
            UPDATE boss_event
            SET current_hp = ?,
                active = ?
            WHERE id = 1
              AND current_hp = ?
              AND active = 1
            """,
            (
                new_hp,
                0 if new_hp <= 0 else 1,
                current_hp
            )
        )
        if conn.execute(
            "SELECT changes()"
        ).fetchone()[0] != 1:
            conn.rollback()
            return 0
        conn.execute(
            """
            INSERT INTO boss_participants (
                user_id,
                damage,
                reward_claimed
            )
            VALUES (?, ?, 0)
            ON CONFLICT(user_id)
            DO UPDATE SET
                damage =
                    boss_participants.damage
                    + excluded.damage
            """,
            (
                int(user_id),
                actual_damage
            )
        )
        conn.execute(
            """
            UPDATE players
            SET boss_damage =
                boss_damage + ?
            WHERE user_id = ?
            """,
            (
                actual_damage,
                int(user_id)
            )
        )
        conn.commit()
        return actual_damage
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
def get_boss_participants():
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT
                bp.user_id,
                bp.damage,
                bp.reward_claimed,
                p.username
            FROM boss_participants bp
            LEFT JOIN players p
                ON p.user_id = bp.user_id
            ORDER BY bp.damage DESC
            """
        ).fetchall()
    finally:
        conn.close()
def get_boss_damage(
    user_id
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT damage
            FROM boss_participants
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
        if row:
            return int(
                row['damage']
            )
        player = conn.execute(
            """
            SELECT boss_damage
            FROM players
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
        if not player:
            return 0
        return int(
            player['boss_damage']
        )
    finally:
        conn.close()
def add_boss_damage(
    user_id,
    amount
):
    amount = max(
        0,
        int(amount)
    )
    if amount <= 0:
        return
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO boss_participants (
                user_id,
                damage,
                reward_claimed
            )
            VALUES (?, ?, 0)
            ON CONFLICT(user_id)
            DO UPDATE SET
                damage =
                    boss_participants.damage
                    + excluded.damage
            """,
            (
                int(user_id),
                amount
            )
        )
        conn.execute(
            """
            UPDATE players
            SET boss_damage =
                boss_damage + ?
            WHERE user_id = ?
            """,
            (
                amount,
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def claim_boss_reward(
    user_id
):
    conn = get_connection()
    try:
        boss = conn.execute(
            """
            SELECT *
            FROM boss_event
            WHERE id = 1
            """
        ).fetchone()
        if not boss:
            return None
        now = int(
            datetime.now().timestamp()
        )
        # Награда доступна после победы
        # или после завершения события.
        finished = (
            int(
                boss['current_hp']
            ) <= 0
            or int(
                boss['ends_at']
            ) <= now
            or int(
                boss['active']
            ) == 0
        )
        if not finished:
            return None
        participant = conn.execute(
            """
            SELECT *
            FROM boss_participants
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
        if not participant:
            return None
        if int(
            participant['reward_claimed']
        ) == 1:
            return None
        conn.execute(
            """
            UPDATE boss_participants
            SET reward_claimed = 1
            WHERE user_id = ?
            """,
            (
                int(user_id),
            )
        )
        conn.commit()
        return {
            'damage':
                int(
                    participant['damage']
                )
        }
    finally:
        conn.close()
# =========================================================
# EGG PASS
# =========================================================
def ensure_egg_pass(
    user_id
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO egg_pass (
                user_id,
                xp,
                level,
                premium
            )
            VALUES (?, 0, 0, 0)
            """,
            (
                int(user_id),
            )
        )
        conn.commit()
    finally:
        conn.close()
def get_egg_pass(
    user_id
):
    ensure_egg_pass(
        user_id
    )
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM egg_pass
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
    finally:
        conn.close()
def add_egg_pass_xp(
    user_id,
    amount
):
    amount = max(
        0,
        int(amount)
    )
    ensure_egg_pass(
        user_id
    )
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT xp
            FROM egg_pass
            WHERE user_id = ?
            """,
            (int(user_id),)
        ).fetchone()
        if not row:
            return
        new_xp = (
            int(row['xp'])
            + amount
        )
        new_level = min(
            30,
            new_xp // 100
        )
        conn.execute(
            """
            UPDATE egg_pass
            SET xp = ?,
                level = ?
            WHERE user_id = ?
            """,
            (
                new_xp,
                new_level,
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def set_egg_pass_premium(
    user_id,
    premium=True
):
    ensure_egg_pass(
        user_id
    )
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE egg_pass
            SET premium = ?
            WHERE user_id = ?
            """,
            (
                1 if premium else 0,
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def has_egg_pass_reward(
    user_id,
    level,
    track
):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT 1
            FROM egg_pass_claims
            WHERE user_id = ?
              AND level = ?
              AND track = ?
            """,
            (
                int(user_id),
                int(level),
                str(track)
            )
        ).fetchone()
        return row is not None
    finally:
        conn.close()
def claim_egg_pass_reward(
    user_id,
    level,
    track
):
    level = int(
        level
    )
    track = str(
        track
    )
    if not 1 <= level <= 30:
        return False
    if track not in (
        'free',
        'premium'
    ):
        return False
    state = get_egg_pass(
        user_id
    )
    if not state:
        return False
    if int(
        state['level']
    ) < level:
        return False
    if (
        track == 'premium'
        and int(
            state['premium']
        ) != 1
    ):
        return False
    if has_egg_pass_reward(
        user_id,
        level,
        track
    ):
        return False
    conn = get_connection()
    try:
        try:
            conn.execute(
                """
                INSERT INTO egg_pass_claims (
                    user_id,
                    level,
                    track
                )
                VALUES (?, ?, ?)
                """,
                (
                    int(user_id),
                    level,
                    track
                )
            )
        except sqlite3.IntegrityError:
            conn.rollback()
            return False
        conn.commit()
        return True
    finally:
        conn.close()
# =========================================================
# AVATAR
# =========================================================
def get_avatar(
    user_id
):
    player = get_player(
        user_id
    )
    if not player:
        return '🥚'
    return (
        player['avatar']
        or '🥚'
    )
def set_avatar(
    user_id,
    avatar
):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE players
            SET avatar = ?
            WHERE user_id = ?
            """,
            (
                avatar,
                int(user_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
# =========================================================
# BLOCK
# =========================================================
def block_player(
    user_id
):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE players
            SET blocked = 1
            WHERE user_id = ?
            """,
            (
                int(user_id),
            )
        )
        conn.commit()
    finally:
        conn.close()
def unblock_player(
    user_id
):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE players
            SET blocked = 0
            WHERE user_id = ?
            """,
            (
                int(user_id),
            )
        )
        conn.commit()
    finally:
        conn.close()
def is_blocked(
    user_id
):
    player = get_player(
        user_id
    )
    if not player:
        return False
    return bool(
        player['blocked']
    )
# =========================================================
# PLAYERS / LEADERBOARD
# =========================================================
def get_all_players():
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM players
            ORDER BY egg_coins DESC,
                     tap_coins DESC
            """
        ).fetchall()
    finally:
        conn.close()
def get_top_players(
    limit=10
):
    conn = get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM players
            ORDER BY egg_coins DESC,
                     tap_coins DESC
            LIMIT ?
            """,
            (
                int(limit),
            )
        ).fetchall()
    finally:
        conn.close()
def get_player_rank(
    user_id
):
    players = get_all_players()
    for position, player in enumerate(
        players,
        start=1
    ):
        if int(
            player['user_id']
        ) == int(user_id):
            return position
    return None
# =========================================================
# NEW MINI-GAMES: TABLES
# =========================================================
def init_game_tables():
    conn = get_connection()
    try:
        # Дневные лимиты / счётчики игр (колесо, награды игр)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS game_daily (
                user_id INTEGER NOT NULL,
                game TEXT NOT NULL,
                day TEXT NOT NULL,
                plays INTEGER NOT NULL DEFAULT 0,
                coins INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, game, day)
            )
            """
        )
        # Незавершённые партии (переживают перезапуск сервера)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS game_sessions (
                user_id INTEGER NOT NULL,
                game TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                PRIMARY KEY (user_id, game)
            )
            """
        )
        # Дуэли между игроками
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS duels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                creator_move TEXT NOT NULL,
                opponent_id INTEGER,
                opponent_move TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                winner_id INTEGER NOT NULL DEFAULT 0,
                creator_reward INTEGER NOT NULL DEFAULT 0,
                opponent_reward INTEGER NOT NULL DEFAULT 0,
                creator_seen INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL,
                resolved_at INTEGER
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_duels_status
            ON duels(status, created_at)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_duels_creator
            ON duels(creator_id)
            """
        )
        conn.commit()
    finally:
        conn.close()
# =========================================================
# GAME SESSIONS
# =========================================================
def session_set(user_id, game, state):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO game_sessions (
                user_id, game, state, created_at
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, game)
            DO UPDATE SET
                state = excluded.state,
                created_at = excluded.created_at
            """,
            (
                int(user_id),
                str(game),
                json.dumps(state),
                int(datetime.now().timestamp())
            )
        )
        conn.commit()
    finally:
        conn.close()
def session_get(user_id, game):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT state
            FROM game_sessions
            WHERE user_id = ? AND game = ?
            """,
            (int(user_id), str(game))
        ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row['state'])
        except (TypeError, ValueError):
            return None
    finally:
        conn.close()
def session_pop(user_id, game):
    """Удаляет партию. True, если именно этот вызов её забрал."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            DELETE FROM game_sessions
            WHERE user_id = ? AND game = ?
            """,
            (int(user_id), str(game))
        )
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()
# =========================================================
# GAME DAILY COUNTERS
# =========================================================
def game_daily_get(user_id, game):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT plays, coins
            FROM game_daily
            WHERE user_id = ? AND game = ? AND day = ?
            """,
            (
                int(user_id),
                str(game),
                date.today().isoformat()
            )
        ).fetchone()
        if not row:
            return 0, 0
        return int(row['plays']), int(row['coins'])
    finally:
        conn.close()
def game_daily_add(user_id, game, plays=1, coins=0):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO game_daily (
                user_id, game, day, plays, coins
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, game, day)
            DO UPDATE SET
                plays = plays + excluded.plays,
                coins = coins + excluded.coins
            """,
            (
                int(user_id),
                str(game),
                date.today().isoformat(),
                int(plays),
                int(coins)
            )
        )
        conn.commit()
    finally:
        conn.close()
def game_daily_claim_once(user_id, game):
    """True, если сегодня это действие ещё не выполнялось.

    Атомарно: второй одновременный запрос получит False.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO game_daily (
                user_id, game, day, plays, coins
            )
            VALUES (?, ?, ?, 1, 0)
            """,
            (
                int(user_id),
                str(game),
                date.today().isoformat()
            )
        )
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()
# =========================================================
# DUELS
# =========================================================
DUEL_TTL = 86400
def _duel_now():
    return int(datetime.now().timestamp())
def duel_create(creator_id, move, max_open=3):
    now = _duel_now()
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE duels
            SET status = 'expired'
            WHERE status = 'open' AND created_at < ?
            """,
            (now - DUEL_TTL,)
        )
        row = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM duels
            WHERE creator_id = ? AND status = 'open'
            """,
            (int(creator_id),)
        ).fetchone()
        if int(row['c']) >= max_open:
            conn.commit()
            return None
        cursor = conn.execute(
            """
            INSERT INTO duels (
                creator_id, creator_move, created_at
            )
            VALUES (?, ?, ?)
            """,
            (int(creator_id), str(move), now)
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()
def duel_open_list(exclude_id, limit=20):
    now = _duel_now()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT d.id AS id,
                   d.creator_id AS creator_id,
                   d.created_at AS created_at,
                   p.username AS username,
                   p.avatar AS avatar
            FROM duels d
            JOIN players p ON p.user_id = d.creator_id
            WHERE d.status = 'open'
              AND d.creator_id != ?
              AND d.created_at >= ?
              AND p.blocked = 0
            ORDER BY d.id DESC
            LIMIT ?
            """,
            (
                int(exclude_id),
                now - DUEL_TTL,
                int(limit)
            )
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
def duel_get(duel_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM duels WHERE id = ?",
            (int(duel_id),)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()
def duel_finish(
    duel_id,
    opponent_id,
    opponent_move,
    winner_id,
    creator_reward,
    opponent_reward
):
    """Атомарно закрывает открытую дуэль. False, если её уже забрали."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE duels
            SET status = 'done',
                opponent_id = ?,
                opponent_move = ?,
                winner_id = ?,
                creator_reward = ?,
                opponent_reward = ?,
                resolved_at = ?
            WHERE id = ?
              AND status = 'open'
              AND creator_id != ?
              AND created_at >= ?
            """,
            (
                int(opponent_id),
                str(opponent_move),
                int(winner_id),
                int(creator_reward),
                int(opponent_reward),
                _duel_now(),
                int(duel_id),
                int(opponent_id),
                _duel_now() - DUEL_TTL
            )
        )
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()
def duel_set_rewards(duel_id, creator_reward, opponent_reward):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE duels
            SET creator_reward = ?,
                opponent_reward = ?
            WHERE id = ?
            """,
            (
                int(creator_reward),
                int(opponent_reward),
                int(duel_id)
            )
        )
        conn.commit()
    finally:
        conn.close()
def duel_cancel(duel_id, creator_id):
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE duels
            SET status = 'cancelled'
            WHERE id = ?
              AND creator_id = ?
              AND status = 'open'
            """,
            (int(duel_id), int(creator_id))
        )
        conn.commit()
        return cursor.rowcount == 1
    finally:
        conn.close()
def duel_mine(user_id, limit=10):
    """Свои открытые вызовы и недавние результаты (я создатель)."""
    now = _duel_now()
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT d.*,
                   p.username AS opponent_name,
                   p.avatar AS opponent_avatar
            FROM duels d
            LEFT JOIN players p ON p.user_id = d.opponent_id
            WHERE d.creator_id = ?
              AND (
                    (d.status = 'open' AND d.created_at >= ?)
                    OR d.status = 'done'
                  )
            ORDER BY d.id DESC
            LIMIT ?
            """,
            (int(user_id), now - DUEL_TTL, int(limit))
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
def duel_mark_seen(user_id):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE duels
            SET creator_seen = 1
            WHERE creator_id = ? AND status = 'done'
            """,
            (int(user_id),)
        )
        conn.commit()
    finally:
        conn.close()
# =========================================================
# START DATABASE
# =========================================================
init_database()
init_game_tables()
