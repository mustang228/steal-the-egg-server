import sqlite3
from pathlib import Path
from datetime import date


DB_PATH = Path(__file__).resolve().parent / "players.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# DATABASE INIT
# =========================================================

def init_database():
    conn = get_connection()
    cur = conn.cursor()

    # -----------------------------------------------------
    # PLAYERS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id INTEGER PRIMARY KEY,
            tap_coins INTEGER DEFAULT 0,
            egg_coins INTEGER DEFAULT 0,
            username TEXT DEFAULT '',
            blocked INTEGER DEFAULT 0,

            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,

            login_streak INTEGER DEFAULT 0,
            last_login TEXT DEFAULT '',

            daily_bonus_date TEXT DEFAULT '',

            task_date TEXT DEFAULT '',
            task_taps INTEGER DEFAULT 0,
            task_games INTEGER DEFAULT 0,
            task_eggs INTEGER DEFAULT 0,

            boss_damage INTEGER DEFAULT 0
        )
    """)

    # -----------------------------------------------------
    # EGGS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_eggs (
            user_id INTEGER,
            egg_id INTEGER,
            count INTEGER DEFAULT 0,

            PRIMARY KEY (user_id, egg_id)
        )
    """)

    # -----------------------------------------------------
    # ITEMS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_items (
            user_id INTEGER,
            item_id INTEGER,
            count INTEGER DEFAULT 0,

            PRIMARY KEY (user_id, item_id)
        )
    """)

    # -----------------------------------------------------
    # ACHIEVEMENTS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            user_id INTEGER,
            achievement_id INTEGER,

            PRIMARY KEY (user_id, achievement_id)
        )
    """)

    # -----------------------------------------------------
    # DAILY TASK CLAIMS
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_task_claims (
            user_id INTEGER,
            task_date TEXT,
            task_id TEXT,

            PRIMARY KEY (user_id, task_date, task_id)
        )
    """)

    conn.commit()

    # -----------------------------------------------------
    # ADD MISSING COLUMNS
    # -----------------------------------------------------

    cur.execute("PRAGMA table_info(players)")
    columns = [row["name"] for row in cur.fetchall()]

    required_columns = {
        "tap_coins": "INTEGER DEFAULT 0",
        "egg_coins": "INTEGER DEFAULT 0",
        "username": "TEXT DEFAULT ''",
        "blocked": "INTEGER DEFAULT 0",
        "xp": "INTEGER DEFAULT 0",
        "level": "INTEGER DEFAULT 1",
        "login_streak": "INTEGER DEFAULT 0",
        "last_login": "TEXT DEFAULT ''",
        "daily_bonus_date": "TEXT DEFAULT ''",
        "task_date": "TEXT DEFAULT ''",
        "task_taps": "INTEGER DEFAULT 0",
        "task_games": "INTEGER DEFAULT 0",
        "task_eggs": "INTEGER DEFAULT 0",
        "boss_damage": "INTEGER DEFAULT 0"
    }

    for column, definition in required_columns.items():
        if column not in columns:
            cur.execute(
                f"ALTER TABLE players ADD COLUMN {column} {definition}"
            )

    conn.commit()
    conn.close()


# =========================================================
# PLAYER
# =========================================================

def ensure_player(user_id, username=""):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM players WHERE user_id = ?",
        (user_id,)
    )

    player = cur.fetchone()

    if player is None:
        cur.execute("""
            INSERT INTO players (
                user_id,
                username
            )
            VALUES (?, ?)
        """, (user_id, username))
    else:
        cur.execute("""
            UPDATE players
            SET username = ?
            WHERE user_id = ?
        """, (username, user_id))

    conn.commit()
    conn.close()


def get_player(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    conn.close()

    if result is None:
        return None

    return dict(result)


# =========================================================
# BALANCE
# =========================================================

def get_balance(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT tap_coins, egg_coins
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()
    conn.close()

    if result is None:
        return 0, 0

    return result["tap_coins"], result["egg_coins"]


def add_tap_coins(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET tap_coins = tap_coins + ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


def remove_tap_coins(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET tap_coins = tap_coins - ?
        WHERE user_id = ?
        AND tap_coins >= ?
    """, (amount, user_id, amount))

    success = cur.rowcount > 0

    conn.commit()
    conn.close()

    return success


