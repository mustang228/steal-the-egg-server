import sqlite3
from pathlib import Path
from datetime import date, datetime


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "players.db"


# =========================================================
# CONNECTION
# =========================================================

def get_connection():

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# INIT DATABASE
# =========================================================

def init_database():

    conn = get_connection()
    cur = conn.cursor()

    # =====================================================
    # PLAYERS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (

            user_id INTEGER PRIMARY KEY,

            tap_coins INTEGER NOT NULL DEFAULT 0,

            egg_coins INTEGER NOT NULL DEFAULT 0,

            username TEXT,

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

            avatar TEXT NOT NULL DEFAULT '🥚'
        )
    """)

    # =====================================================
    # PLAYER EGGS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_eggs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            egg_id INTEGER NOT NULL
        )
    """)

    # =====================================================
    # PLAYER ITEMS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_items (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            item_id INTEGER NOT NULL
        )
    """)

    # =====================================================
    # ACHIEVEMENTS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            achievement_id INTEGER NOT NULL
        )
    """)

    # =====================================================
    # DAILY TASK CLAIMS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_task_claims (

            user_id INTEGER NOT NULL,

            task_date TEXT NOT NULL,

            task_id INTEGER NOT NULL,

            PRIMARY KEY (
                user_id,
                task_date,
                task_id
            )
        )
    """)

    # =====================================================
    # EGG METADATA
    #
    # Здесь хранится информация о яйцах.
    # Сами яйца игроков находятся в player_eggs.
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS egg_types (

            egg_id INTEGER PRIMARY KEY,

            name TEXT NOT NULL,

            rarity TEXT NOT NULL,

            rarity_order INTEGER NOT NULL DEFAULT 1,

            marketable INTEGER NOT NULL DEFAULT 1
        )
    """)

    # =====================================================
    # CHESTS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_chests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            chest_id INTEGER NOT NULL,

            created_at TEXT NOT NULL
        )
    """)

    # =====================================================
    # PETS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets (

            pet_id INTEGER PRIMARY KEY,

            name TEXT NOT NULL,

            rarity TEXT NOT NULL,

            bonus_type TEXT NOT NULL,

            bonus_value REAL NOT NULL DEFAULT 0
        )
    """)

    # =====================================================
    # PLAYER PETS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_pets (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            pet_id INTEGER NOT NULL,

            active INTEGER NOT NULL DEFAULT 0,

            created_at TEXT NOT NULL
        )
    """)

    # =====================================================
    # MARKET LISTINGS
    #
    # Яйцо удаляется у продавца при создании объявления.
    # При покупке оно переходит покупателю.
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_listings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            seller_id INTEGER NOT NULL,

            egg_id INTEGER NOT NULL,

            price INTEGER NOT NULL,

            status TEXT NOT NULL DEFAULT 'active',

            buyer_id INTEGER,

            created_at TEXT NOT NULL,

            sold_at TEXT
        )
    """)

    # =====================================================
    # THEFT / STEAL SYSTEM
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS steal_attempts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            thief_id INTEGER NOT NULL,

            victim_id INTEGER NOT NULL,

            egg_id INTEGER NOT NULL,

            success INTEGER NOT NULL DEFAULT 0,

            created_at TEXT NOT NULL
        )
    """)

    # =====================================================
    # EGG PROTECTION
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS egg_protection (

            user_id INTEGER PRIMARY KEY,

            protection_until TEXT
        )
    """)

    # =====================================================
    # BOSS EVENT
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS boss_event (

            id INTEGER PRIMARY KEY CHECK (id = 1),

            boss_name TEXT NOT NULL DEFAULT 'Король Яиц',

            max_hp INTEGER NOT NULL DEFAULT 100000,

            current_hp INTEGER NOT NULL DEFAULT 100000,

            started_at TEXT,

            ends_at TEXT,

            active INTEGER NOT NULL DEFAULT 0,

            reward_claimed INTEGER NOT NULL DEFAULT 0
        )
    """)

    # =====================================================
    # BOSS PARTICIPATION
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS boss_participants (

            user_id INTEGER PRIMARY KEY,

            damage INTEGER NOT NULL DEFAULT 0,

            reward_claimed INTEGER NOT NULL DEFAULT 0
        )
    """)

    # =====================================================
    # EGG PASS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS egg_pass (

            user_id INTEGER PRIMARY KEY,

            xp INTEGER NOT NULL DEFAULT 0,

            level INTEGER NOT NULL DEFAULT 1,

            premium INTEGER NOT NULL DEFAULT 0
        )
    """)

    # =====================================================
    # EGG PASS CLAIMS
    # =====================================================

    cur.execute("""
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
    """)

    # =====================================================
    # DAILY QUESTS
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_quests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            task_date TEXT NOT NULL,

            quest_id INTEGER NOT NULL,

            progress INTEGER NOT NULL DEFAULT 0,

            target INTEGER NOT NULL DEFAULT 1,

            reward_type TEXT NOT NULL,

            reward_amount INTEGER NOT NULL DEFAULT 0,

            claimed INTEGER NOT NULL DEFAULT 0
        )
    """)

    # =====================================================
    # TABLE STRUCTURE MIGRATION
    # =====================================================

    def has_column(table_name, column_name):

        rows = cur.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        return any(
            row["name"] == column_name
            for row in rows
        )

    # -----------------------------------------------------
    # PLAYER EGGS
    # -----------------------------------------------------

    if not has_column("player_eggs", "id"):

        print("Миграция player_eggs: добавляем id")

        cur.execute("""
            ALTER TABLE player_eggs
            RENAME TO player_eggs_old
        """)

        cur.execute("""
            CREATE TABLE player_eggs (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                egg_id INTEGER NOT NULL
            )
        """)

        cur.execute("""
            INSERT INTO player_eggs (
                user_id,
                egg_id
            )
            SELECT
                user_id,
                egg_id
            FROM player_eggs_old
        """)

        cur.execute("""
            DROP TABLE player_eggs_old
        """)

    # -----------------------------------------------------
    # PLAYER ITEMS
    # -----------------------------------------------------

    if not has_column("player_items", "id"):

        print("Миграция player_items: добавляем id")

        cur.execute("""
            ALTER TABLE player_items
            RENAME TO player_items_old
        """)

        cur.execute("""
            CREATE TABLE player_items (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                item_id INTEGER NOT NULL
            )
        """)

        cur.execute("""
            INSERT INTO player_items (
                user_id,
                item_id
            )
            SELECT
                user_id,
                item_id
            FROM player_items_old
        """)

        cur.execute("""
            DROP TABLE player_items_old
        """)

    # -----------------------------------------------------
    # ACHIEVEMENTS
    # -----------------------------------------------------

    if not has_column("achievements", "id"):

        print("Миграция achievements: добавляем id")

        cur.execute("""
            ALTER TABLE achievements
            RENAME TO achievements_old
        """)

        cur.execute("""
            CREATE TABLE achievements (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                achievement_id INTEGER NOT NULL
            )
        """)

        cur.execute("""
            INSERT INTO achievements (
                user_id,
                achievement_id
            )
            SELECT
                user_id,
                achievement_id
            FROM achievements_old
        """)

        cur.execute("""
            DROP TABLE achievements_old
        """)

    # =====================================================
    # PLAYERS MIGRATION
    # =====================================================

    cur.execute("""
        PRAGMA table_info(players)
    """)

    columns = {
        row["name"]
        for row in cur.fetchall()
    }

    migrations = {

        "tap_coins":
            "ALTER TABLE players ADD COLUMN tap_coins INTEGER NOT NULL DEFAULT 0",

        "egg_coins":
            "ALTER TABLE players ADD COLUMN egg_coins INTEGER NOT NULL DEFAULT 0",

        "username":
            "ALTER TABLE players ADD COLUMN username TEXT",

        "blocked":
            "ALTER TABLE players ADD COLUMN blocked INTEGER NOT NULL DEFAULT 0",

        "xp":
            "ALTER TABLE players ADD COLUMN xp INTEGER NOT NULL DEFAULT 0",

        "level":
            "ALTER TABLE players ADD COLUMN level INTEGER NOT NULL DEFAULT 1",

        "login_streak":
            "ALTER TABLE players ADD COLUMN login_streak INTEGER NOT NULL DEFAULT 0",

        "last_login":
            "ALTER TABLE players ADD COLUMN last_login TEXT",

        "daily_bonus_date":
            "ALTER TABLE players ADD COLUMN daily_bonus_date TEXT",

        "task_date":
            "ALTER TABLE players ADD COLUMN task_date TEXT",

        "task_taps":
            "ALTER TABLE players ADD COLUMN task_taps INTEGER NOT NULL DEFAULT 0",

        "task_games":
            "ALTER TABLE players ADD COLUMN task_games INTEGER NOT NULL DEFAULT 0",

        "task_eggs":
            "ALTER TABLE players ADD COLUMN task_eggs INTEGER NOT NULL DEFAULT 0",

        "boss_damage":
            "ALTER TABLE players ADD COLUMN boss_damage INTEGER NOT NULL DEFAULT 0",

        "avatar":
            "ALTER TABLE players ADD COLUMN avatar TEXT NOT NULL DEFAULT '🥚'"
    }

    for column, query in migrations.items():

        if column not in columns:

            print(
                f"Миграция players: добавляем {column}"
            )

            cur.execute(query)

    # =====================================================
    # DEFAULT BOSS
    # =====================================================

    cur.execute("""
        INSERT OR IGNORE INTO boss_event (
            id,
            boss_name,
            max_hp,
            current_hp,
            active
        )
        VALUES (
            1,
            'Король Яиц',
            100000,
            100000,
            0
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# PLAYER
# =========================================================

def create_player(
    user_id,
    username=None,
    avatar="🥚"
):

    conn = get_connection()

    conn.execute("""
        INSERT OR IGNORE INTO players (
            user_id,
            username,
            avatar
        )
        VALUES (?, ?, ?)
    """, (
        int(user_id),
        username,
        avatar
    ))

    conn.commit()
    conn.close()


def ensure_player(
    user_id,
    username=None,
    first_name=None
):

    user_id = int(user_id)

    conn = get_connection()

    row = conn.execute("""
        SELECT user_id
        FROM players
        WHERE user_id = ?
    """, (
        user_id,
    )).fetchone()

    if row is None:

        display_name = (
            username
            or first_name
            or "Игрок"
        )

        conn.execute("""
            INSERT INTO players (
                user_id,
                username,
                avatar
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            display_name,
            "🥚"
        ))

    else:

        if username:

            conn.execute("""
                UPDATE players
                SET username = ?
                WHERE user_id = ?
            """, (
                username,
                user_id
            ))

    conn.commit()
    conn.close()


