import sqlite3
from pathlib import Path
from datetime import date


# ============================================================
# НАСТРОЙКИ БАЗЫ
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "players.db"


# ============================================================
# ПОДКЛЮЧЕНИЕ
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ
# ============================================================

def init_database():
    conn = get_connection()
    cur = conn.cursor()

    # ========================================================
    # PLAYERS
    # ========================================================

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

    # ========================================================
    # PLAYER EGGS
    #
    # Каждое яйцо хранится отдельной строкой.
    # count здесь НЕ используется.
    # ========================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_eggs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            egg_id INTEGER NOT NULL
        )
    """)

    # ========================================================
    # PLAYER ITEMS
    # ========================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL
        )
    """)

    # ========================================================
    # ACHIEVEMENTS
    # ========================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id INTEGER NOT NULL
        )
    """)

    # ========================================================
    # DAILY TASK CLAIMS
    # ========================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_task_claims (
            user_id INTEGER NOT NULL,
            task_date TEXT NOT NULL,
            task_id TEXT NOT NULL,
            PRIMARY KEY (user_id, task_date, task_id)
        )
    """)

    # ========================================================
    # ПРОВЕРКА КОЛОНОК PLAYERS
    # ========================================================

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


# ============================================================
# СОЗДАНИЕ ИГРОКА
# ============================================================

def create_player(user_id, username=""):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO players (
            user_id,
            username
        )
        VALUES (?, ?)
    """, (user_id, username))

    if username:
        cur.execute("""
            UPDATE players
            SET username = ?
            WHERE user_id = ?
        """, (username, user_id))

    conn.commit()
    conn.close()


# ============================================================
# ENSURE PLAYER
# ============================================================

def ensure_player(user_id, username=""):
    """
    Создаёт игрока, если его ещё нет.
    Если игрок уже есть — обновляет username.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:

        cur.execute("""
            INSERT INTO players (
                user_id,
                username
            )
            VALUES (?, ?)
        """, (user_id, username))

    elif username:

        cur.execute("""
            UPDATE players
            SET username = ?
            WHERE user_id = ?
        """, (username, user_id))

    conn.commit()
    conn.close()


# ============================================================
# ПОЛУЧЕНИЕ ИГРОКА
# ============================================================

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


# ============================================================
# USERNAME
# ============================================================

def update_username(user_id, username):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET username = ?
        WHERE user_id = ?
    """, (username, user_id))

    conn.commit()
    conn.close()


# ============================================================
# БАЛАНС
# ============================================================

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
        return {
            "tap_coins": 0,
            "egg_coins": 0
        }

    return {
        "tap_coins": result["tap_coins"],
        "egg_coins": result["egg_coins"]
    }


# ============================================================
# TAP COINS
# ============================================================

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
        SELECT tap_coins
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return False

    if result["tap_coins"] < amount:
        conn.close()
        return False

    cur.execute("""
        UPDATE players
        SET tap_coins = tap_coins - ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()

    return True


# ============================================================
# EGG COINS
# ============================================================

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
        SELECT egg_coins
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return False

    if result["egg_coins"] < amount:
        conn.close()
        return False

    cur.execute("""
        UPDATE players
        SET egg_coins = egg_coins - ?
        WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()
    conn.close()

    return True


# ============================================================
# ЯЙЦА
# ============================================================

def add_egg(user_id, egg_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO player_eggs (
            user_id,
            egg_id
        )
        VALUES (?, ?)
    """, (user_id, egg_id))

    conn.commit()
    conn.close()


