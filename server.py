import os
import time
import hmac
import hashlib
import json
import random
import threading
from datetime import date
from urllib.parse import parse_qsl
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sys
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)
import database
# =========================================================
# SERVER
# =========================================================
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)
app = Flask(
    __name__,
    static_folder=None
)
CORS(
    app,
    resources={
        r'/api/*': {
            'origins': '*'
        }
    }
)
BOT_TOKEN = os.getenv(
    'BOT_TOKEN',
    ''
)
PORT = int(
    os.getenv(
        'PORT',
        '8080'
    )
)
WITHDRAWAL_BOT = (
    'https://t.me/stealthegg_vyvod_bot'
)
# =========================================================
# EGGS
# =========================================================
EGGS = {
    1: (
        '🥚 Обычное яйцо',
        100,
        '⚪ Обычное'
    ),
    2: (
        '🥈 Серебряное яйцо',
        600,
        '🟢 Необычное'
    ),
    3: (
        '🥇 Золотое яйцо',
        900,
        '🔵 Редкое'
    ),
    4: (
        '💎 Алмазное яйцо',
        1400,
        '🟣 Эпическое'
    ),
    5: (
        '🔥 Огненное яйцо',
        1800,
        '🟣 Эпическое'
    ),
    6: (
        '❄️ Ледяное яйцо',
        2300,
        '🟡 Легендарное'
    ),
    7: (
        '🌌 Космическое яйцо',
        3000,
        '🟡 Легендарное'
    ),
    8: (
        '👑 Королевское яйцо',
        4500,
        '🔴 Мифическое'
    ),
    9: (
        '⚡ Молниевое яйцо',
        6000,
        '🔴 Мифическое'
    ),
    10: (
        '🌑 Тёмное яйцо',
        8000,
        '🔴 Мифическое'
    ),
    11: (
        '☀️ Солнечное яйцо',
        11000,
        '💠 Божественное'
    ),
    12: (
        '🪐 Галактическое яйцо',
        15000,
        '💠 Божественное'
    ),
    13: (
        '🧿 Проклятое яйцо',
        22000,
        '🌈 Секретное'
    ),
    14: (
        '🪽 Небесное яйцо',
        30000,
        '🌈 Секретное'
    ),
    15: (
        '👾 Глитч-яйцо',
        50000,
        '🌈 Секретное'
    ),
    16: (
        '🌋 Магмовое яйцо',
        9500,
        '🟡 Легендарное'
    ),
    17: (
        '🌊 Океанское яйцо',
        7000,
        '🔴 Мифическое'
    ),
    18: (
        '🌳 Древнее яйцо',
        12500,
        '💠 Божественное'
    ),
    19: (
        '👻 Призрачное яйцо',
        5500,
        '🔴 Мифическое'
    ),
    20: (
        '🩸 Тёмно-красное яйцо',
        18000,
        '💠 Божественное'
    ),
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
# CHESTS
# =========================================================
#
# 1. 📦 Обычный       - 200
# 2. 🥈 Серебряный    - 400
# 3. 🥇 Золотой       - 700
# 4. 🌌 Космический   - 1300
# 5. 👑 Легендарный   - 2600
# 6. 🔥 Огненный      - 4000
# 7. ❄️ Ледяной       - 6000
# 8. ⚡ Молниевой     - 9000
# 9. 🌑 Тёмный        - 13000
# 10. 🌌 Божественный - 20000
#
# Третье значение = шанс выпадения яйца.
#
CHESTS = {
    1: (
        '📦 Обычный сундук',
        200,
        1.5
    ),
    2: (
        '🥈 Серебряный сундук',
        400,
        2.5
    ),
    3: (
        '🥇 Золотой сундук',
        700,
        4.0
    ),
    4: (
        '🌌 Космический сундук',
        1300,
        6.0
    ),
    5: (
        '👑 Легендарный сундук',
        2600,
        8.0
    ),
    6: (
        '🔥 Огненный сундук',
        4000,
        10.0
    ),
    7: (
        '❄️ Ледяной сундук',
        6000,
        12.0
    ),
    8: (
        '⚡ Молниевой сундук',
        9000,
        14.0
    ),
    9: (
        '🌑 Тёмный сундук',
        13000,
        17.0
    ),
    10: (
        '🌌 Божественный сундук',
        20000,
        20.0
    ),
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
# Цена Premium Egg Pass в Egg Coins.
# None - Premium недоступен (кнопка покупки скрыта).
PREMIUM_PASS_PRICE = 2000
# Максимум Egg Coins в день за мини-игры
# (угадай число, математика, крестики-нолики).
# None - без лимита.
GAME_DAILY_CAP = 300
# Сколько секунд после конца босса можно забрать награду,
# прежде чем появится следующий босс.
BOSS_CLAIM_WINDOW = 6 * 3600
BOSS_NAMES = [
    'Король Яиц',
    'Тёмный Хранитель',
    'Яичный Дракон',
    'Кибер-Курица'
]
BOSS_LOCK = threading.Lock()
# =========================================================
# BOSS
# =========================================================
BOSS_MAX_HP = 100000
BOSS_DURATION = 86400
# =========================================================
# GAME MEMORY
# =========================================================
# (бустеры теперь хранятся в БД: таблица player_boosters)
guess = {}
math = {}
tic = {}
last_tap = {}
last_game = {}
last_boss = {}
last_steal = {}
# =========================================================
# DATABASE
# =========================================================
database.init_database()
# =========================================================
# PET BONUS
# =========================================================
def pet_bonus(uid):
    pet = database.get_active_pet(uid)
    if not pet:
        return 0
    try:
        pet_id = int(
            pet['pet_id']
        )
    except (
        TypeError,
        ValueError,
        KeyError
    ):
        return 0
    if pet_id not in PETS:
        return 0
    rarity = PETS[pet_id][1]
    return PET_BONUS.get(
        rarity,
        0
    )
# =========================================================
# EGG PASS
# =========================================================
def add_pass_xp(uid, amount):
    database.ensure_egg_pass(uid)
    database.add_egg_pass_xp(
        uid,
        int(amount)
    )
# =========================================================
# RANDOM EGG
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
# TELEGRAM AUTH
# =========================================================
def user():
    raw = request.headers.get(
        'X-Telegram-Init-Data',
        ''
    )
    if not raw:
        return (
            None,
            'Открой Mini App через Telegram.'
        )
    if not BOT_TOKEN:
        return (
            None,
            'На сервере не задан BOT_TOKEN.'
        )
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
        return (
            None,
            'Нет hash Telegram.'
        )
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
        return (
            None,
            'Неверная подпись Telegram.'
        )
    try:
        auth_date = int(
            params.get(
                'auth_date',
                '0'
            )
        )
        if (
            time.time() - auth_date
            > 86400
        ):
            return (
                None,
                'Сессия Telegram устарела.'
            )
        telegram_user = json.loads(
            params['user']
        )
    except Exception:
        return (
            None,
            'Некорректные данные Telegram.'
        )
    try:
        uid = int(
            telegram_user['id']
        )
    except (
        KeyError,
        TypeError,
        ValueError
    ):
        return (
            None,
            'Некорректный ID Telegram.'
        )
    database.ensure_player(
        uid,
        telegram_user.get(
            'username',
            ''
        ) or '',
        telegram_user.get(
            'first_name',
            ''
        ) or ''
    )
    if database.is_blocked(uid):
        return (
            None,
            'Твой аккаунт заблокирован.'
        )
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
# BOOSTERS
# =========================================================
def expiry(
    uid,
    item_id
):
    return database.get_booster_until(
        uid,
        item_id
    )
def has(
    uid,
    item_id
):
    return (
        expiry(
            uid,
            item_id
        )
        > time.time()
    )
# =========================================================
# XP
# =========================================================
def add_xp(
    uid,
    amount
):
    multiplier = (
        2
        if has(uid, 3)
        else 1
    )
    database.add_xp(
        uid,
        int(amount * multiplier)
    )
# =========================================================
# GAME COINS
# =========================================================
def add_game_coins(
    uid,
    amount
):
    amount = int(amount)
    if has(uid, 2):
        amount += 1
    bonus = pet_bonus(uid)
    if bonus > 0:
        amount = int(
            amount * (
                1 + bonus
            )
        )
    database.add_egg_coins(
        uid,
        amount
    )
# =========================================================
# MINIGAME REWARD
# =========================================================
def minigame_reward(
    uid,
    amount
):
    """
    Награда за мини-игру: бустер Egg Coins, бонус питомца
    и дневной лимит GAME_DAILY_CAP.
    Возвращает (начислено, упёрлись_в_лимит).
    """
    amount = int(amount)
    if has(uid, 2):
        amount += 1
    bonus = pet_bonus(uid)
    if bonus > 0:
        amount = int(
            amount * (1 + bonus)
        )
    capped = False
    if GAME_DAILY_CAP:
        left = max(
            0,
            GAME_DAILY_CAP
            - database.get_game_reward_today(uid)
        )
        if amount > left:
            amount = left
            capped = True
    if amount > 0:
        database.add_egg_coins(
            uid,
            amount
        )
        database.add_game_reward_today(
            uid,
            amount
        )
    return amount, capped
# =========================================================
# EGG COUNTS
# =========================================================
def egg_counts(uid):
    eggs = database.get_player_eggs(
        uid
    )
    return {
        str(i): eggs.count(i)
        for i in EGGS
    }
# =========================================================
# PLAYER SNAPSHOT
# =========================================================
def snap(uid):
    tap = database.get_tap_coins(
        uid
    )
    egg = database.get_egg_coins(
        uid
    )
    current_xp, level = (
        database.get_progress(uid)
    )
    streak = database.get_login_streak(
        uid
    )
    login_status = database.get_login_status(
        uid
    )
    tasks = database.get_daily_tasks(
        uid
    )
    owned = egg_counts(uid)
    xp_required = 100
    return {
        'tap_coins':
            int(tap),
        'egg_coins':
            int(egg),
        'xp':
            int(current_xp),
        'level':
            int(level),
        'xp_required': int(xp_required),
        'xp_in_level': int(current_xp) % 100,
        'streak':
            int(streak),
        'last_login':
            login_status.get(
                'last_login'
            )
            if isinstance(
                login_status,
                dict
            )
            else None,
        'eggs_total':
            sum(
                owned.values()
            ),
        'eggs':
            owned,
        'avatar':
            database.get_avatar(uid),
        'avatars':
            AVATARS,
        'achievements':
            database.get_achievements(uid),
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
            'taps':
                int(tasks[0]),
            'games':
                int(tasks[1]),
            'eggs':
                int(tasks[2]),
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
                )
        }
    }