def get_player(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    return dict(row) if row else None


def update_username(
    user_id,
    username
):

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET username = ?
        WHERE user_id = ?
    """, (
        username,
        int(user_id)
    ))

    conn.commit()
    conn.close()


# =========================================================
# BALANCES
# =========================================================

def get_tap_coins(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT tap_coins
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    return int(
        row["tap_coins"]
        if row
        else 0
    )


def add_tap_coins(
    user_id,
    amount
):

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET tap_coins = tap_coins + ?
        WHERE user_id = ?
    """, (
        int(amount),
        int(user_id)
    ))

    conn.commit()
    conn.close()


def remove_tap_coins(
    user_id,
    amount
):

    conn = get_connection()

    cur = conn.execute("""
        UPDATE players
        SET tap_coins = tap_coins - ?
        WHERE user_id = ?
          AND tap_coins >= ?
    """, (
        int(amount),
        int(user_id),
        int(amount)
    ))

    if cur.rowcount == 0:

        conn.rollback()
        conn.close()

        raise ValueError(
            "Недостаточно Tap Coins"
        )

    conn.commit()
    conn.close()


def get_egg_coins(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT egg_coins
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    return int(
        row["egg_coins"]
        if row
        else 0
    )


def add_egg_coins(
    user_id,
    amount
):

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET egg_coins = egg_coins + ?
        WHERE user_id = ?
    """, (
        int(amount),
        int(user_id)
    ))

    conn.commit()
    conn.close()


def remove_egg_coins(
    user_id,
    amount
):

    conn = get_connection()

    cur = conn.execute("""
        UPDATE players
        SET egg_coins = egg_coins - ?
        WHERE user_id = ?
          AND egg_coins >= ?
    """, (
        int(amount),
        int(user_id),
        int(amount)
    ))

    if cur.rowcount == 0:

        conn.rollback()
        conn.close()

        raise ValueError(
            "Недостаточно Egg Coins"
        )

    conn.commit()
    conn.close()


# =========================================================
# EGGS
# =========================================================

def add_egg(
    user_id,
    egg_id
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO player_eggs (
            user_id,
            egg_id
        )
        VALUES (?, ?)
    """, (
        int(user_id),
        int(egg_id)
    ))

    conn.commit()
    conn.close()


