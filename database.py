import sqlite3
import os
from datetime import date


# ============================================================
# НАСТРОЙКИ
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "players.db")


# ============================================================
# ПОДКЛЮЧЕНИЕ
# ============================================================

def connect():
    return sqlite3.connect(DATABASE_NAME)


# ============================================================
# СОЗДАНИЕ БАЗЫ
# ============================================================

def init_database():

    connection = connect()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # ИГРОКИ
    # --------------------------------------------------------

    cursor.execute("""
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

    # --------------------------------------------------------
    # ЯЙЦА
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_eggs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            egg_id INTEGER
        )
    """)

    # --------------------------------------------------------
    # ПРЕДМЕТЫ
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS player_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            item_id INTEGER
        )
    """)

    # --------------------------------------------------------
    # ДОСТИЖЕНИЯ
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            user_id INTEGER,
            achievement_id INTEGER,
            PRIMARY KEY (user_id, achievement_id)
        )
    """)

    # --------------------------------------------------------
    # ПРОВЕРКА СТАРОЙ БАЗЫ
    # --------------------------------------------------------

    cursor.execute("PRAGMA table_info(players)")

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    new_columns = {
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

    for column_name, column_type in new_columns.items():

        if column_name not in columns:

            cursor.execute(
                f"""
                ALTER TABLE players
                ADD COLUMN {column_name} {column_type}
                """
            )

    connection.commit()
    connection.close()


# ============================================================
# ИГРОК
# ============================================================

def create_player(user_id, username=""):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO players
        (
            user_id,
            tap_coins,
            egg_coins,
            username,
            blocked,
            xp,
            level,
            login_streak,
            last_login,
            daily_bonus_date,
            task_date,
            task_taps,
            task_games,
            task_eggs,
            boss_damage
        )
        VALUES (?, 0, 0, ?, 0, 0, 1, 0, '', '', '', 0, 0, 0, 0)
        """,
        (user_id, username)
    )

    if username:

        cursor.execute(
            """
            UPDATE players
            SET username = ?
            WHERE user_id = ?
            """,
            (username, user_id)
        )

    connection.commit()
    connection.close()


def ensure_player(user_id, username=""):

    create_player(
        user_id,
        username
    )


def update_username(user_id, username):

    if not username:
        return

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET username = ?
        WHERE user_id = ?
        """,
        (username, user_id)
    )

    connection.commit()
    connection.close()


# ============================================================
# БАЛАНС
# ============================================================

