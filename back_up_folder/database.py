import sqlite3
from pathlib import Path
from datetime import date


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

    # 100 XP = +1 уровень.
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
# BOSS
# =========================================================

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