def get_player_eggs(user_id):

    conn = get_connection()

    rows = conn.execute("""
        SELECT egg_id
        FROM player_eggs
        WHERE user_id = ?
        ORDER BY id ASC
    """, (
        int(user_id),
    )).fetchall()

    conn.close()

    return [
        int(row["egg_id"])
        for row in rows
    ]


def get_egg_count(
    user_id,
    egg_id
):

    conn = get_connection()

    row = conn.execute("""
        SELECT COUNT(*) AS count
        FROM player_eggs
        WHERE user_id = ?
          AND egg_id = ?
    """, (
        int(user_id),
        int(egg_id)
    )).fetchone()

    conn.close()

    return int(
        row["count"]
    )


def remove_one_egg(
    user_id,
    egg_id
):

    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM player_eggs
        WHERE user_id = ?
          AND egg_id = ?
        ORDER BY id ASC
        LIMIT 1
    """, (
        int(user_id),
        int(egg_id)
    )).fetchone()

    if not row:

        conn.rollback()
        conn.close()

        raise ValueError(
            "У тебя нет этого яйца"
        )

    conn.execute("""
        DELETE FROM player_eggs
        WHERE id = ?
    """, (
        int(row["id"]),
    ))

    conn.commit()
    conn.close()


def get_total_eggs(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT COUNT(*) AS count
        FROM player_eggs
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    return int(
        row["count"]
    )


# =========================================================
# EGG RARITIES
# =========================================================

def add_egg_type(
    egg_id,
    name,
    rarity,
    rarity_order=1,
    marketable=1
):

    conn = get_connection()

    conn.execute("""
        INSERT OR REPLACE INTO egg_types (
            egg_id,
            name,
            rarity,
            rarity_order,
            marketable
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        int(egg_id),
        name,
        rarity,
        int(rarity_order),
        int(marketable)
    ))

    conn.commit()
    conn.close()


def get_egg_type(egg_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM egg_types
        WHERE egg_id = ?
    """, (
        int(egg_id),
    )).fetchone()

    conn.close()

    return dict(row) if row else None


def get_all_egg_types():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM egg_types
        ORDER BY rarity_order ASC, egg_id ASC
    """).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# XP / LEVEL
# =========================================================