def get_balance(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT tap_coins, egg_coins
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:

        create_player(user_id)

        return 0, 0

    return result[0], result[1]


def add_tap_coins(user_id, amount):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET tap_coins = tap_coins + ?
        WHERE user_id = ?
        """,
        (amount, user_id)
    )

    connection.commit()
    connection.close()


def remove_tap_coins(user_id, amount):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET tap_coins = tap_coins - ?
        WHERE user_id = ?
        AND tap_coins >= ?
        """,
        (amount, user_id, amount)
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed > 0


def add_egg_coins(user_id, amount):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET egg_coins = egg_coins + ?
        WHERE user_id = ?
        """,
        (amount, user_id)
    )

    connection.commit()
    connection.close()


def remove_egg_coins(user_id, amount):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET egg_coins = egg_coins - ?
        WHERE user_id = ?
        AND egg_coins >= ?
        """,
        (amount, user_id, amount)
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed > 0


# ============================================================
# ЯЙЦА
# ============================================================

def add_egg(user_id, egg_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO player_eggs
        (user_id, egg_id)
        VALUES (?, ?)
        """,
        (user_id, egg_id)
    )

    connection.commit()
    connection.close()


def get_player_eggs(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT egg_id
        FROM player_eggs
        WHERE user_id = ?
        """,
        (user_id,)
    )

    eggs = cursor.fetchall()

    connection.close()

    return [
        egg[0]
        for egg in eggs
    ]


def remove_one_egg(user_id, egg_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM player_eggs
        WHERE user_id = ?
        AND egg_id = ?
        LIMIT 1
        """,
        (user_id, egg_id)
    )

    result = cursor.fetchone()

    if result is None:

        connection.close()

        return False

    egg_database_id = result[0]

    cursor.execute(
        """
        DELETE FROM player_eggs
        WHERE id = ?
        """,
        (egg_database_id,)
    )

    connection.commit()
    connection.close()

    return True


def get_egg_count(user_id, egg_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM player_eggs
        WHERE user_id = ?
        AND egg_id = ?
        """,
        (user_id, egg_id)
    )

    result = cursor.fetchone()

    connection.close()

    return result[0]


# ============================================================
# XP / УРОВЕНЬ
# ============================================================

def get_progress(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT xp, level
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:

        create_player(user_id)

        return 0, 1

    return result[0], result[1]


def add_xp(user_id, amount):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET xp = xp + ?
        WHERE user_id = ?
        """,
        (amount, user_id)
    )

    cursor.execute(
        """
        SELECT xp, level
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    if result:

        xp = result[0]
        level = result[1]

        required = level * 100

        while xp >= required:

            xp -= required
            level += 1

            required = level * 100

        cursor.execute(
            """
            UPDATE players
            SET xp = ?, level = ?
            WHERE user_id = ?
            """,
            (xp, level, user_id)
        )

    connection.commit()
    connection.close()


# ============================================================
# СЕРИЯ ВХОДОВ
# ============================================================

def get_login_info(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT login_streak, last_login
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return 0, ""

    return result[0], result[1]


def update_login(user_id):

    today = date.today()

    today_string = today.isoformat()

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT login_streak, last_login
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    if result is None:

        connection.close()

        create_player(user_id)

        return 1

    streak = result[0]
    last_login = result[1]

    if last_login == today_string:

        connection.close()

        return streak

    if last_login:

        try:

            previous = date.fromisoformat(
                last_login
            )

            difference = (
                today - previous
            ).days

        except ValueError:

            difference = 999

    else:

        difference = 999

    if difference == 1:

        streak += 1

    else:

        streak = 1

    cursor.execute(
        """
        UPDATE players
        SET login_streak = ?,
            last_login = ?
        WHERE user_id = ?
        """,
        (
            streak,
            today_string,
            user_id
        )
    )

    connection.commit()
    connection.close()

    return streak


# ============================================================
# ЕЖЕДНЕВНЫЙ БОНУС
# ============================================================

def get_daily_bonus_date(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT daily_bonus_date
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return ""

    return result[0]


def set_daily_bonus_date(user_id):

    today = date.today().isoformat()

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET daily_bonus_date = ?
        WHERE user_id = ?
        """,
        (today, user_id)
    )

    connection.commit()
    connection.close()


# ============================================================
# ЕЖЕДНЕВНЫЕ ЗАДАНИЯ
# ============================================================

def get_daily_tasks(user_id):

    today = date.today().isoformat()

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT task_date, task_taps, task_games, task_eggs
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    if result is None:

        connection.close()

        return 0, 0, 0

    task_date = result[0]

    if task_date != today:

        cursor.execute(
            """
            UPDATE players
            SET task_date = ?,
                task_taps = 0,
                task_games = 0,
                task_eggs = 0
            WHERE user_id = ?
            """,
            (today, user_id)
        )

        connection.commit()

        connection.close()

        return 0, 0, 0

    connection.close()

    return result[1], result[2], result[3]


def add_task_tap(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET task_taps = task_taps + 1
        WHERE user_id = ?
        """,
        (user_id,)
    )

    connection.commit()
    connection.close()


def add_task_game(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET task_games = task_games + 1
        WHERE user_id = ?
        """,
        (user_id,)
    )

    connection.commit()
    connection.close()


def add_task_egg(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET task_eggs = task_eggs + 1
        WHERE user_id = ?
        """,
        (user_id,)
    )

    connection.commit()
    connection.close()


# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================

def has_achievement(user_id, achievement_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT 1
        FROM achievements
        WHERE user_id = ?
        AND achievement_id = ?
        """,
        (user_id, achievement_id)
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


def add_achievement(user_id, achievement_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO achievements
        (user_id, achievement_id)
        VALUES (?, ?)
        """,
        (user_id, achievement_id)
    )

    connection.commit()
    connection.close()


def get_achievements(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT achievement_id
        FROM achievements
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in result
    ]


# ============================================================
# ПРЕДМЕТЫ
# ============================================================

def add_item(user_id, item_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO player_items
        (user_id, item_id)
        VALUES (?, ?)
        """,
        (user_id, item_id)
    )

    connection.commit()
    connection.close()


def get_item_count(user_id, item_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM player_items
        WHERE user_id = ?
        AND item_id = ?
        """,
        (user_id, item_id)
    )

    result = cursor.fetchone()

    connection.close()

    return result[0]


def remove_item(user_id, item_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM player_items
        WHERE user_id = ?
        AND item_id = ?
        LIMIT 1
        """,
        (user_id, item_id)
    )

    result = cursor.fetchone()

    if result is None:

        connection.close()

        return False

    cursor.execute(
        """
        DELETE FROM player_items
        WHERE id = ?
        """,
        (result[0],)
    )

    connection.commit()
    connection.close()

    return True


# ============================================================
# БОСС
# ============================================================

def get_boss_damage(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT boss_damage
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return 0

    return result[0]


def add_boss_damage(user_id, amount):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET boss_damage = boss_damage + ?
        WHERE user_id = ?
        """,
        (amount, user_id)
    )

    connection.commit()
    connection.close()


# ============================================================
# ПАНЕЛЬ УПРАВЛЕНИЯ
# ============================================================

def get_all_players():

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id, username, blocked
        FROM players
        ORDER BY user_id
        """
    )

    players = cursor.fetchall()

    connection.close()

    return players


def get_player(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            user_id,
            username,
            blocked,
            tap_coins,
            egg_coins,
            xp,
            level,
            login_streak
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    player = cursor.fetchone()

    connection.close()

    return player


def block_player(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET blocked = 1
        WHERE user_id = ?
        """,
        (user_id,)
    )

    connection.commit()
    connection.close()


def unblock_player(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE players
        SET blocked = 0
        WHERE user_id = ?
        """,
        (user_id,)
    )

    connection.commit()
    connection.close()


def is_blocked(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT blocked
        FROM players
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return False

    return result[0] == 1


# ============================================================
# ЛИДЕРЫ
# ============================================================

def get_top_players(limit=10):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id, username, egg_coins, tap_coins, level
        FROM players
        ORDER BY egg_coins DESC
        LIMIT ?
        """,
        (limit,)
    )

    result = cursor.fetchall()

    connection.close()

    return result


# ============================================================
# КОЛИЧЕСТВО ЯИЦ
# ============================================================

def get_total_eggs(user_id):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM player_eggs
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result[0]


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    init_database()

    print("✅ База данных готова.")
    print(
        f"📁 {DATABASE_NAME}"
    )