# =========================================================
# ACHIEVEMENTS CHECK
# =========================================================
def achievements(uid):
    tap = database.get_tap_coins(
        uid
    )
    eggs = database.get_player_eggs(
        uid
    )
    _, level = database.get_progress(
        uid
    )
    streak = database.get_login_streak(
        uid
    )
    tasks = database.get_daily_tasks(
        uid
    )
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
            database.get_boss_damage(uid)
            >= 100
    }
    unlocked = []
    for (
        achievement_id,
        condition
    ) in checks.items():
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
                'id':
                    achievement_id,
                'name':
                    ACH[achievement_id][0],
                'reward':
                    ACH[achievement_id][2]
            })
    return unlocked
# =========================================================
# REQUEST BODY
# =========================================================
def body():
    """JSON-тело запроса; всегда словарь (мусор -> пустой dict)."""
    data = request.get_json(
        silent=True
    )
    if isinstance(data, dict):
        return data
    return {}
# =========================================================
# JSON ERROR
# =========================================================
def json_error(
    message,
    status=400
):
    return (
        jsonify(
            ok=False,
            error=message
        ),
        status
    )
# =========================================================
# INDEX / STATIC / HEALTH
# =========================================================
#
# ВАЖНО: раньше Flask раздавал ВСЮ папку проекта, включая
# players.db, server.py и database.py. Теперь отдаются
# только три файла интерфейса.
#
STATIC_FILES = {
    'index.html',
    'style.css',
    'script.js'
}
@app.get('/')
def index():
    index_path = os.path.join(
        BASE_DIR,
        'index.html'
    )
    if os.path.exists(index_path):
        return send_from_directory(
            BASE_DIR,
            'index.html'
        )
    return jsonify(
        ok=True,
        message=(
            'STEAL THE EGG '
            'server is running!'
        )
    )