def get_progress(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT xp, level
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    if not row:
        return 0, 1

    return (
        int(row["xp"]),
        int(row["level"])
    )


def add_xp(
    user_id,
    amount
):

    amount = int(amount)

    conn = get_connection()

    row = conn.execute("""
        SELECT xp, level
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    if not row:

        conn.close()

        raise ValueError(
            "Игрок не найден"
        )

    old_xp = int(
        row["xp"]
    )

    old_level = int(
        row["level"]
    )

    new_xp = old_xp + amount

    new_level = (
        new_xp // 100
    ) + 1

    conn.execute("""
        UPDATE players
        SET xp = ?,
            level = ?
        WHERE user_id = ?
    """, (
        new_xp,
        new_level,
        int(user_id)
    ))

    conn.commit()
    conn.close()

    return {

        "xp": new_xp,

        "level": new_level,

        "old_level":
            old_level,

        "level_up":
            new_level > old_level
    }


# =========================================================
# LOGIN STREAK
# =========================================================

def get_login_streak(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT login_streak
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    return int(
        row["login_streak"]
        if row
        else 0
    )


def update_login(user_id):

    today = date.today().isoformat()

    conn = get_connection()

    row = conn.execute("""
        SELECT last_login,
               login_streak
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    if not row:

        conn.close()

        return

    last_login = row["last_login"]

    streak = int(
        row["login_streak"]
    )

    if last_login == today:

        conn.close()
        return

    if last_login:

        try:

            last_date = date.fromisoformat(
                last_login
            )

            days = (
                date.today()
                - last_date
            ).days

            if days == 1:

                streak += 1

            else:

                streak = 1

        except Exception:

            streak = 1

    else:

        streak = 1

    conn.execute("""
        UPDATE players
        SET last_login = ?,
            login_streak = ?
        WHERE user_id = ?
    """, (
        today,
        streak,
        int(user_id)
    ))

    conn.commit()
    conn.close()


def get_login_status(user_id):

    today = date.today().isoformat()

    conn = get_connection()

    row = conn.execute("""
        SELECT last_login,
               login_streak
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    if not row:

        return False, 0, 0

    claimed = (
        row["last_login"] == today
    )

    streak = int(
        row["login_streak"]
    )

    reward = 5 * max(
        streak,
        1
    )

    return (
        claimed,
        streak,
        reward
    )


def set_daily_login(user_id):

    today = date.today().isoformat()

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET last_login = ?
        WHERE user_id = ?
    """, (
        today,
        int(user_id)
    ))

    conn.commit()
    conn.close()


# =========================================================
# DAILY BONUS
# =========================================================

def get_daily_bonus_date(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT daily_bonus_date
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    if not row:

        return None

    return row["daily_bonus_date"]


def set_daily_bonus_date(
    user_id,
    value
):

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET daily_bonus_date = ?
        WHERE user_id = ?
    """, (
        value,
        int(user_id)
    ))

    conn.commit()
    conn.close()


# =========================================================
# DAILY TASKS
# =========================================================

def get_daily_tasks(user_id):

    today = date.today().isoformat()

    conn = get_connection()

    row = conn.execute("""
        SELECT task_date,
               task_taps,
               task_games,
               task_eggs
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    if not row:

        conn.close()

        return 0, 0, 0

    task_date = row["task_date"]

    if task_date != today:

        conn.execute("""
            UPDATE players
            SET task_date = ?,
                task_taps = 0,
                task_games = 0,
                task_eggs = 0
            WHERE user_id = ?
        """, (
            today,
            int(user_id)
        ))

        conn.execute("""
            DELETE FROM daily_task_claims
            WHERE user_id = ?
              AND task_date != ?
        """, (
            int(user_id),
            today
        ))

        conn.commit()
        conn.close()

        return 0, 0, 0

    result = (
        int(row["task_taps"] or 0),
        int(row["task_games"] or 0),
        int(row["task_eggs"] or 0)
    )

    conn.close()

    return result


def add_task_tap(user_id):

    get_daily_tasks(user_id)

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET task_taps = task_taps + 1
        WHERE user_id = ?
    """, (
        int(user_id),
    ))

    conn.commit()
    conn.close()


def add_task_game(user_id):

    get_daily_tasks(user_id)

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET task_games = task_games + 1
        WHERE user_id = ?
    """, (
        int(user_id),
    ))

    conn.commit()
    conn.close()


def add_task_egg(user_id):

    get_daily_tasks(user_id)

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET task_eggs = task_eggs + 1
        WHERE user_id = ?
    """, (
        int(user_id),
    ))

    conn.commit()
    conn.close()


def has_daily_task_claim(
    user_id,
    task_id
):

    today = date.today().isoformat()

    conn = get_connection()

    row = conn.execute("""
        SELECT 1
        FROM daily_task_claims
        WHERE user_id = ?
          AND task_date = ?
          AND task_id = ?
        LIMIT 1
    """, (
        int(user_id),
        today,
        int(task_id)
    )).fetchone()

    conn.close()

    return row is not None


def add_daily_task_claim(
    user_id,
    task_id
):

    today = date.today().isoformat()

    conn = get_connection()

    conn.execute("""
        INSERT OR IGNORE INTO daily_task_claims (
            user_id,
            task_date,
            task_id
        )
        VALUES (?, ?, ?)
    """, (
        int(user_id),
        today,
        int(task_id)
    ))

    conn.commit()
    conn.close()


# =========================================================
# ADVANCED DAILY QUESTS
# =========================================================

def clear_old_daily_quests(user_id):

    today = date.today().isoformat()

    conn = get_connection()

    conn.execute("""
        DELETE FROM daily_quests
        WHERE user_id = ?
          AND task_date != ?
    """, (
        int(user_id),
        today
    ))

    conn.commit()
    conn.close()


def get_daily_quests(user_id):

    today = date.today().isoformat()

    clear_old_daily_quests(user_id)

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM daily_quests
        WHERE user_id = ?
          AND task_date = ?
        ORDER BY id ASC
    """, (
        int(user_id),
        today
    )).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


def create_daily_quest(
    user_id,
    quest_id,
    target,
    reward_type,
    reward_amount
):

    today = date.today().isoformat()

    conn = get_connection()

    conn.execute("""
        INSERT INTO daily_quests (
            user_id,
            task_date,
            quest_id,
            progress,
            target,
            reward_type,
            reward_amount,
            claimed
        )
        VALUES (?, ?, ?, 0, ?, ?, ?, 0)
    """, (
        int(user_id),
        today,
        int(quest_id),
        int(target),
        reward_type,
        int(reward_amount)
    ))

    conn.commit()
    conn.close()


def update_daily_quest(
    user_id,
    quest_id,
    amount=1
):

    today = date.today().isoformat()

    conn = get_connection()

    conn.execute("""
        UPDATE daily_quests

        SET progress = MIN(
            progress + ?,
            target
        )

        WHERE user_id = ?
          AND task_date = ?
          AND quest_id = ?
          AND claimed = 0
    """, (
        int(amount),
        int(user_id),
        today,
        int(quest_id)
    ))

    conn.commit()
    conn.close()


def claim_daily_quest(
    user_id,
    quest_id
):

    today = date.today().isoformat()

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM daily_quests

        WHERE user_id = ?
          AND task_date = ?
          AND quest_id = ?
          AND claimed = 0
    """, (
        int(user_id),
        today,
        int(quest_id)
    )).fetchone()

    if not row:

        conn.close()

        raise ValueError(
            "Задание не найдено"
        )

    if int(row["progress"]) < int(row["target"]):

        conn.close()

        raise ValueError(
            "Задание ещё не выполнено"
        )

    conn.execute("""
        UPDATE daily_quests
        SET claimed = 1
        WHERE user_id = ?
          AND task_date = ?
          AND quest_id = ?
    """, (
        int(user_id),
        today,
        int(quest_id)
    ))

    conn.commit()
    conn.close()

    return {
        "reward_type": row["reward_type"],
        "reward_amount": int(row["reward_amount"])
    }


# =========================================================
# ACHIEVEMENTS
# =========================================================

def has_achievement(
    user_id,
    achievement_id
):

    conn = get_connection()

    row = conn.execute("""
        SELECT 1
        FROM achievements
        WHERE user_id = ?
          AND achievement_id = ?
        LIMIT 1
    """, (
        int(user_id),
        int(achievement_id)
    )).fetchone()

    conn.close()

    return row is not None


def add_achievement(
    user_id,
    achievement_id
):

    conn = get_connection()

    conn.execute("""
        INSERT OR IGNORE INTO achievements (
            user_id,
            achievement_id
        )
        VALUES (?, ?)
    """, (
        int(user_id),
        int(achievement_id)
    ))

    conn.commit()
    conn.close()


def get_achievements(user_id):

    conn = get_connection()

    rows = conn.execute("""
        SELECT achievement_id
        FROM achievements
        WHERE user_id = ?
        ORDER BY id ASC
    """, (
        int(user_id),
    )).fetchall()

    conn.close()

    return [
        {
            "achievement_id":
                int(row["achievement_id"])
        }
        for row in rows
    ]


# =========================================================
# ITEMS
# =========================================================

def add_item(
    user_id,
    item_id
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO player_items (
            user_id,
            item_id
        )
        VALUES (?, ?)
    """, (
        int(user_id),
        int(item_id)
    ))

    conn.commit()
    conn.close()