def add_egg_coins(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET egg_coins = egg_coins + ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


def remove_egg_coins(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET egg_coins = egg_coins - ?
        WHERE user_id = ?
        AND egg_coins >= ?
    """, (amount, user_id, amount))

    success = cur.rowcount > 0

    conn.commit()
    conn.close()

    return success


# =========================================================
# EGGS
# =========================================================

def add_egg(user_id, egg_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO player_eggs (
            user_id,
            egg_id,
            count
        )
        VALUES (?, ?, 1)

        ON CONFLICT(user_id, egg_id)
        DO UPDATE SET count = count + 1
    """, (user_id, egg_id))

    conn.commit()
    conn.close()


def get_player_eggs(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT egg_id, count
        FROM player_eggs
        WHERE user_id = ?
        AND count > 0
        ORDER BY egg_id
    """, (user_id,))

    result = [
        {
            "egg_id": row["egg_id"],
            "count": row["count"]
        }
        for row in cur.fetchall()
    ]

    conn.close()

    return result


def get_egg_count(user_id, egg_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT count
        FROM player_eggs
        WHERE user_id = ?
        AND egg_id = ?
    """, (user_id, egg_id))

    result = cur.fetchone()

    conn.close()

    if result is None:
        return 0

    return result["count"]


def remove_one_egg(user_id, egg_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE player_eggs
        SET count = count - 1
        WHERE user_id = ?
        AND egg_id = ?
        AND count > 0
    """, (user_id, egg_id))

    success = cur.rowcount > 0

    conn.commit()
    conn.close()

    return success


def get_total_eggs(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(count), 0) AS total
        FROM player_eggs
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    conn.close()

    return result["total"]


# =========================================================
# XP / LEVEL
# =========================================================

def get_progress(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT xp, level
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    conn.close()

    if result is None:
        return 0, 1

    return result["xp"], result["level"]


def add_xp(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT xp, level
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return 0, 1

    xp = result["xp"] + amount
    level = result["level"]

    # Каждые 100 XP = новый уровень
    new_level = (xp // 100) + 1

    if new_level > level:
        level = new_level

    cur.execute("""
        UPDATE players
        SET xp = ?,
            level = ?
        WHERE user_id = ?
    """, (xp, level, user_id))

    conn.commit()
    conn.close()

    return xp, level


# =========================================================
# LOGIN STREAK
# =========================================================

def get_login_info(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT login_streak, last_login
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    conn.close()

    if result is None:
        return 0, ""

    return result["login_streak"], result["last_login"]


def update_login(user_id):
    today = date.today().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT login_streak, last_login
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return {
            "claimed": False,
            "streak": 0,
            "reward": 0
        }

    streak = result["login_streak"] or 0
    last_login = result["last_login"] or ""

    if last_login == today:
        conn.close()

        return {
            "claimed": False,
            "streak": streak,
            "reward": 0
        }

    if last_login:
        try:
            old_date = date.fromisoformat(last_login)
            today_date = date.fromisoformat(today)

            difference = (today_date - old_date).days

            if difference == 1:
                streak += 1
            else:
                streak = 1

        except Exception:
            streak = 1
    else:
        streak = 1

    # Награда за вход
    reward = 5 + min(streak, 7) * 2

    cur.execute("""
        UPDATE players
        SET login_streak = ?,
            last_login = ?
        WHERE user_id = ?
    """, (streak, today, user_id))

    conn.commit()
    conn.close()

    return {
        "claimed": True,
        "streak": streak,
        "reward": reward
    }


# =========================================================
# DAILY BONUS
# =========================================================

def get_daily_bonus_date(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT daily_bonus_date
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    conn.close()

    if result is None:
        return ""

    return result["daily_bonus_date"] or ""


def set_daily_bonus_date(user_id):
    today = date.today().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET daily_bonus_date = ?
        WHERE user_id = ?
    """, (today, user_id))

    conn.commit()
    conn.close()


# =========================================================
# DAILY TASKS
# =========================================================

def get_daily_tasks(user_id):
    today = date.today().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            task_date,
            task_taps,
            task_games,
            task_eggs
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return 0, 0, 0

    if result["task_date"] != today:
        cur.execute("""
            UPDATE players
            SET task_date = ?,
                task_taps = 0,
                task_games = 0,
                task_eggs = 0
            WHERE user_id = ?
        """, (today, user_id))

        conn.commit()

        taps = 0
        games = 0
        eggs = 0
    else:
        taps = result["task_taps"]
        games = result["task_games"]
        eggs = result["task_eggs"]

    conn.close()

    return taps, games, eggs


def add_task_tap(user_id, amount=1):
    get_daily_tasks(user_id)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET task_taps = task_taps + ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


def add_task_game(user_id, amount=1):
    get_daily_tasks(user_id)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET task_games = task_games + ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


def add_task_egg(user_id, amount=1):
    get_daily_tasks(user_id)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET task_eggs = task_eggs + ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


def has_daily_task_claim(user_id, task_id):
    today = date.today().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 1
        FROM daily_task_claims
        WHERE user_id = ?
        AND task_date = ?
        AND task_id = ?
    """, (user_id, today, task_id))

    result = cur.fetchone()

    conn.close()

    return result is not None


def add_daily_task_claim(user_id, task_id):
    today = date.today().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO daily_task_claims (
                user_id,
                task_date,
                task_id
            )
            VALUES (?, ?, ?)
        """, (user_id, today, task_id))

        success = True

    except sqlite3.IntegrityError:
        success = False

    conn.commit()
    conn.close()

    return success


