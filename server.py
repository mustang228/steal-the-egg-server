import os
import time
import hmac
import hashlib
import json
import random
import sqlite3
from datetime import date
from urllib.parse import parse_qsl

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database


# =========================================================
# SERVER
# =========================================================

app = Flask(
    __name__,
    static_folder=os.path.dirname(os.path.abspath(__file__)),
    static_url_path=''
)

CORS(app, resources={
    r'/api/*': {
        'origins': '*'
    }
})


BOT_TOKEN = os.getenv('BOT_TOKEN', '')
PORT = int(os.getenv('PORT', '8080'))

WITHDRAWAL_BOT = 'https://t.me/stealthegg_vyvod_bot'


# =========================================================
# EGGS
# =========================================================

EGGS = {
    1: ('🥚 Обычное яйцо', 100, '⚪ Обычное'),
    2: ('🥈 Серебряное яйцо', 600, '🟢 Необычное'),
    3: ('🥇 Золотое яйцо', 900, '🔵 Редкое'),
    4: ('💎 Алмазное яйцо', 1400, '🟣 Эпическое'),
    5: ('🔥 Огненное яйцо', 1800, '🟣 Эпическое'),
    6: ('❄️ Ледяное яйцо', 2300, '🟡 Легендарное'),
    7: ('🌌 Космическое яйцо', 3000, '🟡 Легендарное'),
    8: ('👑 Королевское яйцо', 4500, '🔴 Мифическое'),
    9: ('⚡ Молниевое яйцо', 6000, '🔴 Мифическое'),
    10: ('🌑 Тёмное яйцо', 8000, '🔴 Мифическое'),
    11: ('☀️ Солнечное яйцо', 11000, '💠 Божественное'),
    12: ('🪐 Галактическое яйцо', 15000, '💠 Божественное'),
    13: ('🧿 Проклятое яйцо', 22000, '🌈 Секретное'),
    14: ('🪽 Небесное яйцо', 30000, '🌈 Секретное'),
    15: ('👾 Глитч-яйцо', 50000, '🌈 Секретное'),
    16: ('🌋 Магмовое яйцо', 9500, '🟡 Легендарное'),
    17: ('🌊 Океанское яйцо', 7000, '🔴 Мифическое'),
    18: ('🌳 Древнее яйцо', 12500, '💠 Божественное'),
    19: ('👻 Призрачное яйцо', 5500, '🔴 Мифическое'),
    20: ('🩸 Тёмно-красное яйцо', 18000, '💠 Божественное'),
}


# =========================================================
# ITEMS
# =========================================================

ITEMS = {
    1: (
        '⚡ Бустер тапов',
        150,
        '+2 Tap Coins за тап на 10 минут'
    ),

    2: (
        '🥚 Бустер Egg Coins',
        250,
        '+1 Egg Coin к наградам игр на 10 минут'
    ),

    3: (
        '🎁 XP Бустер',
        200,
        'В 2 раза больше XP на 10 минут'
    ),
}


# =========================================================
# ACHIEVEMENTS
# =========================================================

ACH = {
    1: (
        '👆 Первый тап',
        'Сделать первый тап',
        10
    ),

    2: (
        '💰 Богатей',
        'Накопить 1000 Tap Coins',
        25
    ),

    3: (
        '🥚 Коллекционер',
        'Собрать 5 яиц',
        50
    ),

    4: (
        '🥚 Яичный мастер',
        'Собрать 10 разных яиц',
        100
    ),

    5: (
        '🎮 Игрок',
        'Сыграть 10 мини-игр',
        50
    ),

    6: (
        '🔥 Серия',
        'Получить серию 7 дней',
        100
    ),

    7: (
        '⭐ Уровень 10',
        'Достичь 10 уровня',
        150
    ),

    8: (
        '👾 Охотник на боссов',
        'Нанести 100 урона боссу',
        100
    ),
}


# =========================================================
# AVATARS
# =========================================================

AVATARS = [
    '🥚',
    '🐣',
    '🐥',
    '🐔',
    '🦊',
    '🐼',
    '🐸',
    '🐵',
    '😎',
    '🤖',
    '👽',
    '👾',
    '🤑',
    '🔥',
    '⚡',
    '💎',
    '👑',
    '🌌',
    '🌑',
    '🍀'
]


# =========================================================
# GAME MEMORY
# =========================================================

active = {}
guess = {}
math = {}
tic = {}

last_tap = {}
last_game = {}
last_boss = {}
last_steal = {}

boss_hp = 10000


# =========================================================
# DATABASE
# =========================================================

database.init_database()

EXTRA_DB = getattr(
    database,
    'DB_PATH',
    os.path.join(os.path.dirname(__file__), 'players.db')
)


# =========================================================
# CHESTS
# =========================================================

CHESTS = {
    1: ('🪵 Деревянный сундук', 100, 0.8),
    2: ('🥇 Золотой сундук', 350, 1.5),
    3: ('💎 Алмазный сундук', 900, 3.0),
    4: ('🌌 Космический сундук', 2000, 5.0),
    5: ('👑 Королевский сундук', 5000, 8.0),
    6: ('🌑 Тёмный сундук', 10000, 12.0),
    7: ('🐾 Сундук питомца', 2500, 0.0),
}


# =========================================================
# PETS
# =========================================================

PETS = {
    1: (
        '🐹 Яичный хомяк',
        '⚪ Обычное',
        '+5% Egg Coins'
    ),

    2: (
        '🐱 Космо-кот',
        '🟢 Необычное',
        '+8% Egg Coins'
    ),

    3: (
        '🦊 Огненный лис',
        '🔵 Редкое',
        '+10% Egg Coins'
    ),

    4: (
        '🐉 Маленький дракон',
        '🟣 Эпическое',
        '+15% Egg Coins'
    ),

    5: (
        '🦄 Неоновый единорог',
        '🟡 Легендарное',
        '+20% Egg Coins'
    ),

    6: (
        '👑 Королевский дракон',
        '🔴 Мифическое',
        '+30% Egg Coins'
    ),

    7: (
        '👾 Глитч-питомец',
        '💠 Божественное',
        '+40% Egg Coins'
    ),
}


PET_BONUS = {
    '⚪ Обычное': 0.05,
    '🟢 Необычное': 0.08,
    '🔵 Редкое': 0.10,
    '🟣 Эпическое': 0.15,
    '🟡 Легендарное': 0.20,
    '🔴 Мифическое': 0.30,
    '💠 Божественное': 0.40,
}


# =========================================================
# PASS
# =========================================================

PASS_MAX = 30
PASS_XP = 100

BOSS_MAX_HP = 100000


# =========================================================
# EXTRA DATABASE CONNECTION
# =========================================================