def get_item_count(
    user_id,
    item_id
):

    conn = get_connection()

    row = conn.execute("""
        SELECT COUNT(*) AS count
        FROM player_items
        WHERE user_id = ?
          AND item_id = ?
    """, (
        int(user_id),
        int(item_id)
    )).fetchone()

    conn.close()

    return int(
        row["count"]
    )


def remove_item(
    user_id,
    item_id
):

    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM player_items
        WHERE user_id = ?
          AND item_id = ?
        ORDER BY id ASC
        LIMIT 1
    """, (
        int(user_id),
        int(item_id)
    )).fetchone()

    if not row:

        conn.rollback()
        conn.close()

        raise ValueError(
            "Предмет не найден"
        )

    conn.execute("""
        DELETE FROM player_items
        WHERE id = ?
    """, (
        int(row["id"]),
    ))

    conn.commit()
    conn.close()


def get_player_items(user_id):

    conn = get_connection()

    rows = conn.execute("""
        SELECT item_id,
               COUNT(*) AS count
        FROM player_items
        WHERE user_id = ?
        GROUP BY item_id
    """, (
        int(user_id),
    )).fetchall()

    conn.close()

    result = {}

    for row in rows:

        result[str(
            row["item_id"]
        )] = int(
            row["count"]
        )

    return result


# =========================================================
# CHESTS
# =========================================================

def add_chest(
    user_id,
    chest_id
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO player_chests (
            user_id,
            chest_id,
            created_at
        )
        VALUES (?, ?, ?)
    """, (
        int(user_id),
        int(chest_id),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_chest_count(
    user_id,
    chest_id
):

    conn = get_connection()

    row = conn.execute("""
        SELECT COUNT(*) AS count
        FROM player_chests
        WHERE user_id = ?
          AND chest_id = ?
    """, (
        int(user_id),
        int(chest_id)
    )).fetchone()

    conn.close()

    return int(row["count"])


def get_player_chests(user_id):

    conn = get_connection()

    rows = conn.execute("""
        SELECT chest_id,
               COUNT(*) AS count
        FROM player_chests
        WHERE user_id = ?
        GROUP BY chest_id
        ORDER BY chest_id ASC
    """, (
        int(user_id),
    )).fetchall()

    conn.close()

    return {
        str(row["chest_id"]):
            int(row["count"])
        for row in rows
    }


def remove_chest(
    user_id,
    chest_id
):

    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM player_chests
        WHERE user_id = ?
          AND chest_id = ?
        ORDER BY id ASC
        LIMIT 1
    """, (
        int(user_id),
        int(chest_id)
    )).fetchone()

    if not row:

        conn.close()

        raise ValueError(
            "Сундук не найден"
        )

    conn.execute("""
        DELETE FROM player_chests
        WHERE id = ?
    """, (
        int(row["id"]),
    ))

    conn.commit()
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

    conn.execute("""
        INSERT OR REPLACE INTO pets (
            pet_id,
            name,
            rarity,
            bonus_type,
            bonus_value
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        int(pet_id),
        name,
        rarity,
        bonus_type,
        float(bonus_value)
    ))

    conn.commit()
    conn.close()


def get_pet_type(pet_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM pets
        WHERE pet_id = ?
    """, (
        int(pet_id),
    )).fetchone()

    conn.close()

    return dict(row) if row else None


def get_all_pets():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM pets
        ORDER BY pet_id ASC
    """).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