def get_player_eggs(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT egg_id
        FROM player_eggs
        WHERE user_id = ?
        ORDER BY id ASC
    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    return [row["egg_id"] for row in rows]


def get_egg_count(user_id, egg_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM player_eggs
        WHERE user_id = ?
        AND egg_id = ?
    """, (user_id, egg_id))

    result = cur.fetchone()

    conn.close()

    return result[0]


def remove_one_egg(user_id, egg_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM player_eggs
        WHERE user_id = ?
        AND egg_id = ?
        LIMIT 1
    """, (user_id, egg_id))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return False

    cur.execute("""
        DELETE FROM player_eggs
        WHERE id = ?
    """, (result["id"],))

    conn.commit()
    conn.close()

    return True


def get_total_eggs(user_id):
    """
    Возвращает общее количество яиц игрока.

    Используем COUNT(*), потому что каждое яйцо
    хранится отдельной строкой.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM player_eggs
        WHERE user_id = ?
    """, (user_id,))

    total = cur.fetchone()[0]

    conn.close()

    return total


# ============================================================
# XP / LEVEL
# ============================================================

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
        return {
            "xp": 0,
            "level": 1
        }

    return {
        "xp": result["xp"],
        "level": result["level"]
    }


def add_xp(user_id, amount):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT xp
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:
        conn.close()

        return {
            "xp": 0,
            "level": 1
        }

    new_xp = result["xp"] + amount

    new_level = (new_xp // 100) + 1

    cur.execute("""
        UPDATE players
        SET xp = ?,
            level = ?
        WHERE user_id = ?
    """, (new_xp, new_level, user_id))

    conn.commit()
    conn.close()

    return {
        "xp": new_xp,
        "level": new_level
    }


# ============================================================
# DAILY LOGIN
# ============================================================

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
        return {
            "streak": 0,
            "last_login": ""
        }

    return {
        "streak": result["login_streak"],
        "last_login": result["last_login"]
    }


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

        ensure_player(user_id)

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE players
            SET login_streak = ?,
                last_login = ?
            WHERE user_id = ?
        """, (1, today, user_id))

        conn.commit()
        conn.close()

        return {
            "claimed": True,
            "streak": 1,
            "reward": 0
        }

    last_login = result["last_login"]
    streak = result["login_streak"]

    if last_login == today:
        conn.close()

        return {
            "claimed": False,
            "streak": streak,
            "reward": 0
        }

    if last_login:
        try:
            last_date = date.fromisoformat(last_login)
            today_date = date.fromisoformat(today)

            difference = (today_date - last_date).days

            if difference == 1:
                streak += 1
            else:
                streak = 1

        except Exception:
            streak = 1

    else:
        streak = 1

    reward = 5 * streak

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


# ============================================================
# DAILY BONUS
# ============================================================

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

    return result["daily_bonus_date"]


def set_daily_bonus_date(user_id, value):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE players
        SET daily_bonus_date = ?
        WHERE user_id = ?
    """, (value, user_id))

    conn.commit()
    conn.close()


# ============================================================
# DAILY TASKS
# ============================================================

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
        return (0, 0, 0)

    if result["task_date"] != today:

        cur.execute("""
            UPDATE players
            SET
                task_date = ?,
                task_taps = 0,
                task_games = 0,
                task_eggs = 0
            WHERE user_id = ?
        """, (today, user_id))

        conn.commit()
        conn.close()

        return (0, 0, 0)

    taps = result["task_taps"]
    games = result["task_games"]
    eggs = result["task_eggs"]

    conn.close()

    return (
        taps,
        games,
        eggs
    )


def add_task_tap(user_id, amount=1):
    today = date.today().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT task_date
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return

    if result["task_date"] != today:

        cur.execute("""
            UPDATE players
            SET
                task_date = ?,
                task_taps = ?,
                task_games = 0,
                task_eggs = 0
            WHERE user_id = ?
        """, (today, amount, user_id))

    else:

        cur.execute("""
            UPDATE players
            SET task_taps = task_taps + ?
            WHERE user_id = ?
        """, (amount, user_id))

    conn.commit()
    conn.close()