# =========================================================
# ACHIEVEMENTS
# =========================================================

def has_achievement(user_id, achievement_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 1
        FROM achievements
        WHERE user_id = ?
        AND achievement_id = ?
    """, (user_id, achievement_id))

    result = cur.fetchone()

    conn.close()

    return result is not None


def add_achievement(user_id, achievement_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO achievements (
            user_id,
            achievement_id
        )
        VALUES (?, ?)
    """, (user_id, achievement_id))

    conn.commit()
    conn.close()


def get_achievements(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT achievement_id
        FROM achievements
        WHERE user_id = ?
        ORDER BY achievement_id
    """, (user_id,))

    result = [
        row["achievement_id"]
        for row in cur.fetchall()
    ]

    conn.close()

    return result


# =========================================================
# ITEMS
# =========================================================

def add_item(user_id, item_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO player_items (
            user_id,
            item_id,
            count
        )
        VALUES (?, ?, 1)

        ON CONFLICT(user_id, item_id)
        DO UPDATE SET count = count + 1
    """, (user_id, item_id))

    conn.commit()
    conn.close()


def get_item_count(user_id, item_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT count
        FROM player_items
        WHERE user_id = ?
        AND item_id = ?
    """, (user_id, item_id))

    result = cur.fetchone()

    conn.close()

    if result is None:
        return 0

    return result["count"]


def get_items(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT item_id, count
        FROM player_items
        WHERE user_id = ?
        AND count > 0
        ORDER BY item_id
    """, (user_id,))

    result = [
        {
            "item_id": row["item_id"],
            "count": row["count"]
        }
        for row in cur.fetchall()
    ]

    conn.close()

    return result


def remove_item(user_id, item_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE player_items
        SET count = count - 1
        WHERE user_id = ?
        AND item_id = ?
        AND count > 0
    """, (user_id, item_id))

    success = cur.rowcount > 0

    conn.commit()
    conn.close()

    return success


# =========================================================
# BOSS
# =========================================================

def get_boss_damage(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT boss_damage
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    conn.close()

    if result is None:
        return 0

    return result["boss_damage"]


def add_boss_damage(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET boss_damage = boss_damage + ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()


# =========================================================
# ADMIN
# =========================================================

def get_all_players():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM players
        ORDER BY egg_coins DESC
    """)

    result = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return result


def block_player(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET blocked = 1
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


def unblock_player(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET blocked = 0
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


def is_blocked(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT blocked
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    conn.close()

    if result is None:
        return False

    return bool(result["blocked"])


# =========================================================
# LEADERBOARD
# =========================================================

def get_top_players(limit=10):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            user_id,
            username,
            tap_coins,
            egg_coins,
            level,
            xp
        FROM players
        WHERE blocked = 0
        ORDER BY egg_coins DESC, xp DESC
        LIMIT ?
    """, (limit,))

    result = [
        dict(row)
        for row in cur.fetchall()
    ]

    conn.close()

    return result