def add_pet(
    user_id,
    pet_id,
    active=0
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO player_pets (
            user_id,
            pet_id,
            active,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        int(user_id),
        int(pet_id),
        int(active),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_player_pets(user_id):

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            pp.id,
            pp.pet_id,
            pp.active,
            pp.created_at,
            p.name,
            p.rarity,
            p.bonus_type,
            p.bonus_value

        FROM player_pets pp

        LEFT JOIN pets p
            ON p.pet_id = pp.pet_id

        WHERE pp.user_id = ?

        ORDER BY pp.id ASC
    """, (
        int(user_id),
    )).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


def get_active_pet(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT
            pp.id,
            pp.pet_id,
            p.name,
            p.rarity,
            p.bonus_type,
            p.bonus_value

        FROM player_pets pp

        LEFT JOIN pets p
            ON p.pet_id = pp.pet_id

        WHERE pp.user_id = ?
          AND pp.active = 1

        ORDER BY pp.id ASC
        LIMIT 1
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    return dict(row) if row else None


def set_active_pet(
    user_id,
    player_pet_id
):

    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM player_pets
        WHERE id = ?
          AND user_id = ?
    """, (
        int(player_pet_id),
        int(user_id)
    )).fetchone()

    if not row:

        conn.close()

        raise ValueError(
            "Питомец не найден"
        )

    conn.execute("""
        UPDATE player_pets
        SET active = 0
        WHERE user_id = ?
    """, (
        int(user_id),
    ))

    conn.execute("""
        UPDATE player_pets
        SET active = 1
        WHERE id = ?
          AND user_id = ?
    """, (
        int(player_pet_id),
        int(user_id)
    ))

    conn.commit()
    conn.close()


def remove_pet(
    user_id,
    player_pet_id
):

    conn = get_connection()

    conn.execute("""
        DELETE FROM player_pets
        WHERE id = ?
          AND user_id = ?
    """, (
        int(player_pet_id),
        int(user_id)
    ))

    conn.commit()
    conn.close()


# =========================================================
# MARKET
# =========================================================

def create_market_listing(
    seller_id,
    egg_id,
    price
):

    price = int(price)

    if price <= 0:

        raise ValueError(
            "Цена должна быть больше 0"
        )

    conn = get_connection()

    # Проверяем, есть ли яйцо
    row = conn.execute("""
        SELECT id
        FROM player_eggs
        WHERE user_id = ?
          AND egg_id = ?
        ORDER BY id ASC
        LIMIT 1
    """, (
        int(seller_id),
        int(egg_id)
    )).fetchone()

    if not row:

        conn.close()

        raise ValueError(
            "У тебя нет этого яйца"
        )

    # Проверяем, можно ли продавать это яйцо
    egg = conn.execute("""
        SELECT marketable
        FROM egg_types
        WHERE egg_id = ?
    """, (
        int(egg_id),
    )).fetchone()

    if egg and int(egg["marketable"]) == 0:

        conn.close()

        raise ValueError(
            "Это яйцо нельзя выставить на рынок"
        )

    # Удаляем яйцо из инвентаря
    conn.execute("""
        DELETE FROM player_eggs
        WHERE id = ?
    """, (
        int(row["id"]),
    ))

    # Создаём объявление
    cur = conn.execute("""
        INSERT INTO market_listings (
            seller_id,
            egg_id,
            price,
            status,
            created_at
        )
        VALUES (?, ?, ?, 'active', ?)
    """, (
        int(seller_id),
        int(egg_id),
        price,
        datetime.now().isoformat()
    ))

    listing_id = cur.lastrowid

    conn.commit()
    conn.close()

    return listing_id


def get_market_listings(
    egg_id=None,
    limit=50
):

    conn = get_connection()

    if egg_id is None:

        rows = conn.execute("""
            SELECT *
            FROM market_listings

            WHERE status = 'active'

            ORDER BY price ASC, id ASC

            LIMIT ?
        """, (
            int(limit),
        )).fetchall()

    else:

        rows = conn.execute("""
            SELECT *
            FROM market_listings

            WHERE status = 'active'
              AND egg_id = ?

            ORDER BY price ASC, id ASC

            LIMIT ?
        """, (
            int(egg_id),
            int(limit)
        )).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


def get_market_listing(listing_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM market_listings
        WHERE id = ?
    """, (
        int(listing_id),
    )).fetchone()

    conn.close()

    return dict(row) if row else None


def cancel_market_listing(
    seller_id,
    listing_id
):

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM market_listings

        WHERE id = ?
          AND seller_id = ?
          AND status = 'active'
    """, (
        int(listing_id),
        int(seller_id)
    )).fetchone()

    if not row:

        conn.close()

        raise ValueError(
            "Объявление не найдено"
        )

    # Возвращаем яйцо владельцу
    conn.execute("""
        INSERT INTO player_eggs (
            user_id,
            egg_id
        )
        VALUES (?, ?)
    """, (
        int(seller_id),
        int(row["egg_id"])
    ))

    conn.execute("""
        UPDATE market_listings
        SET status = 'cancelled'
        WHERE id = ?
    """, (
        int(listing_id),
    ))

    conn.commit()
    conn.close()


def buy_market_listing(
    buyer_id,
    listing_id
):

    buyer_id = int(buyer_id)

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM market_listings

        WHERE id = ?
          AND status = 'active'
    """, (
        int(listing_id),
    )).fetchone()

    if not row:

        conn.close()

        raise ValueError(
            "Объявление уже недоступно"
        )

    if int(row["seller_id"]) == buyer_id:

        conn.close()

        raise ValueError(
            "Нельзя купить собственное яйцо"
        )

    price = int(row["price"])

    # Сначала списываем деньги атомарно
    cur = conn.execute("""
        UPDATE players

        SET egg_coins = egg_coins - ?

        WHERE user_id = ?
          AND egg_coins >= ?
    """, (
        price,
        buyer_id,
        price
    ))

    if cur.rowcount == 0:

        conn.rollback()
        conn.close()

        raise ValueError(
            "Недостаточно Egg Coins"
        )

    # Комиссия рынка 5%
    fee = max(
        1,
        int(price * 0.05)
    )

    seller_reward = price - fee

    # Деньги продавцу
    conn.execute("""
        UPDATE players

        SET egg_coins = egg_coins + ?

        WHERE user_id = ?
    """, (
        seller_reward,
        int(row["seller_id"])
    ))

    # Яйцо покупателю
    conn.execute("""
        INSERT INTO player_eggs (
            user_id,
            egg_id
        )
        VALUES (?, ?)
    """, (
        buyer_id,
        int(row["egg_id"])
    ))

    # Закрываем объявление
    conn.execute("""
        UPDATE market_listings

        SET status = 'sold',
            buyer_id = ?,
            sold_at = ?

        WHERE id = ?
          AND status = 'active'
    """, (
        buyer_id,
        datetime.now().isoformat(),
        int(listing_id)
    ))

    conn.commit()
    conn.close()

    return {
        "price": price,
        "fee": fee,
        "seller_reward": seller_reward,
        "egg_id": int(row["egg_id"])
    }


def get_player_market_listings(user_id):

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM market_listings

        WHERE seller_id = ?

        ORDER BY id DESC
    """, (
        int(user_id),
    )).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# EGG PROTECTION