def add_task_game(user_id, amount=1):
    today = date.today().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT task_date
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return

    if result["task_date"] != today:

        cur.execute("""
            UPDATE players
            SET
                task_date = ?,
                task_taps = 0,
                task_games = ?,
                task_eggs = 0
            WHERE user_id = ?
        """, (today, amount, user_id))

    else:

        cur.execute("""
            UPDATE players
            SET task_games = task_games + ?
            WHERE user_id = ?
        """, (amount, user_id))

    conn.commit()
    conn.close()


def add_task_egg(user_id, amount=1):
    today = date.today().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT task_date
        FROM players
        WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return

    if result["task_date"] != today:

        cur.execute("""
            UPDATE players
            SET
                task_date = ?,
                task_taps = 0,
                task_games = 0,
                task_eggs = ?
            WHERE user_id = ?
        """, (today, amount, user_id))

    else:

        cur.execute("""
            UPDATE players
            SET task_eggs = task_eggs + ?
            WHERE user_id = ?
        """, (amount, user_id))

    conn.commit()
    conn.close()


# ============================================================
# DAILY TASK CLAIMS
# ============================================================

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
    """, (
        user_id,
        today,
        str(task_id)
    ))

    result = cur.fetchone()

    conn.close()

    return result is not None


def add_daily_task_claim(user_id, task_id):
    today = date.today().isoformat()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO daily_task_claims (
            user_id,
            task_date,
            task_id
        )
        VALUES (?, ?, ?)
    """, (
        user_id,
        today,
        str(task_id)
    ))

    conn.commit()
    conn.close()


# ============================================================
# ACHIEVEMENTS
# ============================================================

def has_achievement(user_id, achievement_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 1
        FROM achievements
        WHERE user_id = ?
        AND achievement_id = ?
        LIMIT 1
    """, (
        user_id,
        achievement_id
    ))

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
    """, (
        user_id,
        achievement_id
    ))

    conn.commit()
    conn.close()


def get_achievements(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT achievement_id
        FROM achievements
        WHERE user_id = ?
        ORDER BY id ASC
    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    return [
        row["achievement_id"]
        for row in rows
    ]


# ============================================================
# ITEMS
# ============================================================

def add_item(user_id, item_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO player_items (
            user_id,
            item_id
        )
        VALUES (?, ?)
    """, (
        user_id,
        item_id
    ))

    conn.commit()
    conn.close()


def get_item_count(user_id, item_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM player_items
        WHERE user_id = ?
        AND item_id = ?
    """, (
        user_id,
        item_id
    ))

    count = cur.fetchone()[0]

    conn.close()

    return count


def get_items(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            item_id,
            COUNT(*) AS item_count
        FROM player_items
        WHERE user_id = ?
        GROUP BY item_id
    """, (user_id,))

    rows = cur.fetchall()

    conn.close()

    result = {}

    for row in rows:
        result[str(row["item_id"])] = row["item_count"]

    return result


def remove_item(user_id, item_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id
        FROM player_items
        WHERE user_id = ?
        AND item_id = ?
        LIMIT 1
    """, (
        user_id,
        item_id
    ))

    result = cur.fetchone()

    if result is None:
        conn.close()
        return False

    cur.execute("""
        DELETE FROM player_items
        WHERE id = ?
    """, (result["id"],))

    conn.commit()
    conn.close()

    return True


# ============================================================
# BOSS
# ============================================================

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
    """, (
        amount,
        user_id
    ))

    conn.commit()
    conn.close()


# ============================================================
# BLOCK
# ============================================================

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


# ============================================================
# ВСЕ ИГРОКИ
# ============================================================

def get_all_players():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM players
        ORDER BY user_id ASC
    """)

    rows = cur.fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# LEADERBOARD
# ============================================================

def get_top_players(limit=10):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            user_id,
            username,
            tap_coins,
            egg_coins,
            xp,
            level
        FROM players
        WHERE blocked = 0
        ORDER BY
            egg_coins DESC,
            tap_coins DESC
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# ЗАПУСК ИНИЦИАЛИЗАЦИИ
# ============================================================

init_database()