@app.get('/health')
def health():
    return jsonify(
        ok=True
    )
@app.get('/<path:filename>')
def static_files(filename):
    if filename in STATIC_FILES:
        return send_from_directory(
            BASE_DIR,
            filename
        )
    return json_error(
        'Не найдено.',
        404
    )
# =========================================================
# INIT
# =========================================================
@app.post('/api/init')
def init():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    today = date.today().isoformat()
    login_status = (
        database.get_login_status(uid)
    )
    last_login = None
    if isinstance(
        login_status,
        dict
    ):
        last_login = login_status.get(
            'last_login'
        )
    elif isinstance(
        login_status,
        (tuple, list)
    ) and len(login_status) >= 2:
        last_login = login_status[1]
    streak = database.get_login_streak(
        uid
    )
    claimed = False
    reward = 0
    if last_login != today:
        streak = database.update_login(
            uid
        )
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
    database.ensure_egg_pass(
        uid
    )
    return jsonify(
        ok=True,
        user={
            'id':
                uid,
            'username':
                u.get(
                    'username',
                    ''
                ),
            'first_name':
                u.get(
                    'first_name',
                    ''
                )
        },
        login={
            'claimed':
                claimed,
            'streak':
                streak,
            'reward':
                reward
        },
        data=
            snap(uid),
        new_achievements=
            achievements(uid)
    )
# =========================================================
# STATE
# =========================================================
@app.get('/api/state')
def state():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    return jsonify(
        ok=True,
        data=snap(uid)
    )
# =========================================================
# TAP
# =========================================================
@app.post('/api/tap')
def tap():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    now = time.time()
    old = [
        timestamp
        for timestamp
        in last_tap.get(
            uid,
            []
        )
        if now - timestamp < 2
    ]
    if len(old) >= 30:
        return json_error(
            'Слишком быстро. Подожди немного.',
            429
        )
    old.append(now)
    last_tap[uid] = old
    gain = (
        3
        if has(uid, 1)
        else 1
    )
    database.add_tap_coins(
        uid,
        gain
    )
    database.add_task_tap(
        uid,
        1
    )
    add_pass_xp(
        uid,
        1
    )
    add_xp(
        uid,
        1
    )
    return jsonify(
        ok=True,
        gained=
            gain,
        data=
            snap(uid),
        new_achievements=
            achievements(uid)
    )
# =========================================================
# EXCHANGE TAP COINS -> EGG COINS
# =========================================================
@app.post('/api/exchange')
def exchange():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    tap = database.get_tap_coins(
        uid
    )
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
        spent=
            spent,
        received=
            received,
        data=
            snap(uid)
    )