# =========================================================

def set_egg_protection(
    user_id,
    seconds
):

    until = datetime.now().timestamp() + int(seconds)

    conn = get_connection()

    conn.execute("""
        INSERT OR REPLACE INTO egg_protection (
            user_id,
            protection_until
        )
        VALUES (?, ?)
    """, (
        int(user_id),
        datetime.fromtimestamp(until).isoformat()
    ))

    conn.commit()
    conn.close()


def is_egg_protected(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT protection_until
        FROM egg_protection
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    if not row or not row["protection_until"]:

        return False

    try:

        until = datetime.fromisoformat(
            row["protection_until"]
        )

        return datetime.now() < until

    except Exception:

        return False


# =========================================================
# THEFT SYSTEM
# =========================================================

def add_steal_attempt(
    thief_id,
    victim_id,
    egg_id,
    success
):

    conn = get_connection()

    conn.execute("""
        INSERT INTO steal_attempts (
            thief_id,
            victim_id,
            egg_id,
            success,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        int(thief_id),
        int(victim_id),
        int(egg_id),
        int(success),
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def get_last_steal_attempt(thief_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM steal_attempts

        WHERE thief_id = ?

        ORDER BY id DESC

        LIMIT 1
    """, (
        int(thief_id),
    )).fetchone()

    conn.close()

    return dict(row) if row else None


def get_steal_attempts_today(thief_id):

    today = date.today().isoformat()

    conn = get_connection()

    row = conn.execute("""
        SELECT COUNT(*) AS count
        FROM steal_attempts

        WHERE thief_id = ?
          AND created_at LIKE ?
    """, (
        int(thief_id),
        today + "%"
    )).fetchone()

    conn.close()

    return int(row["count"])


def transfer_stolen_egg(
    thief_id,
    victim_id,
    egg_id
):

    thief_id = int(thief_id)
    victim_id = int(victim_id)
    egg_id = int(egg_id)

    if thief_id == victim_id:

        raise ValueError(
            "Нельзя красть яйцо у себя"
        )

    conn = get_connection()

    row = conn.execute("""
        SELECT id
        FROM player_eggs

        WHERE user_id = ?
          AND egg_id = ?

        ORDER BY id ASC

        LIMIT 1
    """, (
        victim_id,
        egg_id
    )).fetchone()

    if not row:

        conn.close()

        raise ValueError(
            "У игрока нет такого яйца"
        )

    conn.execute("""
        DELETE FROM player_eggs
        WHERE id = ?
    """, (
        int(row["id"]),
    ))

    conn.execute("""
        INSERT INTO player_eggs (
            user_id,
            egg_id
        )
        VALUES (?, ?)
    """, (
        thief_id,
        egg_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# BOSS EVENT
# =========================================================

def start_boss_event(
    boss_name="Король Яиц",
    max_hp=100000,
    duration_seconds=86400
):

    now = datetime.now()

    ends = (
        now.timestamp()
        + int(duration_seconds)
    )

    conn = get_connection()

    conn.execute("""
        UPDATE boss_event

        SET boss_name = ?,
            max_hp = ?,
            current_hp = ?,
            started_at = ?,
            ends_at = ?,
            active = 1,
            reward_claimed = 0

        WHERE id = 1
    """, (
        boss_name,
        int(max_hp),
        int(max_hp),
        now.isoformat(),
        datetime.fromtimestamp(ends).isoformat()
    ))

    conn.execute("""
        DELETE FROM boss_participants
    """)

    conn.commit()
    conn.close()


def get_boss_event():

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM boss_event
        WHERE id = 1
    """).fetchone()

    conn.close()

    return dict(row) if row else None


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

    boss = conn.execute("""
        SELECT current_hp,
               active
        FROM boss_event
        WHERE id = 1
    """).fetchone()

    if not boss or int(boss["active"]) != 1:

        conn.close()

        raise ValueError(
            "Босс сейчас не активен"
        )

    current_hp = int(
        boss["current_hp"]
    )

    actual_damage = min(
        amount,
        current_hp
    )

    new_hp = (
        current_hp
        - actual_damage
    )

    conn.execute("""
        UPDATE boss_event
        SET current_hp = ?
        WHERE id = 1
    """, (
        new_hp,
    ))

    conn.execute("""
        INSERT OR IGNORE INTO boss_participants (
            user_id,
            damage,
            reward_claimed
        )
        VALUES (?, 0, 0)
    """, (
        int(user_id),
    ))

    conn.execute("""
        UPDATE boss_participants

        SET damage = damage + ?

        WHERE user_id = ?
    """, (
        actual_damage,
        int(user_id)
    ))

    conn.execute("""
        UPDATE players
        SET boss_damage = boss_damage + ?
        WHERE user_id = ?
    """, (
        actual_damage,
        int(user_id)
    ))

    if new_hp <= 0:

        conn.execute("""
            UPDATE boss_event
            SET active = 0
            WHERE id = 1
        """)

    conn.commit()
    conn.close()

    return actual_damage


def get_boss_participants():

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM boss_participants

        ORDER BY damage DESC
    """).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


def get_boss_damage(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT boss_damage
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    return int(
        row["boss_damage"]
        if row
        else 0
    )


def add_boss_damage(
    user_id,
    amount
):

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET boss_damage = boss_damage + ?
        WHERE user_id = ?
    """, (
        int(amount),
        int(user_id)
    ))

    conn.commit()
    conn.close()


def claim_boss_reward(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT damage,
               reward_claimed

        FROM boss_participants

        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    if not row:

        conn.close()

        raise ValueError(
            "Ты не участвовал в событии"
        )

    if int(row["reward_claimed"]) == 1:

        conn.close()

        raise ValueError(
            "Награда уже получена"
        )

    boss = conn.execute("""
        SELECT current_hp,
               active
        FROM boss_event
        WHERE id = 1
    """).fetchone()

    if boss and int(boss["active"]) == 1:

        conn.close()

        raise ValueError(
            "Босс ещё не побеждён"
        )

    conn.execute("""
        UPDATE boss_participants
        SET reward_claimed = 1
        WHERE user_id = ?
    """, (
        int(user_id),
    ))

    conn.commit()
    conn.close()

    return int(row["damage"])


# =========================================================
# EGG PASS
# =========================================================

def ensure_egg_pass(user_id):

    conn = get_connection()

    conn.execute("""
        INSERT OR IGNORE INTO egg_pass (
            user_id,
            xp,
            level,
            premium
        )
        VALUES (?, 0, 1, 0)
    """, (
        int(user_id),
    ))

    conn.commit()
    conn.close()


def get_egg_pass(user_id):

    ensure_egg_pass(user_id)

    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM egg_pass
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    return dict(row) if row else None


def add_egg_pass_xp(
    user_id,
    amount
):

    amount = max(
        0,
        int(amount)
    )

    ensure_egg_pass(user_id)

    conn = get_connection()

    row = conn.execute("""
        SELECT xp,
               level
        FROM egg_pass
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    old_level = int(
        row["level"]
    )

    new_xp = int(
        row["xp"]
    ) + amount

    # 100 XP = 1 уровень Egg Pass
    new_level = min(
        30,
        (new_xp // 100) + 1
    )

    conn.execute("""
        UPDATE egg_pass

        SET xp = ?,
            level = ?

        WHERE user_id = ?
    """, (
        new_xp,
        new_level,
        int(user_id)
    ))

    conn.commit()
    conn.close()

    return {
        "xp": new_xp,
        "level": new_level,
        "level_up": new_level > old_level
    }


def set_egg_pass_premium(
    user_id,
    premium=True
):

    ensure_egg_pass(user_id)

    conn = get_connection()

    conn.execute("""
        UPDATE egg_pass
        SET premium = ?
        WHERE user_id = ?
    """, (
        1 if premium else 0,
        int(user_id)
    ))

    conn.commit()
    conn.close()


def has_egg_pass_reward(
    user_id,
    level,
    track
):

    conn = get_connection()

    row = conn.execute("""
        SELECT 1

        FROM egg_pass_claims

        WHERE user_id = ?
          AND level = ?
          AND track = ?

        LIMIT 1
    """, (
        int(user_id),
        int(level),
        track
    )).fetchone()

    conn.close()

    return row is not None


def claim_egg_pass_reward(
    user_id,
    level,
    track
):

    ensure_egg_pass(user_id)

    conn = get_connection()

    pass_row = conn.execute("""
        SELECT level,
               premium
        FROM egg_pass
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    if not pass_row:

        conn.close()

        raise ValueError(
            "Egg Pass не найден"
        )

    if int(pass_row["level"]) < int(level):

        conn.close()

        raise ValueError(
            "Этот уровень Egg Pass ещё не открыт"
        )

    if track == "premium" and int(
        pass_row["premium"]
    ) != 1:

        conn.close()

        raise ValueError(
            "Нужен Premium Egg Pass"
        )

    if has_egg_pass_reward(
        user_id,
        level,
        track
    ):

        conn.close()

        raise ValueError(
            "Награда уже получена"
        )

    conn.execute("""
        INSERT INTO egg_pass_claims (
            user_id,
            level,
            track
        )
        VALUES (?, ?, ?)
    """, (
        int(user_id),
        int(level),
        track
    ))

    conn.commit()
    conn.close()


# =========================================================
# AVATAR
# =========================================================

def get_avatar(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT avatar
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    if not row:

        return "🥚"

    return (
        row["avatar"]
        or "🥚"
    )


def set_avatar(
    user_id,
    avatar
):

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET avatar = ?
        WHERE user_id = ?
    """, (
        avatar,
        int(user_id)
    ))

    conn.commit()
    conn.close()


# =========================================================
# BLOCK
# =========================================================

def block_player(user_id):

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET blocked = 1
        WHERE user_id = ?
    """, (
        int(user_id),
    ))

    conn.commit()
    conn.close()


def unblock_player(user_id):

    conn = get_connection()

    conn.execute("""
        UPDATE players
        SET blocked = 0
        WHERE user_id = ?
    """, (
        int(user_id),
    ))

    conn.commit()
    conn.close()


def is_blocked(user_id):

    conn = get_connection()

    row = conn.execute("""
        SELECT blocked
        FROM players
        WHERE user_id = ?
    """, (
        int(user_id),
    )).fetchone()

    conn.close()

    return bool(
        row["blocked"]
        if row
        else False
    )


# =========================================================
# PLAYERS / LEADERBOARD
# =========================================================

def get_all_players():

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            user_id,
            username,
            tap_coins,
            egg_coins,
            xp,
            level,
            blocked,
            avatar
        FROM players
    """).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


def get_top_players(
    limit=10
):

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            user_id,
            username,
            tap_coins,
            egg_coins,
            xp,
            level,
            avatar
        FROM players

        ORDER BY
            egg_coins DESC,
            tap_coins DESC,
            xp DESC

        LIMIT ?
    """, (
        int(limit),
    )).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# =========================================================
# START DATABASE
# =========================================================

init_database()