def extra_conn():
    conn = sqlite3.connect(
        EXTRA_DB,
        timeout=30
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# EXTRA DATABASE TABLES
# =========================================================

def init_extra():

    conn = extra_conn()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS player_pets(
            user_id INTEGER,
            pet_id INTEGER,
            active INTEGER DEFAULT 0,
            PRIMARY KEY(user_id, pet_id)
        );

        CREATE TABLE IF NOT EXISTS market_listings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            egg_id INTEGER,
            price INTEGER,
            created_at INTEGER,
            sold INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS chest_opens(
            user_id INTEGER,
            chest_id INTEGER,
            count INTEGER DEFAULT 0,
            PRIMARY KEY(user_id, chest_id)
        );

        CREATE TABLE IF NOT EXISTS boss_event(
            id INTEGER PRIMARY KEY CHECK(id=1),
            hp INTEGER,
            max_hp INTEGER,
            started_at INTEGER,
            ends_at INTEGER,
            reward_claimed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS boss_contributions(
            user_id INTEGER PRIMARY KEY,
            damage INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS egg_pass(
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS egg_pass_claims(
            user_id INTEGER,
            level INTEGER,
            track TEXT,
            PRIMARY KEY(user_id, level, track)
        );

        CREATE TABLE IF NOT EXISTS steal_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attacker_id INTEGER,
            defender_id INTEGER,
            egg_id INTEGER,
            success INTEGER,
            created_at INTEGER
        );

        CREATE TABLE IF NOT EXISTS egg_protection(
            user_id INTEGER PRIMARY KEY,
            until_ts INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS extra_daily(
            user_id INTEGER PRIMARY KEY,
            task_date TEXT,
            task_id TEXT,
            target INTEGER,
            progress INTEGER DEFAULT 0,
            reward INTEGER DEFAULT 0,
            claimed INTEGER DEFAULT 0
        );
    """)

    conn.commit()
    conn.close()


init_extra()


# =========================================================
# PET BONUS
# =========================================================

def pet_bonus(uid):

    conn = extra_conn()

    row = conn.execute(
        '''
        SELECT pet_id
        FROM player_pets
        WHERE user_id=? AND active=1
        ''',
        (uid,)
    ).fetchone()

    conn.close()

    if not row:
        return 0

    pet_id = int(row['pet_id'])

    if pet_id not in PETS:
        return 0

    rarity = PETS[pet_id][1]

    return PET_BONUS.get(rarity, 0)


# =========================================================
# EGG PASS XP
# =========================================================

def add_pass_xp(uid, amount):

    conn = extra_conn()

    row = conn.execute(
        'SELECT xp FROM egg_pass WHERE user_id=?',
        (uid,)
    ).fetchone()

    old_xp = int(row['xp']) if row else 0

    xp = old_xp + int(amount)

    level = min(
        PASS_MAX,
        xp // PASS_XP
    )

    conn.execute(
        '''
        INSERT INTO egg_pass(user_id, xp, level)
        VALUES(?,?,?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            xp=excluded.xp,
            level=excluded.level
        ''',
        (
            uid,
            xp,
            level
        )
    )

    conn.commit()
    conn.close()


# =========================================================
# RANDOM EGG FROM CHEST
# =========================================================

def chest_egg():

    ids = list(EGGS)

    weights = [
        52,
        20,
        10,
        5,
        4,
        3,
        2,
        1.3,
        0.8,
        0.5,
        0.2,
        0.1,
        0.05,
        0.03,
        0.02,
        0.3,
        0.25,
        0.15,
        0.1,
        0.1
    ]

    return random.choices(
        ids,
        weights=weights,
        k=1
    )[0]


# =========================================================
# EXTRA DAILY
# =========================================================

def new_daily(uid):

    today = date.today().isoformat()

    conn = extra_conn()

    row = conn.execute(
        'SELECT * FROM extra_daily WHERE user_id=?',
        (uid,)
    ).fetchone()

    if not row or row['task_date'] != today:

        task = random.choice([
            (
                'tap',
                '👆 Сделать 100 тапов',
                100,
                25
            ),

            (
                'game',
                '🎮 Сыграть 3 мини-игры',
                3,
                35
            ),

            (
                'chest',
                '🎁 Открыть 1 сундук',
                1,
                45
            ),

            (
                'boss',
                '👹 Нанести 100 урона боссу',
                100,
                50
            ),

            (
                'egg',
                '🥚 Получить 1 яйцо',
                1,
                40
            ),

            (
                'market',
                '🏪 Купить 1 яйцо на рынке',
                1,
                50
            )
        ])

        conn.execute(
            '''
            INSERT INTO extra_daily(
                user_id,
                task_date,
                task_id,
                target,
                progress,
                reward,
                claimed
            )
            VALUES(?,?,?,?,0,?,0)

            ON CONFLICT(user_id)
            DO UPDATE SET
                task_date=excluded.task_date,
                task_id=excluded.task_id,
                target=excluded.target,
                progress=0,
                reward=excluded.reward,
                claimed=0
            ''',
            (
                uid,
                today,
                task[0],
                task[2],
                task[3]
            )
        )

        conn.commit()

        row = conn.execute(
            'SELECT * FROM extra_daily WHERE user_id=?',
            (uid,)
        ).fetchone()

    conn.close()

    return dict(row)


# =========================================================
# DAILY PROGRESS
# =========================================================

def progress_daily(uid, kind, amount=1):

    try:

        task = new_daily(uid)

        if (
            task['task_id'] == kind
            and not task['claimed']
        ):

            conn = extra_conn()

            conn.execute(
                '''
                UPDATE extra_daily
                SET progress=MIN(target, progress+?)
                WHERE user_id=?
                ''',
                (
                    int(amount),
                    uid
                )
            )

            conn.commit()
            conn.close()

    except Exception:
        pass


# =========================================================
# TELEGRAM AUTH
# =========================================================

def user():

    raw = request.headers.get(
        'X-Telegram-Init-Data',
        ''
    )

    if not raw:
        return None, 'Открой Mini App через Telegram.'

    if not BOT_TOKEN:
        return None, 'На сервере не задан BOT_TOKEN.'

    params = dict(
        parse_qsl(
            raw,
            keep_blank_values=True
        )
    )

    received_hash = params.pop(
        'hash',
        None
    )

    if not received_hash:
        return None, 'Нет hash Telegram.'

    check_string = '\n'.join(
        f'{key}={params[key]}'
        for key in sorted(params)
    )

    secret_key = hmac.new(
        b'WebAppData',
        BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(
        calculated_hash,
        received_hash
    ):
        return None, 'Неверная подпись Telegram.'

    try:

        if (
            time.time()
            - int(params.get('auth_date', '0'))
            > 86400
        ):
            return None, 'Сессия Telegram устарела.'

        telegram_user = json.loads(
            params['user']
        )

    except Exception:
        return None, 'Некорректные данные Telegram.'

    uid = int(
        telegram_user['id']
    )

    database.ensure_player(
        uid,
        telegram_user.get('username', '') or ''
    )

    if database.is_blocked(uid):
        return None, 'Твой аккаунт заблокирован.'

    return telegram_user, None


# =========================================================
# AUTH WRAPPER
# =========================================================

def auth():

    u, error = user()

    if error:
        return (
            None,
            (
                jsonify(
                    ok=False,
                    error=error
                ),
                401
            )
        )

    return u, None


# =========================================================
# ITEMS
# =========================================================

def expiry(uid, item_id):

    return active.get(
        (uid, item_id),
        0
    )


def has(uid, item_id):

    return expiry(
        uid,
        item_id
    ) > time.time()


# =========================================================
# XP
# =========================================================

def add_xp(uid, amount):

    multiplier = 2 if has(uid, 3) else 1

    database.add_xp(
        uid,
        amount * multiplier
    )


# =========================================================
# GAME COINS
# =========================================================

def add_game_coins(uid, amount):

    amount += 1 if has(uid, 2) else 0

    bonus = pet_bonus(uid)

    if bonus > 0:
        amount = int(
            amount * (1 + bonus)
        )

    database.add_egg_coins(
        uid,
        amount
    )


# =========================================================
# EGG COUNTS
# =========================================================

def egg_counts(uid):

    eggs = database.get_player_eggs(uid)

    return {
        str(i): eggs.count(i)
        for i in EGGS
    }


# =========================================================
# PLAYER SNAPSHOT
# =========================================================

def snap(uid):

    tap, egg = database.get_balance(uid)

    current_xp, level = database.get_progress(uid)

    streak, last = database.get_login_info(uid)

    tasks = database.get_daily_tasks(uid)

    owned = egg_counts(uid)

    xp_required = max(
        100,
        level * 100
    )

    return {
        'tap_coins': int(tap),

        'egg_coins': int(egg),

        'xp': int(current_xp),

        'level': int(level),

        'xp_required': int(xp_required),

        'streak': int(streak),

        'last_login': last,

        'eggs_total': sum(
            owned.values()
        ),

        'eggs': owned,

        'avatar': database.get_avatar(uid),

        'avatars': AVATARS,

        'achievements': database.get_achievements(uid),

        'active_items': {
            str(i): max(
                0,
                int(
                    expiry(uid, i)
                    - time.time()
                )
            )
            for i in ITEMS
            if has(uid, i)
        },

        'tasks': {
            'taps': int(tasks[0]),
            'games': int(tasks[1]),
            'eggs': int(tasks[2]),

            'tap_claimed':
                database.has_daily_task_claim(
                    uid,
                    'tap'
                ),

            'game_claimed':
                database.has_daily_task_claim(
                    uid,
                    'game'
                ),

            'egg_claimed':
                database.has_daily_task_claim(
                    uid,
                    'egg'
                ),
        },
    }


# =========================================================
# ACHIEVEMENTS CHECK
# =========================================================

def achievements(uid):

    tap, _ = database.get_balance(uid)

    eggs = database.get_player_eggs(uid)

    _, level = database.get_progress(uid)

    streak, _ = database.get_login_info(uid)

    tasks = database.get_daily_tasks(uid)

    checks = {

        1:
            tap >= 1,

        2:
            tap >= 1000,

        3:
            len(eggs) >= 5,

        4:
            len(set(eggs)) >= 10,

        5:
            tasks[1] >= 10,

        6:
            streak >= 7,

        7:
            level >= 10,

        8:
            database.get_boss_damage(uid) >= 100,
    }

    unlocked = []

    for achievement_id, condition in checks.items():

        if (
            condition
            and not database.has_achievement(
                uid,
                achievement_id
            )
        ):

            database.add_achievement(
                uid,
                achievement_id
            )

            database.add_egg_coins(
                uid,
                ACH[achievement_id][2]
            )

            unlocked.append({
                'id': achievement_id,
                'name': ACH[achievement_id][0],
                'reward': ACH[achievement_id][2]
            })

    return unlocked


# =========================================================
# JSON ERROR
# =========================================================

def json_error(message, status=400):

    return jsonify(
        ok=False,
        error=message
    ), status


# =========================================================
# INDEX
# =========================================================

@app.get('/')
def index():

    return jsonify(
        ok=True,
        message='STEAL THE EGG server is running!'
    )


# =========================================================
# INIT
# =========================================================

@app.post('/api/init')
def init():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    streak, last = database.get_login_info(uid)

    today = date.today().isoformat()

    claimed = False
    reward = 0

    if last != today:

        streak = database.update_login(uid)

        reward = min(
            10 + streak * 5,
            100
        )

        database.add_egg_coins(
            uid,
            reward
        )

        add_xp(
            uid,
            10
        )

        claimed = True

    return jsonify(
        ok=True,

        user={
            'id': uid,
            'username': u.get('username', ''),
            'first_name': u.get('first_name', '')
        },

        login={
            'claimed': claimed,
            'streak': streak,
            'reward': reward
        },

        data=snap(uid),

        new_achievements=achievements(uid)
    )


# =========================================================
# STATE
# =========================================================

@app.get('/api/state')
def state():

    u, f = auth()

    if f:
        return f

    return jsonify(
        ok=True,
        data=snap(int(u['id']))
    )


# =========================================================
# TAP
# =========================================================

@app.post('/api/tap')
def tap():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    now = time.time()

    try:
        amount = int(
            (request.json or {}).get(
                'amount',
                1
            )
        )
    except (
        TypeError,
        ValueError
    ):
        amount = 1

    amount = max(
        1,
        min(amount, 40)
    )

    old = [
        t
        for t in last_tap.get(uid, [])
        if now - t < 2
    ]

    if len(old) + amount > 80:

        return json_error(
            'Слишком быстро. Подожди немного.',
            429
        )

    old += [now] * amount

    last_tap[uid] = old

    gain = amount * (
        3 if has(uid, 1) else 1
    )

    database.add_tap_coins(
        uid,
        gain
    )

    progress_daily(
        uid,
        'tap',
        amount
    )

    add_pass_xp(
        uid,
        amount
    )

    database.add_task_tap(
        uid,
        amount
    )

    add_xp(
        uid,
        amount
    )

    return jsonify(
        ok=True,

        gained=gain,

        data=snap(uid),

        new_achievements=achievements(uid)
    )


# =========================================================
# EXCHANGE TAP COINS -> EGG COINS
# =========================================================

@app.post('/api/exchange')
def exchange():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    tap, _ = database.get_balance(uid)

    # 30 Tap Coins = 10 Egg Coins
    count = tap // 30

    if count < 1:

        return json_error(
            'Нужно минимум 30 Tap Coins.'
        )

    spent = count * 30

    received = count * 10

    if not database.remove_tap_coins(
        uid,
        spent
    ):
        return json_error(
            'Не удалось выполнить обмен.'
        )

    database.add_egg_coins(
        uid,
        received
    )

    add_xp(
        uid,
        5
    )

    return jsonify(
        ok=True,
        spent=spent,
        received=received,
        data=snap(uid)
    )


# =========================================================
# GAME COOLDOWN
# =========================================================

def game_ok(uid):

    now = time.time()

    if (
        now - last_game.get(uid, 0)
        < 1
    ):
        return False

    last_game[uid] = now

    return True


# =========================================================
# GUESS GAME START
# =========================================================

@app.post('/api/game/guess/start')
def guess_start():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    if not game_ok(uid):

        return json_error(
            'Подожди немного.',
            429
        )

    guess[uid] = {
        'n': random.randint(1, 20),
        'a': 0
    }

    return jsonify(
        ok=True,
        min=1,
        max=20,
        attempts=10
    )


# =========================================================
# GUESS GAME ANSWER
# =========================================================

@app.post('/api/game/guess/answer')
def guess_answer():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    game = guess.get(uid)

    if not game:

        return json_error(
            'Игра не запущена.'
        )

    try:

        value = int(
            (request.json or {}).get(
                'guess'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Введите число.'
        )

    if not 1 <= value <= 20:

        return json_error(
            'Число от 1 до 20.'
        )

    game['a'] += 1

    attempts = game['a']

    rewards = {
        1: 5,
        2: 4,
        3: 3,
        4: 3,
        5: 2,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        10: 1
    }

    if value == game['n']:

        reward = rewards[attempts]

        add_game_coins(
            uid,
            reward
        )

        database.add_task_game(uid)

        add_xp(
            uid,
            10
        )

        number = game['n']

        guess.pop(
            uid,
            None
        )

        return jsonify(
            ok=True,
            result='win',
            reward=reward,
            number=number,
            attempts=attempts,
            data=snap(uid),
            new_achievements=achievements(uid)
        )

    if attempts >= 10:

        number = game['n']

        guess.pop(
            uid,
            None
        )

        database.add_task_game(uid)

        return jsonify(
            ok=True,
            result='lose',
            reward=0,
            number=number,
            attempts=attempts,
            data=snap(uid),
            new_achievements=achievements(uid)
        )

    return jsonify(
        ok=True,
        result='continue',
        hint=(
            'Больше!'
            if value < game['n']
            else 'Меньше!'
        ),
        attempts=attempts
    )


# =========================================================
# MATH GAME START
# =========================================================

@app.post('/api/game/math/start')
def math_start():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    if not game_ok(uid):

        return json_error(
            'Подожди немного.',
            429
        )

    a = random.randint(
        5,
        30
    )

    b = random.randint(
        2,
        20
    )

    operation = random.choice([
        '+',
        '-',
        '*'
    ])

    if operation == '+':

        answer = a + b

    elif operation == '-':

        answer = a - b

    else:

        answer = a * b

    math[uid] = {
        'a': a,
        'b': b,
        'op': operation,
        'answer': answer
    }

    return jsonify(
        ok=True,
        question=f'{a} {operation} {b} = ?'
    )


# =========================================================
# NEW MATH QUESTION
# =========================================================

def new_math_question(uid):

    a = random.randint(
        5,
        30
    )

    b = random.randint(
        2,
        20
    )

    operation = random.choice([
        '+',
        '-',
        '*'
    ])

    if operation == '+':

        answer = a + b

    elif operation == '-':

        answer = a - b

    else:

        answer = a * b

    math[uid] = {
        'a': a,
        'b': b,
        'op': operation,
        'answer': answer
    }

    return f'{a} {operation} {b} = ?'


# =========================================================
# MATH ANSWER
# =========================================================

@app.post('/api/game/math/answer')
def math_answer():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    game = math.get(uid)

    if not game:

        return json_error(
            'Задание не запущено.'
        )

    try:

        value = int(
            (request.json or {}).get(
                'answer'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Введите число.'
        )

    correct = game['answer']

    database.add_task_game(uid)

    if value == correct:

        math.pop(
            uid,
            None
        )

        # Победа = 4 Egg Coins
        reward = 4

        add_game_coins(
            uid,
            reward
        )

        add_xp(
            uid,
            10
        )

        return jsonify(
            ok=True,
            result='win',
            correct=correct,
            reward=reward,
            data=snap(uid),
            new_achievements=achievements(uid)
        )

    new_question = new_math_question(uid)

    return jsonify(
        ok=True,
        result='wrong',
        correct=correct,
        reward=0,
        question=new_question,
        data=snap(uid),
        new_achievements=achievements(uid)
    )


# =========================================================
# TIC-TAC-TOE WINNER
# =========================================================

def winner(board):

    combinations = (
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),

        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),

        (0, 4, 8),
        (2, 4, 6)
    )

    for a, b, c in combinations:

        if (
            board[a] != ' '
            and board[a]
            == board[b]
            == board[c]
        ):

            return board[a]

    if ' ' not in board:
        return 'draw'

    return None


# =========================================================
# TIC-TAC-TOE START
# =========================================================

@app.post('/api/game/tic/start')
def tic_start():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    if not game_ok(uid):

        return json_error(
            'Подожди немного.',
            429
        )

    tic[uid] = [
        ' '
    ] * 9

    return jsonify(
        ok=True,
        board=tic[uid]
    )


# =========================================================
# TIC-TAC-TOE FINISH
# =========================================================

def finish_tic(
    uid,
    result,
    reward=0,
    xp_amount=0
):

    if reward:

        add_game_coins(
            uid,
            reward
        )

    if xp_amount:

        add_xp(
            uid,
            xp_amount
        )

    database.add_task_game(uid)

    board = tic.pop(
        uid,
        [' '] * 9
    )

    return jsonify(
        ok=True,
        board=board,
        result=result,
        reward=reward,
        data=snap(uid),
        new_achievements=achievements(uid)
    )


# =========================================================
# TIC-TAC-TOE MOVE
# =========================================================

@app.post('/api/game/tic/move')
def tic_move():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    board = tic.get(uid)

    if board is None:

        return json_error(
            'Игра не запущена.'
        )

    try:

        index = int(
            (request.json or {}).get(
                'index'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверная клетка.'
        )

    if index < 0 or index > 8:

        return json_error(
            'Неверная клетка.'
        )

    if board[index] != ' ':

        return json_error(
            'Клетка уже занята.'
        )

    board[index] = 'X'

    result = winner(board)

    if result == 'X':

        return finish_tic(
            uid,
            'win',
            5,
            15
        )

    if result == 'draw':

        return finish_tic(
            uid,
            'draw',
            2,
            10
        )

    empty = [
        position
        for position, value
        in enumerate(board)
        if value == ' '
    ]

    if empty:

        board[
            random.choice(empty)
        ] = 'O'

    result = winner(board)

    if result == 'O':

        return finish_tic(
            uid,
            'lose',
            0,
            0
        )

    if result == 'draw':

        return finish_tic(
            uid,
            'draw',
            2,
            10
        )

    return jsonify(
        ok=True,
        board=board,
        result='continue'
    )


# =========================================================
# EGGS SHOP
# =========================================================

@app.get('/api/eggs')
def eggs():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    owned = egg_counts(uid)

    shop = {
        str(i): {
            'id': i,
            'name': egg[0],
            'price': egg[1],
            'rarity': egg[2]
        }

        for i, egg in EGGS.items()
    }

    return jsonify(
        ok=True,
        shop=shop,
        owned=owned,
        total=sum(
            owned.values()
        )
    )


# =========================================================
# BUY EGG
# =========================================================

@app.post('/api/eggs/buy')
def buy_egg():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    try:

        egg_id = int(
            (request.json or {}).get(
                'egg_id'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверное яйцо.'
        )

    if egg_id not in EGGS:

        return json_error(
            'Такого яйца нет.'
        )

    price = EGGS[egg_id][1]

    if not database.remove_egg_coins(
        uid,
        price
    ):

        return json_error(
            f'Недостаточно Egg Coins. Нужно {price} 🥚.'
        )

    database.add_egg(
        uid,
        egg_id
    )

    progress_daily(
        uid,
        'egg',
        1
    )

    add_pass_xp(
        uid,
        15
    )

    database.add_task_egg(
        uid
    )

    add_xp(
        uid,
        15
    )

    return jsonify(
        ok=True,

        egg={
            'id': egg_id,
            'name': EGGS[egg_id][0]
        },

        data=snap(uid),

        new_achievements=achievements(uid)
    )


# =========================================================
# OPEN EGG
# =========================================================

@app.post('/api/eggs/open')
def open_egg():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    try:

        egg_id = int(
            (request.json or {}).get(
                'egg_id'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверное яйцо.'
        )

    if egg_id not in EGGS:

        return json_error(
            'Такого яйца нет.'
        )

    if not database.remove_one_egg(
        uid,
        egg_id
    ):

        return json_error(
            'У тебя нет этого яйца.'
        )

    reward = 5 + egg_id * 2

    database.add_egg_coins(
        uid,
        reward
    )

    add_xp(
        uid,
        20
    )

    return jsonify(
        ok=True,
        reward=reward,

        egg={
            'id': egg_id,
            'name': EGGS[egg_id][0]
        },

        data=snap(uid),

        new_achievements=achievements(uid)
    )


# =========================================================
# ITEMS LIST
# =========================================================

@app.get('/api/items')
def items():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    return jsonify(
        ok=True,

        items={
            str(i): {
                'id': i,
                'name': item[0],
                'price': item[1],
                'description': item[2],

                'count':
                    database.get_item_count(
                        uid,
                        i
                    ),

                'active_seconds':
                    max(
                        0,
                        int(
                            expiry(uid, i)
                            - time.time()
                        )
                    )
            }

            for i, item in ITEMS.items()
        }
    )


# =========================================================
# BUY ITEM
# =========================================================

@app.post('/api/items/buy')
def buy_item():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    try:

        item_id = int(
            (request.json or {}).get(
                'item_id'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверный предмет.'
        )

    if item_id not in ITEMS:

        return json_error(
            'Такого предмета нет.'
        )

    price = ITEMS[item_id][1]

    if not database.remove_egg_coins(
        uid,
        price
    ):

        return json_error(
            f'Недостаточно Egg Coins. Нужно {price} 🥚.'
        )

    database.add_item(
        uid,
        item_id
    )

    add_xp(
        uid,
        10
    )

    return jsonify(
        ok=True,
        data=snap(uid)
    )


# =========================================================
# ACTIVATE ITEM
# =========================================================

@app.post('/api/items/activate')
def activate_item():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    try:

        item_id = int(
            (request.json or {}).get(
                'item_id'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверный предмет.'
        )

    if item_id not in ITEMS:

        return json_error(
            'Такого предмета нет.'
        )

    if not database.remove_item(
        uid,
        item_id
    ):

        return json_error(
            'У тебя нет этого предмета.'
        )

    active[
        (uid, item_id)
    ] = time.time() + 600

    return jsonify(
        ok=True,
        data=snap(uid)
    )


# =========================================================
# ACHIEVEMENTS
# =========================================================

@app.get('/api/achievements')
def achievement_list():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    unlocked = set(
        database.get_achievements(uid)
    )

    return jsonify(
        ok=True,

        items=[
            {
                'id': i,
                'name': achievement[0],
                'description': achievement[1],
                'reward': achievement[2],
                'unlocked':
                    i in unlocked
            }

            for i, achievement
            in ACH.items()
        ]
    )


# =========================================================
# LEADERBOARD
# =========================================================

@app.get('/api/leaderboard')
def leaderboard():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    players = database.get_top_players(
        10
    )

    for player in players:

        player['avatar'] = database.get_avatar(
            player['user_id']
        )

    return jsonify(
        ok=True,
        players=players,
        my_rank=database.get_player_rank(
            uid
        )
    )


# =========================================================
# SET AVATAR
# =========================================================

@app.post('/api/profile/avatar')
def set_avatar():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    avatar = str(
        (request.json or {}).get(
            'avatar',
            ''
        )
    ).strip()

    if avatar not in AVATARS:

        return json_error(
            'Такой аватар недоступен.'
        )

    database.set_avatar(
        uid,
        avatar
    )

    return jsonify(
        ok=True,
        avatar=avatar,
        data=snap(uid)
    )


# =========================================================
# AVATARS
# =========================================================

@app.get('/api/profile/avatars')
def avatars():

    u, f = auth()

    if f:
        return f

    return jsonify(
        ok=True,
        avatars=AVATARS,
        current=database.get_avatar(
            int(u['id'])
        )
    )


# =========================================================
# DAILY BONUS
# =========================================================

@app.post('/api/daily/bonus')
def bonus():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    today = date.today().isoformat()

    if (
        database.get_daily_bonus_date(uid)
        == today
    ):

        return json_error(
            'Бонус уже получен сегодня.'
        )

    streak, _ = database.get_login_info(
        uid
    )

    reward = min(
        20 + streak * 5,
        100
    )

    database.add_egg_coins(
        uid,
        reward
    )

    database.set_daily_bonus_date(
        uid
    )

    add_xp(
        uid,
        20
    )

    return jsonify(
        ok=True,
        reward=reward,
        data=snap(uid)
    )


# =========================================================
# DAILY TASKS
# =========================================================

@app.get('/api/daily/tasks')
def tasks():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    task = database.get_daily_tasks(
        uid
    )

    return jsonify(
        ok=True,

        tasks=[
            {
                'id': 'tap',
                'title': '👆 Сделать 100 тапов',
                'progress': min(
                    task[0],
                    100
                ),
                'target': 100,
                'reward': 25,
                'claimed':
                    database.has_daily_task_claim(
                        uid,
                        'tap'
                    )
            },

            {
                'id': 'game',
                'title': '🎮 Сыграть 3 игры',
                'progress': min(
                    task[1],
                    3
                ),
                'target': 3,
                'reward': 30,
                'claimed':
                    database.has_daily_task_claim(
                        uid,
                        'game'
                    )
            },

            {
                'id': 'egg',
                'title': '🥚 Купить 1 яйцо',
                'progress': min(
                    task[2],
                    1
                ),
                'target': 1,
                'reward': 40,
                'claimed':
                    database.has_daily_task_claim(
                        uid,
                        'egg'
                    )
            }
        ]
    )


# =========================================================
# CLAIM DAILY TASK
# =========================================================

@app.post('/api/daily/tasks/claim')
def claim():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    task_id = (
        request.json or {}
    ).get('task_id')

    rewards = {
        'tap': 25,
        'game': 30,
        'egg': 40
    }

    targets = {
        'tap': 100,
        'game': 3,
        'egg': 1
    }

    task = database.get_daily_tasks(
        uid
    )

    progress = {
        'tap': task[0],
        'game': task[1],
        'egg': task[2]
    }

    if (
        task_id not in rewards
        or progress[task_id]
        < targets[task_id]
    ):

        return json_error(
            'Задание ещё не выполнено или неверное задание.'
        )

    if not database.add_daily_task_claim(
        uid,
        task_id
    ):

        return json_error(
            'Задание уже получено.'
        )

    database.add_egg_coins(
        uid,
        rewards[task_id]
    )

    add_xp(
        uid,
        15
    )

    return jsonify(
        ok=True,
        reward=rewards[task_id],
        data=snap(uid)
    )


# =========================================================
# WITHDRAWAL
# =========================================================

@app.get('/api/withdrawal')
def withdrawal():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    owned = egg_counts(uid)

    eggs = {
        str(i): {
            'id': i,
            'name': EGGS[i][0],
            'count': count
        }

        for i, count
        in (
            (
                int(key),
                value
            )
            for key, value
            in owned.items()
        )

        if count > 0
    }

    return jsonify(
        ok=True,
        bot=WITHDRAWAL_BOT,
        total=sum(
            owned.values()
        ),
        eggs=eggs
    )


# =========================================================
# CHESTS
# =========================================================

@app.get('/api/chests')
def api_chests():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    conn = extra_conn()

    rows = conn.execute(
        '''
        SELECT chest_id, count
        FROM chest_opens
        WHERE user_id=?
        ''',
        (uid,)
    ).fetchall()

    conn.close()

    opened = {
        int(row['chest_id']):
            int(row['count'])
        for row in rows
    }

    return jsonify(
        ok=True,

        chests={
            str(i): {
                'id': i,
                'name': chest[0],
                'price': chest[1],
                'egg_chance': chest[2],
                'opened':
                    opened.get(i, 0)
            }

            for i, chest
            in CHESTS.items()
        }
    )


# =========================================================
# OPEN CHEST
# =========================================================

@app.post('/api/chests/open')
def api_chest_open():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    try:

        chest_id = int(
            (request.json or {}).get(
                'chest_id'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверный сундук.'
        )

    if chest_id not in CHESTS:

        return json_error(
            'Такого сундука нет.'
        )

    price = CHESTS[chest_id][1]

    if not database.remove_egg_coins(
        uid,
        price
    ):

        return json_error(
            'Недостаточно Egg Coins.'
        )

    # Pet chest
    if (
        chest_id == 7
        and random.random() < 0.70
    ):

        pet_id = random.choices(
            list(PETS),
            weights=[
                45,
                25,
                15,
                8,
                5,
                1.5,
                0.5
            ]
        )[0]

        conn = extra_conn()

        conn.execute(
            '''
            INSERT OR IGNORE INTO player_pets(
                user_id,
                pet_id,
                active
            )
            VALUES(?,?,0)
            ''',
            (
                uid,
                pet_id
            )
        )

        conn.commit()
        conn.close()

        result = {
            'type': 'pet',

            'pet': {
                'id': pet_id,
                'name': PETS[pet_id][0],
                'rarity': PETS[pet_id][1],
                'bonus': PETS[pet_id][2]
            }
        }

    elif (
        random.random() * 100
        < CHESTS[chest_id][2]
    ):

        egg_id = chest_egg()

        database.add_egg(
            uid,
            egg_id
        )

        progress_daily(
            uid,
            'egg'
        )

        result = {
            'type': 'egg',

            'egg': {
                'id': egg_id,
                'name': EGGS[egg_id][0],
                'rarity': EGGS[egg_id][2]
            }
        }

    else:

        roll = random.random()

        if roll < 0.65:

            amount = (
                random.randint(20, 60)
                * (chest_id + 1)
            )

            database.add_egg_coins(
                uid,
                amount
            )

            result = {
                'type': 'coins',
                'amount': amount
            }

        elif roll < 0.90:

            item_id = random.choices(
                [1, 2, 3],
                [45, 35, 20]
            )[0]

            database.add_item(
                uid,
                item_id
            )

            result = {
                'type': 'booster',

                'item': {
                    'id': item_id,
                    'name': ITEMS[item_id][0]
                }
            }

        else:

            amount = (
                random.randint(20, 80)
                * chest_id
            )

            database.add_xp(
                uid,
                amount
            )

            result = {
                'type': 'xp',
                'amount': amount
            }

    conn = extra_conn()

    conn.execute(
        '''
        INSERT INTO chest_opens(
            user_id,
            chest_id,
            count
        )
        VALUES(?,?,1)

        ON CONFLICT(user_id,chest_id)
        DO UPDATE SET
            count=count+1
        ''',
        (
            uid,
            chest_id
        )
    )

    conn.commit()
    conn.close()

    progress_daily(
        uid,
        'chest'
    )

    add_pass_xp(
        uid,
        10
    )

    return jsonify(
        ok=True,
        reward=result,
        data=snap(uid)
    )


# =========================================================
# PETS
# =========================================================

@app.get('/api/pets')
def api_pets():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    conn = extra_conn()

    rows = conn.execute(
        '''
        SELECT pet_id, active
        FROM player_pets
        WHERE user_id=?
        ''',
        (uid,)
    ).fetchall()

    conn.close()

    owned = {
        int(row['pet_id']):
            int(row['active'])
        for row in rows
    }

    return jsonify(
        ok=True,

        pets={
            str(i): {
                'id': i,
                'name': pet[0],
                'rarity': pet[1],
                'bonus': pet[2],
                'owned': i in owned,
                'active':
                    bool(
                        owned.get(i, 0)
                    )
            }

            for i, pet
            in PETS.items()
        }
    )


# =========================================================
# ACTIVATE PET
# =========================================================

@app.post('/api/pets/activate')
def api_pet_activate():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    try:

        pet_id = int(
            (request.json or {}).get(
                'pet_id'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверный питомец.'
        )

    if pet_id not in PETS:

        return json_error(
            'Такого питомца нет.'
        )

    conn = extra_conn()

    owned = conn.execute(
        '''
        SELECT 1
        FROM player_pets
        WHERE user_id=?
        AND pet_id=?
        ''',
        (
            uid,
            pet_id
        )
    ).fetchone()

    if not owned:

        conn.close()

        return json_error(
            'У тебя нет этого питомца.'
        )

    conn.execute(
        '''
        UPDATE player_pets
        SET active=0
        WHERE user_id=?
        ''',
        (uid,)
    )

    conn.execute(
        '''
        UPDATE player_pets
        SET active=1
        WHERE user_id=?
        AND pet_id=?
        ''',
        (
            uid,
            pet_id
        )
    )

    conn.commit()
    conn.close()

    return jsonify(
        ok=True,
        data=snap(uid)
    )


# =========================================================
# MARKET
# =========================================================

@app.get('/api/market')
def api_market():

    u, f = auth()

    if f:
        return f

    rarity = request.args.get(
        'rarity',
        ''
    )

    search = request.args.get(
        'search',
        ''
    ).lower()

    conn = extra_conn()

    rows = conn.execute(
        '''
        SELECT *
        FROM market_listings
        WHERE sold=0
        ORDER BY id DESC
        LIMIT 100
        '''
    ).fetchall()

    conn.close()

    listings = []

    for row in rows:

        egg = EGGS.get(
            int(row['egg_id'])
        )

        if not egg:
            continue

        if (
            rarity
            and egg[2] != rarity
        ):
            continue

        if (
            search
            and search not in egg[0].lower()
        ):
            continue

        listings.append({
            'id': row['id'],
            'seller_id': row['seller_id'],
            'egg_id': row['egg_id'],
            'name': egg[0],
            'rarity': egg[2],
            'price': row['price'],
            'fee': max(
                1,
                int(row['price'] * 0.05)
            ),
            'created_at':
                row['created_at']
        })

    return jsonify(
        ok=True,
        listings=listings
    )


# =========================================================
# MARKET LIST
# =========================================================

@app.post('/api/market/list')
def api_market_list():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    data = request.json or {}

    try:

        egg_id = int(
            data.get('egg_id')
        )

        price = int(
            data.get('price')
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверные данные.'
        )

    if egg_id not in EGGS:

        return json_error(
            'Такого яйца нет.'
        )

    if not 1 <= price <= 10000000:

        return json_error(
            'Цена должна быть от 1 до 10 000 000.'
        )

    if not database.remove_one_egg(
        uid,
        egg_id
    ):

        return json_error(
            'У тебя нет этого яйца.'
        )

    conn = extra_conn()

    conn.execute(
        '''
        INSERT INTO market_listings(
            seller_id,
            egg_id,
            price,
            created_at,
            sold
        )
        VALUES(?,?,?,?,0)
        ''',
        (
            uid,
            egg_id,
            price,
            int(time.time())
        )
    )

    conn.commit()
    conn.close()

    return jsonify(
        ok=True,
        data=snap(uid)
    )


# =========================================================
# MARKET BUY
# =========================================================

@app.post('/api/market/buy')
def api_market_buy():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    try:

        listing_id = int(
            (request.json or {}).get(
                'listing_id'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверный лот.'
        )

    conn = extra_conn()

    row = conn.execute(
        '''
        SELECT *
        FROM market_listings
        WHERE id=?
        AND sold=0
        ''',
        (listing_id,)
    ).fetchone()

    if not row:

        conn.close()

        return json_error(
            'Лот уже продан.'
        )

    if row['seller_id'] == uid:

        conn.close()

        return json_error(
            'Нельзя купить свой лот.'
        )

    total = (
        int(row['price'])
        + max(
            1,
            int(row['price'] * 0.05)
        )
    )

    if not database.remove_egg_coins(
        uid,
        total
    ):

        conn.close()

        return json_error(
            f'Нужно {total} Egg Coins.'
        )

    database.add_egg(
        uid,
        row['egg_id']
    )

    database.add_egg_coins(
        row['seller_id'],
        row['price']
    )

    conn.execute(
        '''
        UPDATE market_listings
        SET sold=1
        WHERE id=?
        ''',
        (listing_id,)
    )

    conn.commit()
    conn.close()

    progress_daily(
        uid,
        'market'
    )

    return jsonify(
        ok=True,

        bought={
            'egg_id': row['egg_id'],
            'name': EGGS[row['egg_id']][0],
            'price': row['price']
        },

        data=snap(uid)
    )


# =========================================================
# MARKET CANCEL
# =========================================================

@app.post('/api/market/cancel')
def api_market_cancel():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    try:

        listing_id = int(
            (request.json or {}).get(
                'listing_id'
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверный лот.'
        )

    conn = extra_conn()

    row = conn.execute(
        '''
        SELECT *
        FROM market_listings
        WHERE id=?
        AND seller_id=?
        AND sold=0
        ''',
        (
            listing_id,
            uid
        )
    ).fetchone()

    if not row:

        conn.close()

        return json_error(
            'Лот не найден.'
        )

    database.add_egg(
        uid,
        row['egg_id']
    )

    conn.execute(
        '''
        UPDATE market_listings
        SET sold=1
        WHERE id=?
        ''',
        (listing_id,)
    )

    conn.commit()
    conn.close()

    return jsonify(
        ok=True,
        data=snap(uid)
    )


# =========================================================
# BOSS
# =========================================================

def get_boss():

    now = int(
        time.time()
    )

    conn = extra_conn()

    row = conn.execute(
        '''
        SELECT *
        FROM boss_event
        WHERE id=1
        '''
    ).fetchone()

    if (
        not row
        or now >= row['ends_at']
        or (
            row['hp'] <= 0
            and row['reward_claimed']
        )
    ):

        conn.execute(
            'DELETE FROM boss_contributions'
        )

        conn.execute(
            '''
            INSERT INTO boss_event(
                id,
                hp,
                max_hp,
                started_at,
                ends_at,
                reward_claimed
            )
            VALUES(1,?,?,?,?,0)

            ON CONFLICT(id)
            DO UPDATE SET
                hp=excluded.hp,
                max_hp=excluded.max_hp,
                started_at=excluded.started_at,
                ends_at=excluded.ends_at,
                reward_claimed=0
            ''',
            (
                BOSS_MAX_HP,
                BOSS_MAX_HP,
                now,
                now + 86400
            )
        )

        conn.commit()

        row = conn.execute(
            '''
            SELECT *
            FROM boss_event
            WHERE id=1
            '''
        ).fetchone()

    conn.close()

    return dict(row)


# =========================================================
# BOSS INFO
# =========================================================

@app.get('/api/boss')
def api_boss():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    boss = get_boss()

    conn = extra_conn()

    my_damage = conn.execute(
        '''
        SELECT damage
        FROM boss_contributions
        WHERE user_id=?
        ''',
        (uid,)
    ).fetchone()

    top = conn.execute(
        '''
        SELECT user_id, damage
        FROM boss_contributions
        ORDER BY damage DESC
        LIMIT 10
        '''
    ).fetchall()

    conn.close()

    return jsonify(
        ok=True,

        hp=boss['hp'],

        max_hp=boss['max_hp'],

        ends_at=boss['ends_at'],

        my_damage=(
            my_damage['damage']
            if my_damage
            else 0
        ),

        leaderboard=[
            {
                'user_id': row['user_id'],
                'damage': row['damage']
            }

            for row in top
        ]
    )


# =========================================================
# BOSS ATTACK
# =========================================================

@app.post('/api/boss/attack')
def api_boss_attack():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    now = time.time()

    if (
        now - last_boss.get(uid, 0)
        < 0.7
    ):

        return json_error(
            'Подожди немного.',
            429
        )

    last_boss[uid] = now

    boss = get_boss()

    damage = min(
        random.randint(20, 60),
        boss['hp']
    )

    conn = extra_conn()

    conn.execute(
        '''
        UPDATE boss_event
        SET hp=hp-?
        WHERE id=1
        ''',
        (damage,)
    )

    conn.execute(
        '''
        INSERT INTO boss_contributions(
            user_id,
            damage
        )
        VALUES(?,?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            damage=damage+excluded.damage
        ''',
        (
            uid,
            damage
        )
    )

    conn.commit()
    conn.close()

    database.add_boss_damage(
        uid,
        damage
    )

    progress_daily(
        uid,
        'boss',
        damage
    )

    add_pass_xp(
        uid,
        max(
            1,
            damage // 5
        )
    )

    new_hp = max(
        0,
        boss['hp'] - damage
    )

    return jsonify(
        ok=True,

        damage=damage,

        hp=new_hp,

        max_hp=BOSS_MAX_HP,

        defeated=(
            new_hp <= 0
        ),

        data=snap(uid),

        new_achievements=
            achievements(uid)
    )


# =========================================================
# EGG PASS
# =========================================================

@app.get('/api/egg-pass')
def api_pass():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    conn = extra_conn()

    row = conn.execute(
        '''
        SELECT *
        FROM egg_pass
        WHERE user_id=?
        ''',
        (uid,)
    ).fetchone()

    if not row:

        conn.execute(
            '''
            INSERT INTO egg_pass(
                user_id,
                xp,
                level
            )
            VALUES(?,?,?)
            ''',
            (
                uid,
                0,
                0
            )
        )

        conn.commit()

        row = conn.execute(
            '''
            SELECT *
            FROM egg_pass
            WHERE user_id=?
            ''',
            (uid,)
        ).fetchone()

    claims = conn.execute(
        '''
        SELECT level, track
        FROM egg_pass_claims
        WHERE user_id=?
        ''',
        (uid,)
    ).fetchall()

    conn.close()

    claimed = {
        f"{claim['level']}:{claim['track']}"
        for claim in claims
    }

    levels = []

    for level in range(
        1,
        PASS_MAX + 1
    ):

        levels.append({
            'level': level,

            'free_coins':
                20 + level * 5,

            'premium_coins':
                50 + level * 10,

            'free_claimed':
                f'{level}:free'
                in claimed,

            'premium_claimed':
                f'{level}:premium'
                in claimed
        })

    return jsonify(
        ok=True,

        state={
            'xp': row['xp'],
            'level': row['level']
        },

        levels=levels
    )


# =========================================================
# EGG PASS CLAIM
# =========================================================

@app.post('/api/egg-pass/claim')
def api_pass_claim():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    data = request.json or {}

    try:

        level = int(
            data.get('level')
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверный уровень.'
        )

    track = data.get(
        'track',
        'free'
    )

    if (
        not 1 <= level <= PASS_MAX
        or track not in (
            'free',
            'premium'
        )
    ):

        return json_error(
            'Неверная награда.'
        )

    conn = extra_conn()

    row = conn.execute(
        '''
        SELECT level
        FROM egg_pass
        WHERE user_id=?
        ''',
        (uid,)
    ).fetchone()

    current_level = (
        int(row['level'])
        if row
        else 0
    )

    if current_level < level:

        conn.close()

        return json_error(
            'Этот уровень ещё не достигнут.'
        )

    already = conn.execute(
        '''
        SELECT 1
        FROM egg_pass_claims
        WHERE user_id=?
        AND level=?
        AND track=?
        ''',
        (
            uid,
            level,
            track
        )
    ).fetchone()

    if already:

        conn.close()

        return json_error(
            'Награда уже получена.'
        )

    conn.execute(
        '''
        INSERT INTO egg_pass_claims(
            user_id,
            level,
            track
        )
        VALUES(?,?,?)
        ''',
        (
            uid,
            level,
            track
        )
    )

    conn.commit()
    conn.close()

    if track == 'free':

        reward = (
            20
            + level * 5
        )

    else:

        reward = (
            50
            + level * 10
        )

    database.add_egg_coins(
        uid,
        reward
    )

    return jsonify(
        ok=True,
        reward=reward,
        data=snap(uid)
    )


# =========================================================
# STEAL PLAYERS
# =========================================================

@app.get('/api/steal/players')
def api_steal_players():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    players = database.get_top_players(
        30
    )

    result = []

    for player in players:

        player_id = int(
            player['user_id']
        )

        if player_id == uid:
            continue

        result.append({
            'user_id': player_id,

            'username':
                player.get(
                    'username',
                    ''
                ) or 'Игрок',

            'avatar':
                database.get_avatar(
                    player_id
                ),

            'eggs':
                database.get_total_eggs(
                    player_id
                )
        })

    return jsonify(
        ok=True,
        players=result[:20]
    )


# =========================================================
# STEAL
# =========================================================

@app.post('/api/steal')
def api_steal():

    u, f = auth()

    if f:
        return f

    uid = int(u['id'])

    data = request.json or {}

    try:

        target = int(
            data.get('target_id')
        )

    except (
        TypeError,
        ValueError
    ):

        return json_error(
            'Неверный игрок.'
        )

    if target == uid:

        return json_error(
            'Нельзя красть у себя.'
        )

    now = time.time()

    previous = last_steal.get(
        uid,
        0
    )

    if (
        now - previous
        < 300
    ):

        remaining = int(
            300 - (
                now - previous
            )
        )

        return json_error(
            f'Красть можно раз в 5 минут. '
            f'Осталось {remaining} сек.'
        )

    conn = extra_conn()

    protection = conn.execute(
        '''
        SELECT until_ts
        FROM egg_protection
        WHERE user_id=?
        ''',
        (target,)
    ).fetchone()

    conn.close()

    if (
        protection
        and protection['until_ts'] > now
    ):

        return json_error(
            'У игрока сейчас защита от кражи.'
        )

    eggs = database.get_player_eggs(
        target
    )

    if not eggs:

        return json_error(
            'У игрока нет яиц.'
        )

    egg_id = random.choice(
        eggs
    )

    rarity = EGGS.get(
        egg_id,
        (
            '',
            0,
            '⚪ Обычное'
        )
    )[2]

    chances = {
        '⚪ Обычное': 55,
        '🟢 Необычное': 48,
        '🔵 Редкое': 40,
        '🟣 Эпическое': 33,
        '🟡 Легендарное': 27,
        '🔴 Мифическое': 20,
        '💠 Божественное': 12,
        '🌈 Секретное': 5
    }

    chance = chances.get(
        rarity,
        30
    )

    success = (
        random.random() * 100
        < chance
    )

    last_steal[uid] = now

    conn = extra_conn()

    conn.execute(
        '''
        INSERT INTO steal_log(
            attacker_id,
            defender_id,
            egg_id,
            success,
            created_at
        )
        VALUES(?,?,?,?,?)
        ''',
        (
            uid,
            target,
            egg_id,
            int(success),
            int(now)
        )
    )

    if (
        success
        and database.remove_one_egg(
            target,
            egg_id
        )
    ):

        database.add_egg(
            uid,
            egg_id
        )

        conn.execute(
            '''
            INSERT INTO egg_protection(
                user_id,
                until_ts
            )
            VALUES(?,?)

            ON CONFLICT(user_id)
            DO UPDATE SET
                until_ts=excluded.until_ts
            ''',
            (
                target,
                int(now) + 1800
            )
        )

        conn.commit()
        conn.close()

        add_pass_xp(
            uid,
            25
        )

        return jsonify(
            ok=True,

            success=True,

            egg={
                'id': egg_id,
                'name': EGGS[egg_id][0],
                'rarity': rarity
            },

            data=snap(uid)
        )

    conn.commit()
    conn.close()

    return jsonify(
        ok=True,
        success=False,
        message=(
            'Кража не удалась. '
            'Игрок заметил попытку.'
        )
    )


# =========================================================
# START SERVER
# =========================================================

if __name__ == '__main__':

    database.init_database()

    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False
    )