# =========================================================
# GAME COOLDOWN
# =========================================================
def game_ok(uid):
    now = time.time()
    if (
        now - last_game.get(
            uid,
            0
        )
        < 2
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
    uid = int(
        u['id']
    )
    if not game_ok(uid):
        return json_error(
            'Подожди немного.',
            429
        )
    guess[uid] = {
        'n':
            random.randint(
                1,
                20
            ),
        'a':
            0
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
    uid = int(
        u['id']
    )
    game = guess.get(
        uid
    )
    if not game:
        return json_error(
            'Игра не запущена.'
        )
    try:
        value = int(
            (body() or {}).get(
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
        reward, capped = minigame_reward(
            uid,
            rewards[attempts]
        )
        database.add_task_game(
            uid
        )
        add_pass_xp(
            uid,
            10
        )
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
            result='win', reward=reward, capped=capped, number=number,
            attempts=
                attempts,
            data=
                snap(uid),
            new_achievements=
                achievements(uid)
        )
    if attempts >= 10:
        number = game['n']
        guess.pop(
            uid,
            None
        )
        database.add_task_game(
            uid
        )
        add_pass_xp(
            uid,
            5
        )
        add_xp(
            uid,
            5
        )
        return jsonify(
            ok=True,
            result='lose',
            reward=0,
            number=
                number,
            attempts=
                attempts,
            data=
                snap(uid),
            new_achievements=
                achievements(uid)
        )
    return jsonify(
        ok=True,
        result='continue',
        hint=(
            'Больше!'
            if value < game['n']
            else 'Меньше!'
        ),
        attempts=
            attempts
    )
# =========================================================
# MATH GAME START
# =========================================================
def create_math_question(uid):
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
        'a':
            a,
        'b':
            b,
        'op':
            operation,
        'answer':
            answer
    }
    return (
        f'{a} '
        f'{operation} '
        f'{b} = ?'
    )
@app.post('/api/game/math/start')
def math_start():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    if not game_ok(uid):
        return json_error(
            'Подожди немного.',
            429
        )
    question = create_math_question(
        uid
    )
    return jsonify(
        ok=True,
        question=question
    )
# =========================================================
# MATH ANSWER
# =========================================================
@app.post('/api/game/math/answer')
def math_answer():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    game = math.get(
        uid
    )
    if not game:
        return json_error(
            'Задание не запущено.'
        )
    try:
        value = int(
            (body() or {}).get(
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
    if value == correct:
        math.pop(uid, None)
        database.add_task_game(uid)
        reward, capped = minigame_reward(
            uid,
            4
        )
        add_pass_xp(
            uid,
            10
        )
        add_xp(
            uid,
            10
        )
        return jsonify(
            ok=True,
            result='win', correct=correct, reward=reward, capped=capped,
            data=
                snap(uid),
            new_achievements=
                achievements(uid)
        )
    new_question = create_math_question(
        uid
    )
    return jsonify(
        ok=True,
        result='wrong',
        correct=
            correct,
        reward=0,
        question=
            new_question,
        data=
            snap(uid),
        new_achievements=
            achievements(uid)
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
# TIC-TAC-TOE COMPUTER
# =========================================================
#
# 70% ходов компьютер играет «по уму»
# (выигрывает, блокирует, берёт центр и углы),
# 30% - случайно. Так его можно победить.
#
def computer_move(board):
    empty = [
        position
        for position, value
        in enumerate(board)
        if value == ' '
    ]
    if not empty:
        return None
    if random.random() < 0.3:
        return random.choice(empty)
    # 1. Выиграть самому, 2. Не дать выиграть игроку
    for mark in ('O', 'X'):
        for position in empty:
            board[position] = mark
            won = winner(board) == mark
            board[position] = ' '
            if won:
                return position
    # 3. Центр, затем углы, затем стороны
    for position in (4, 0, 2, 6, 8, 1, 3, 5, 7):
        if position in empty:
            return position
    return random.choice(empty)
# =========================================================
# TIC-TAC-TOE START
# =========================================================
@app.post('/api/game/tic/start')
def tic_start():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
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
        board=
            tic[uid],
        result=
            'continue'
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
    capped = False
    if reward:
        reward, capped = minigame_reward(
            uid,
            reward
        )
    if xp_amount:
        add_pass_xp(
            uid,
            xp_amount
        )
        add_xp(
            uid,
            xp_amount
        )
    database.add_task_game(
        uid
    )
    board = tic.pop(
        uid,
        [' '] * 9
    )
    return jsonify(
        ok=True,
        board=board, result=result, reward=reward, capped=capped,
        data=
            snap(uid),
        new_achievements=
            achievements(uid)
    )
# =========================================================
# TIC-TAC-TOE MOVE
# =========================================================
@app.post('/api/game/tic/move')
def tic_move():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    board = tic.get(
        uid
    )
    if board is None:
        return json_error(
            'Игра не запущена.'
        )
    try:
        index = int(
            (body() or {}).get(
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
    # Игрок
    board[index] = 'X'
    result = winner(
        board
    )
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
    # Компьютер
    computer_position = computer_move(
        board
    )
    if computer_position is not None:
        board[
            computer_position
        ] = 'O'
    result = winner(
        board
    )
    if result == 'O':
        return finish_tic(
            uid,
            'lose',
            0,
            5
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
        board=
            board,
        result=
            'continue'
    )
# =========================================================
# EGGS SHOP
# =========================================================
#
# Серверную систему оставляем.
# Сам магазин яиц уберём из интерфейса отдельно.
#
@app.get('/api/eggs')
def eggs():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    owned = egg_counts(
        uid
    )
    shop = {
        str(i): {
            'id':
                i,
            'name':
                egg[0],
            'price':
                egg[1],
            'rarity':
                egg[2]
        }
        for i, egg
        in EGGS.items()
    }
    return jsonify(
        ok=True,
        shop=
            shop,
        owned=
            owned,
        total=
            sum(
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
    uid = int(
        u['id']
    )
    try:
        egg_id = int(
            (body() or {}).get(
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
    price = EGGS[
        egg_id
    ][1]
    if not database.remove_egg_coins(
        uid,
        price
    ):
        return json_error(
            f'Недостаточно Egg Coins. '
            f'Нужно {price} 🥚.'
        )
    database.add_egg(
        uid,
        egg_id
    )
    database.add_task_egg(
        uid
    )
    add_pass_xp(
        uid,
        15
    )
    add_xp(
        uid,
        15
    )
    return jsonify(
        ok=True,
        egg={
            'id':
                egg_id,
            'name':
                EGGS[egg_id][0]
        },
        data=
            snap(uid),
        new_achievements=
            achievements(uid)
    )
# =========================================================
# OPEN EGG
# =========================================================
@app.post('/api/eggs/open')
def open_egg():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    try:
        egg_id = int(
            (body() or {}).get(
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
    reward = (
        5 + egg_id * 2
    )
    add_game_coins(
        uid,
        reward
    )
    add_pass_xp(
        uid,
        20
    )
    add_xp(
        uid,
        20
    )
    return jsonify(
        ok=True,
        reward=
            reward,
        egg={
            'id':
                egg_id,
            'name':
                EGGS[egg_id][0]
        },
        data=
            snap(uid),
        new_achievements=
            achievements(uid)
    )
# =========================================================
# ITEMS LIST
# =========================================================
@app.get('/api/items')
def items():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    return jsonify(
        ok=True,
        items={
            str(i): {
                'id':
                    i,
                'name':
                    item[0],
                'price':
                    item[1],
                'description':
                    item[2],
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
            for i, item
            in ITEMS.items()
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
    uid = int(
        u['id']
    )
    try:
        item_id = int(
            (body() or {}).get(
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
    price = ITEMS[
        item_id
    ][1]
    if not database.remove_egg_coins(
        uid,
        price
    ):
        return json_error(
            f'Недостаточно Egg Coins. '
            f'Нужно {price} 🥚.'
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
    uid = int(
        u['id']
    )
    try:
        item_id = int(
            (body() or {}).get(
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
    database.extend_booster(
        uid,
        item_id,
        600
    )
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
    uid = int(
        u['id']
    )
    unlocked = set(
        database.get_achievements(
            uid
        )
    )
    return jsonify(
        ok=True,
        items=[
            {
                'id':
                    i,
                'name':
                    achievement[0],
                'description':
                    achievement[1],
                'reward':
                    achievement[2],
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
    uid = int(
        u['id']
    )
    players = [
        dict(player)
        for player in database.get_all_players()
        if not int(
            player['blocked']
        )
    ]
    my_rank = None
    for position, player in enumerate(
        players,
        start=1
    ):
        if int(
            player['user_id']
        ) == uid:
            my_rank = position
            break
    result = [
        {
            'user_id': int(player['user_id']),
            'username': player['username'] or '',
            'avatar': player['avatar'] or '🥚',
            'level': int(player['level']),
            'egg_coins': int(player['egg_coins'])
        }
        for player in players[:10]
    ]
    return jsonify(
        ok=True,
        players=result,
        my_rank=my_rank
    )
# =========================================================
# SET AVATAR
# =========================================================
def save_avatar_for_user(uid):
    avatar = str(
        (body() or {}).get(
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
        avatar=
            avatar,
        data=
            snap(uid)
    )
@app.post('/api/profile/avatar')
def set_avatar():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    return save_avatar_for_user(
        uid
    )
# =========================================================
# AVATAR COMPATIBILITY ROUTE
# =========================================================
#
# Старый script.js использовал /api/avatar.
# Оставляем этот маршрут, чтобы аватар работал
# даже до изменения frontend.
#
@app.post('/api/avatar')
def set_avatar_compatibility():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    return save_avatar_for_user(
        uid
    )
# =========================================================
# AVATARS
# =========================================================
@app.get('/api/profile/avatars')
def avatars():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    return jsonify(
        ok=True,
        avatars=
            AVATARS,
        current=
            database.get_avatar(
                uid
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
    uid = int(
        u['id']
    )
    today = date.today().isoformat()
    if (
        database.get_daily_bonus_date(uid)
        == today
    ):
        return json_error(
            'Бонус уже получен сегодня.'
        )
    streak = database.get_login_streak(
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
        reward=
            reward,
        data=
            snap(uid)
    )
# =========================================================
# DAILY TASKS
# =========================================================
@app.get('/api/daily/tasks')
def tasks():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    task = database.get_daily_tasks(
        uid
    )
    return jsonify(
        ok=True,
        tasks=[
            {
                'id':
                    'tap',
                'title':
                    '👆 Сделать 100 тапов',
                'progress':
                    min(
                        task[0],
                        100
                    ),
                'target':
                    100,
                'reward':
                    25,
                'claimed':
                    database.has_daily_task_claim(
                        uid,
                        'tap'
                    )
            },
            {
                'id':
                    'game',
                'title':
                    '🎮 Сыграть 3 игры',
                'progress':
                    min(
                        task[1],
                        3
                    ),
                'target':
                    3,
                'reward':
                    30,
                'claimed':
                    database.has_daily_task_claim(
                        uid,
                        'game'
                    )
            },
            {
                'id':
                    'egg',
                'title':
                    '🥚 Получить 1 яйцо',
                'progress':
                    min(
                        task[2],
                        1
                    ),
                'target':
                    1,
                'reward':
                    40,
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
    uid = int(
        u['id']
    )
    task_id = (
        body() or {}
    ).get(
        'task_id'
    )
    rewards = {
        'tap':
            25,
        'game':
            30,
        'egg':
            40
    }
    targets = {
        'tap':
            100,
        'game':
            3,
        'egg':
            1
    }
    task = database.get_daily_tasks(
        uid
    )
    progress = {
        'tap':
            task[0],
        'game':
            task[1],
        'egg':
            task[2]
    }
    if (
        task_id not in rewards
        or progress[task_id]
        < targets[task_id]
    ):
        return json_error(
            'Задание ещё не выполнено '
            'или неверное задание.'
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
        reward=
            rewards[task_id],
        data=
            snap(uid)
    )
# =========================================================
# WITHDRAWAL
# =========================================================
@app.get('/api/withdrawal')
def withdrawal():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    owned = egg_counts(
        uid
    )
    eggs = {
        str(i): {
            'id':
                i,
            'name':
                EGGS[i][0],
            'count':
                count
        }
        for key, count
        in owned.items()
        for i in [int(key)]
        if count > 0
    }
    return jsonify(
        ok=True,
        bot=
            WITHDRAWAL_BOT,
        total=
            sum(
                owned.values()
            ),
        eggs=
            eggs
    )
# =========================================================
# CHESTS
# =========================================================
@app.get('/api/chests')
def api_chests():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    owned_chests = (
        database.get_player_chests(
            uid
        )
    )
    opened = {}
    for chest in owned_chests:
        chest = dict(
            chest
        )
        chest_id = int(
            chest.get(
                'chest_id',
                0
            )
        )
        opened[chest_id] = (
            opened.get(
                chest_id,
                0
            ) + 1
        )
    return jsonify(
        ok=True,
        chests={
            str(i): {
                'id':
                    i,
                'name':
                    chest[0],
                'price':
                    chest[1],
                'egg_chance':
                    chest[2],
                'owned':
                    opened.get(
                        i,
                        0
                    )
            }
            for i, chest
            in CHESTS.items()
        }
    )
# =========================================================
# BUY CHEST
# =========================================================
@app.post('/api/chests/buy')
def api_chest_buy():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    try:
        chest_id = int(
            (body() or {}).get(
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
    price = int(
        CHESTS[chest_id][1]
    )
    if not database.remove_egg_coins(
        uid,
        price
    ):
        return json_error(
            f'Недостаточно Egg Coins. '
            f'Нужно {price} 🥚.'
        )
    database.add_chest(
        uid,
        chest_id
    )
    add_pass_xp(
        uid,
        10
    )
    add_xp(
        uid,
        10
    )
    return jsonify(
        ok=True,
        chest={
            'id':
                chest_id,
            'name':
                CHESTS[chest_id][0],
            'price':
                price
        },
        data=
            snap(uid)
    )
# =========================================================
# OPEN CHEST
# =========================================================
@app.post('/api/chests/open')
def api_chest_open():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    try:
        chest_id = int(
            (body() or {}).get(
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
    # Сначала проверяем, есть ли такой сундук
    # у игрока.
    if not database.remove_chest(
        uid,
        chest_id
    ):
        return json_error(
            'У тебя нет этого сундука.'
        )
    # =====================================================
    # PET REWARD
    # =====================================================
    #
    # Божественный сундук имеет шанс дать питомца.
    #
    if (
        chest_id == 10
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
        database.add_pet(
            uid,
            pet_id
        )
        result = {
            'type':
                'pet',
            'pet': {
                'id':
                    pet_id,
                'name':
                    PETS[pet_id][0],
                'rarity':
                    PETS[pet_id][1],
                'bonus':
                    PETS[pet_id][2]
            }
        }
    # =====================================================
    # EGG
    # =====================================================
    elif (
        random.random() * 100
        < CHESTS[chest_id][2]
    ):
        egg_id = chest_egg()
        database.add_egg(
            uid,
            egg_id
        )
        database.add_task_egg(
            uid
        )
        result = {
            'type':
                'egg',
            'egg': {
                'id':
                    egg_id,
                'name':
                    EGGS[egg_id][0],
                'rarity':
                    EGGS[egg_id][2]
            }
        }
    # =====================================================
    # OTHER REWARD
    # =====================================================
    else:
        roll = random.random()
        if roll < 0.65:
            amount = (
                random.randint(
                    20,
                    60
                )
                * (
                    chest_id + 1
                )
            )
            add_game_coins(
                uid,
                amount
            )
            result = {
                'type':
                    'coins',
                'amount':
                    amount
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
                'type':
                    'booster',
                'item': {
                    'id':
                        item_id,
                    'name':
                        ITEMS[item_id][0]
                }
            }
        else:
            amount = (
                random.randint(
                    20,
                    80
                )
                * chest_id
            )
            add_xp(
                uid,
                amount
            )
            result = {
                'type':
                    'xp',
                'amount':
                    amount
            }
    add_pass_xp(
        uid,
        10
    )
    return jsonify(
        ok=True,
        reward=
            result,
        data=
            snap(uid)
    )
# =========================================================
# PETS
# =========================================================
@app.get('/api/pets')
def api_pets():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    rows = database.get_player_pets(
        uid
    )
    owned = {}
    for row in rows:
        row = dict(
            row
        )
        pet_id = int(
            row.get(
                'pet_id',
                0
            )
        )
        owned[pet_id] = int(
            row.get(
                'active',
                0
            )
        )
    return jsonify(
        ok=True,
        pets={
            str(i): {
                'id':
                    i,
                'name':
                    pet[0],
                'rarity':
                    pet[1],
                'bonus':
                    pet[2],
                'owned':
                    i in owned,
                'active':
                    bool(
                        owned.get(
                            i,
                            0
                        )
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
    uid = int(
        u['id']
    )
    try:
        pet_id = int(
            (body() or {}).get(
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
    rows = database.get_player_pets(
        uid
    )
    owned = False
    player_pet_id = None
    for row in rows:
        row = dict(
            row
        )
        if int(
            row.get(
                'pet_id',
                0
            )
        ) == pet_id:
            owned = True
            player_pet_id = row.get(
                'id'
            )
            break
    if not owned:
        return json_error(
            'У тебя нет этого питомца.'
        )
    if player_pet_id is None:
        return json_error(
            'Не удалось определить питомца.'
        )
    database.set_active_pet(
        uid,
        int(player_pet_id)
    )
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
    rows = database.get_market_listings(
        limit=100
    )
    listings = []
    for row in rows:
        row = dict(
            row
        )
        egg_id = int(
            row['egg_id']
        )
        egg = EGGS.get(
            egg_id
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
            and search
            not in egg[0].lower()
        ):
            continue
        price = int(
            row['price']
        )
        listings.append({
            'id':
                row['id'],
            'seller_id':
                row['seller_id'],
            'egg_id':
                egg_id,
            'name':
                egg[0],
            'rarity':
                egg[2],
            'price':
                price,
            'fee':
                max(
                    1,
                    int(
                        price * 0.05
                    )
                ),
            'created_at':
                row.get(
                    'created_at'
                )
        })
    return jsonify(
        ok=True,
        listings=
            listings
    )
# =========================================================
# MARKET LIST
# =========================================================
@app.post('/api/market/list')
def api_market_list():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    data = body() or {}
    try:
        egg_id = int(
            data.get(
                'egg_id'
            )
        )
        price = int(
            data.get(
                'price'
            )
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
    try:
        listing_id = (
            database.create_market_listing(
                uid,
                egg_id,
                price
            )
        )
    except Exception as error:
        return json_error(
            str(error)
        )
    return jsonify(
        ok=True,
        listing_id=
            listing_id,
        data=
            snap(uid)
    )
# =========================================================
# MARKET BUY
# =========================================================
@app.post('/api/market/buy')
def api_market_buy():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    try:
        listing_id = int(
            (body() or {}).get(
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
    try:
        result = (
            database.buy_market_listing(
                uid,
                listing_id
            )
        )
    except Exception as error:
        return json_error(
            str(error)
        )
    if not result:
        return json_error(
            'Не удалось купить лот.'
        )
    egg_id = int(
        result['egg_id']
    )
    database.add_task_egg(
        uid
    )
    add_pass_xp(
        uid,
        15
    )
    return jsonify(
        ok=True,
        bought={
            'egg_id':
                egg_id,
            'name':
                EGGS[egg_id][0],
            'price':
                int(
                    result['price']
                )
        },
        fee=
            int(
                result['fee']
            ),
        seller_reward=
            int(
                result['seller_reward']
            ),
        data=
            snap(uid)
    )
# =========================================================
# MARKET CANCEL
# =========================================================
@app.post('/api/market/cancel')
def api_market_cancel():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    try:
        listing_id = int(
            (body() or {}).get(
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
    try:
        success = (
            database.cancel_market_listing(
                uid,
                listing_id
            )
        )
    except Exception as error:
        return json_error(
            str(error)
        )
    if not success:
        return json_error(
            'Лот не найден.'
        )
    return jsonify(
        ok=True,
        data=snap(uid)
    )
# =========================================================
# BOSS
# =========================================================
def boss_is_finished(boss, now=None):
    now = int(now or time.time())
    return (
        int(boss['current_hp']) <= 0
        or int(boss['ends_at']) <= now
        or int(boss['active']) == 0
    )
def boss_reward_amount(damage):
    return min(
        500,
        max(
            50,
            int(damage) // 2
        )
    )
def get_boss():
    """
    Возвращает текущего босса. Когда босс побеждён или время
    вышло и окно получения наград (BOSS_CLAIM_WINDOW) прошло -
    автоматически запускается следующий.
    """
    with BOSS_LOCK:
        boss = database.get_boss_event()
        now = int(time.time())
        if not boss:
            database.start_boss_event(
                BOSS_NAMES[0],
                BOSS_MAX_HP,
                BOSS_DURATION
            )
            return database.get_boss_event()
        if (
            boss_is_finished(boss, now)
            and now >= int(boss['ends_at']) + BOSS_CLAIM_WINDOW
        ):
            others = [
                name for name in BOSS_NAMES
                if name != boss['boss_name']
            ] or BOSS_NAMES
            database.start_boss_event(
                random.choice(others),
                BOSS_MAX_HP,
                BOSS_DURATION
            )
            boss = database.get_boss_event()
        return boss
def boss_payload(uid, boss):
    now = int(time.time())
    finished = boss_is_finished(boss, now)
    hp = max(0, int(boss['current_hp']))
    my_damage = 0
    my_claimed = False
    board = []
    for row in database.get_boss_participants():
        row = dict(row)
        damage = int(row['damage'])
        if int(row['user_id']) == uid:
            my_damage = damage
            my_claimed = bool(row['reward_claimed'])
        if len(board) < 10:
            board.append({
                'name': row.get('username') or 'Игрок',
                'damage': damage,
                'me': int(row['user_id']) == uid
            })
    return {
        'name': boss['boss_name'],
        'hp': hp,
        'max_hp': int(boss['max_hp']),
        'ends_at': int(boss['ends_at']),
        'seconds_left': max(0, int(boss['ends_at']) - now),
        'finished': finished,
        'defeated': hp <= 0,
        'my_damage': my_damage,
        'reward_amount': boss_reward_amount(my_damage) if my_damage > 0 else 0,
        'reward_claimed': my_claimed,
        'reward_available': (
            finished and my_damage > 0 and not my_claimed
        ),
        'next_boss_in': (
            max(0, int(boss['ends_at']) + BOSS_CLAIM_WINDOW - now)
            if finished else 0
        ),
        'leaderboard': board
    }
@app.get('/api/boss')
def api_boss():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    boss = get_boss()
    return jsonify(
        ok=True,
        **boss_payload(uid, boss)
    )
@app.post('/api/boss/attack')
def api_boss_attack():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    now = time.time()
    if now - last_boss.get(uid, 0) < 0.7:
        return json_error(
            'Подожди немного.',
            429
        )
    boss = get_boss()
    if int(boss['current_hp']) <= 0:
        return json_error(
            'Босс уже побеждён.'
        )
    if boss_is_finished(boss, now):
        return json_error(
            'Событие босса завершено.'
        )
    last_boss[uid] = now
    actual_damage = int(
        database.damage_boss(
            uid,
            random.randint(20, 60)
        ) or 0
    )
    if not actual_damage:
        return json_error(
            'Не удалось нанести урон.'
        )
    boss = database.get_boss_event()
    hp = max(
        0,
        int(boss['current_hp'])
    )
    add_pass_xp(
        uid,
        max(1, actual_damage // 5)
    )
    add_xp(
        uid,
        max(1, actual_damage // 5)
    )
    return jsonify(
        ok=True,
        damage=actual_damage,
        hp=hp,
        max_hp=int(boss['max_hp']),
        defeated=hp <= 0,
        my_damage=int(
            database.get_boss_damage(uid)
        ),
        data=snap(uid),
        new_achievements=achievements(uid)
    )
@app.post('/api/boss/reward')
def api_boss_reward():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    get_boss()
    result = database.claim_boss_reward(
        uid
    )
    if not result:
        return json_error(
            'Награда недоступна.'
        )
    damage = int(
        result.get('damage', 0)
    )
    reward = boss_reward_amount(
        damage
    )
    database.add_egg_coins(
        uid,
        reward
    )
    add_xp(
        uid,
        50
    )
    return jsonify(
        ok=True,
        reward=reward,
        damage=damage,
        data=snap(uid)
    )
# =========================================================
# EGG PASS
# =========================================================
def pass_reward(level, track):
    if track == 'free':
        return 20 + level * 5
    return 50 + level * 10
PASS_XP_SOURCES = [
    {'text': '👆 Тап по яйцу', 'xp': '1'},
    {'text': '🔢 Угадай число', 'xp': '10 (победа) / 5'},
    {'text': '🧠 Математика (верный ответ)', 'xp': '10'},
    {'text': '❌⭕ Крестики-нолики', 'xp': '15 / 10 / 5'},
    {'text': '🎁 Покупка и открытие сундука', 'xp': '10 + 10'},
    {'text': '🏪 Покупка на рынке', 'xp': '15'},
    {'text': '🥷 Успешная кража яйца', 'xp': '25'},
    {'text': '👾 Атака босса', 'xp': 'урон / 5'}
]
@app.get('/api/egg-pass')
def api_pass():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    database.ensure_egg_pass(
        uid
    )
    state = database.get_egg_pass(
        uid
    )
    if not state:
        return json_error(
            'Не удалось загрузить Egg Pass.'
        )
    state = dict(
        state
    )
    xp = int(
        state.get('xp', 0)
    )
    level = int(
        state.get('level', 0)
    )
    premium = bool(
        state.get('premium', 0)
    )
    levels = []
    for lvl in range(
        1,
        PASS_MAX + 1
    ):
        levels.append({
            'level':
                lvl,
            'unlocked':
                lvl <= level,
            'free_reward':
                pass_reward(lvl, 'free'),
            'premium_reward':
                pass_reward(lvl, 'premium'),
            'free_claimed':
                bool(
                    database.has_egg_pass_reward(
                        uid,
                        lvl,
                        'free'
                    )
                ),
            'premium_claimed':
                bool(
                    database.has_egg_pass_reward(
                        uid,
                        lvl,
                        'premium'
                    )
                )
        })
    return jsonify(
        ok=True,
        xp=
            xp,
        level=
            level,
        premium=premium, premium_price=PREMIUM_PASS_PRICE, max_level=PASS_MAX,
        xp_per_level=
            PASS_XP,
        xp_in_level=
            0 if level >= PASS_MAX
            else xp % PASS_XP,
        sources=
            PASS_XP_SOURCES,
        levels=
            levels
    )
# =========================================================
# EGG PASS CLAIM
# =========================================================
@app.post('/api/egg-pass/claim')
def api_pass_claim():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    data = body() or {}
    try:
        level = int(
            data.get(
                'level'
            )
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
    state = database.get_egg_pass(
        uid
    )
    if not state:
        return json_error(
            'Egg Pass не найден.'
        )
    state = dict(
        state
    )
    current_level = int(
        state.get(
            'level',
            0
        )
    )
    if current_level < level:
        return json_error(
            'Этот уровень ещё не достигнут.'
        )
    if (
        track == 'premium'
        and not state.get(
            'premium',
            0
        )
    ):
        return json_error(
            'Premium Egg Pass не активирован.'
        )
    if database.has_egg_pass_reward(
        uid,
        level,
        track
    ):
        return json_error(
            'Награда уже получена.'
        )
    claimed = database.claim_egg_pass_reward(
        uid,
        level,
        track
    )
    if not claimed:
        return json_error(
            'Не удалось получить награду.'
        )
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
        reward=
            reward,
        data=
            snap(uid)
    )
# =========================================================
# EGG PASS CLAIM ALL
# =========================================================
@app.post('/api/egg-pass/claim-all')
def api_pass_claim_all():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    state = database.get_egg_pass(
        uid
    )
    if not state:
        return json_error(
            'Egg Pass не найден.'
        )
    state = dict(
        state
    )
    level = int(
        state.get('level', 0)
    )
    premium = bool(
        state.get('premium', 0)
    )
    total = 0
    count = 0
    for lvl in range(
        1,
        min(level, PASS_MAX) + 1
    ):
        tracks = ['free']
        if premium:
            tracks.append('premium')
        for track in tracks:
            if database.claim_egg_pass_reward(
                uid,
                lvl,
                track
            ):
                reward = pass_reward(
                    lvl,
                    track
                )
                database.add_egg_coins(
                    uid,
                    reward
                )
                total += reward
                count += 1
    if not count:
        return json_error(
            'Нет наград для получения.'
        )
    return jsonify(
        ok=True,
        reward=
            total,
        count=
            count,
        data=
            snap(uid)
    )
# =========================================================
# EGG PASS PREMIUM
# =========================================================
@app.post('/api/egg-pass/premium')
def api_pass_premium():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    if not PREMIUM_PASS_PRICE:
        return json_error(
            'Premium Egg Pass пока недоступен.'
        )
    status = database.buy_egg_pass_premium(
        uid,
        PREMIUM_PASS_PRICE
    )
    if status == 'already':
        return json_error(
            'Premium уже активен.'
        )
    if status == 'funds':
        return json_error(
            f'Недостаточно Egg Coins. '
            f'Нужно {PREMIUM_PASS_PRICE} 🥚.'
        )
    return jsonify(
        ok=True,
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
    uid = int(
        u['id']
    )
    result = []
    for player in database.get_steal_candidates(
        uid,
        30
    ):
        player_id = int(
            player['user_id']
        )
        result.append({
            'user_id':
                player_id,
            'username':
                player.get(
                    'username',
                    ''
                )
                or 'Игрок',
            'avatar':
                player.get(
                    'avatar'
                )
                or '🥚',
            'eggs':
                int(
                    player['eggs']
                ),
            'protected':
                bool(
                    database.is_egg_protected(
                        player_id
                    )
                )
        })
    return jsonify(
        ok=True,
        players=
            result[:20]
    )
# =========================================================
# STEAL
# =========================================================
@app.post('/api/steal')
def api_steal():
    u, f = auth()
    if f:
        return f
    uid = int(
        u['id']
    )
    data = body() or {}
    try:
        # Клиент шлёт victim_id, старая версия - target_id.
        target = int(
            data.get(
                'victim_id',
                data.get(
                    'target_id'
                )
            )
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
    if not database.get_player(
        target
    ):
        return json_error(
            'Игрок не найден.'
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
    if database.is_egg_protected(
        target
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
        '⚪ Обычное':
            55,
        '🟢 Необычное':
            48,
        '🔵 Редкое':
            40,
        '🟣 Эпическое':
            33,
        '🟡 Легендарное':
            27,
        '🔴 Мифическое':
            20,
        '💠 Божественное':
            12,
        '🌈 Секретное':
            5
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
    database.add_steal_attempt(
        uid,
        target,
        egg_id,
        success
    )
    if success:
        transferred = (
            database.transfer_stolen_egg(
                uid,
                target,
                egg_id
            )
        )
        if transferred:
            database.set_egg_protection(
                target,
                1800
            )
            add_pass_xp(
                uid,
                25
            )
            add_xp(
                uid,
                25
            )
            return jsonify(
                ok=True,
                success=True,
                egg={
                    'id':
                        egg_id,
                    'name':
                        EGGS[egg_id][0],
                    'rarity':
                        rarity
                },
                data=
                    snap(uid),
                new_achievements=
                    achievements(uid)
            )
    return jsonify(
        ok=True,
        success=False,
        message=(
            'Кража не удалась. '
            'Игрок заметил попытку.'
        ),
        data=
            snap(uid)
    )
# =========================================================
# START SERVER
# =========================================================
if __name__ == '__main__':
    database.init_database()
    # Админ-бот (панель управления) стартует в фоне, если заданы
    # ADMIN_BOT_TOKEN и ADMIN_IDS. Иначе игра работает как обычно.
    try:
        import admin_bot
        admin_bot.configure(
            EGGS,
            CHESTS,
            ITEMS,
            PETS
        )
        admin_bot.start_in_thread()
    except Exception as error:
        print(f'[admin_bot] не запущен: {error}')
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False
    )
