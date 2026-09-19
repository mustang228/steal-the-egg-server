import os
import time
import hmac
import hashlib
import json
import random
from datetime import date, datetime
from urllib.parse import parse_qsl

from flask import Flask, request, jsonify
from flask_cors import CORS

import database


# ============================================================
# НАСТРОЙКИ
# ============================================================

app = Flask(__name__)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PORT = int(os.getenv("PORT", "8080"))

WITHDRAWAL_BOT = "https://t.me/stealtheegg_vyvod_bot"


# ============================================================
# ЯЙЦА
# ============================================================

EGGS = {
    1: {
        "id": 1,
        "name": "Обычное яйцо",
        "price": 100,
        "emoji": "🥚"
    },
    2: {
        "id": 2,
        "name": "Серебряное яйцо",
        "price": 600,
        "emoji": "🥚"
    },
    3: {
        "id": 3,
        "name": "Золотое яйцо",
        "price": 700,
        "emoji": "🥚"
    },
    4: {
        "id": 4,
        "name": "Алмазное яйцо",
        "price": 800,
        "emoji": "💎"
    },
    5: {
        "id": 5,
        "name": "Огненное яйцо",
        "price": 900,
        "emoji": "🔥"
    },
    6: {
        "id": 6,
        "name": "Ледяное яйцо",
        "price": 1000,
        "emoji": "❄️"
    },
    7: {
        "id": 7,
        "name": "Космическое яйцо",
        "price": 1100,
        "emoji": "🌌"
    },
    8: {
        "id": 8,
        "name": "Королевское яйцо",
        "price": 1200,
        "emoji": "👑"
    },
    9: {
        "id": 9,
        "name": "Молниеносное яйцо",
        "price": 1300,
        "emoji": "⚡"
    },
    10: {
        "id": 10,
        "name": "Тёмное яйцо",
        "price": 1400,
        "emoji": "🌑"
    }
}


# ============================================================
# ПРЕДМЕТЫ
# ============================================================

ITEMS = {
    1: {
        "id": 1,
        "name": "Tap Booster",
        "description": "+2 Tap Coins за тап в течение 10 минут",
        "price": 150,
        "duration": 600
    },
    2: {
        "id": 2,
        "name": "Egg Coin Booster",
        "description": "+1 Egg Coin за награды в играх в течение 10 минут",
        "price": 250,
        "duration": 600
    },
    3: {
        "id": 3,
        "name": "XP Booster",
        "description": "2x XP в течение 10 минут",
        "price": 200,
        "duration": 600
    }
}


# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================

ACHIEVEMENTS = {
    1: {
        "id": 1,
        "name": "Первый тап",
        "description": "Сделать первый тап",
        "reward": 10
    },
    2: {
        "id": 2,
        "name": "100 тапов",
        "description": "Сделать 100 тапов",
        "reward": 25
    },
    3: {
        "id": 3,
        "name": "1000 тапов",
        "description": "Сделать 1000 тапов",
        "reward": 100
    },
    4: {
        "id": 4,
        "name": "Первое яйцо",
        "description": "Получить первое яйцо",
        "reward": 25
    },
    5: {
        "id": 5,
        "name": "Игрок",
        "description": "Сыграть 10 мини-игр",
        "reward": 50
    },
    6: {
        "id": 6,
        "name": "Уровень 5",
        "description": "Достичь 5 уровня",
        "reward": 100
    },
    7: {
        "id": 7,
        "name": "Коллекционер",
        "description": "Собрать 10 яиц",
        "reward": 150
    },
    8: {
        "id": 8,
        "name": "Босс",
        "description": "Нанести 1000 урона боссу",
        "reward": 200
    }
}


# ============================================================
# ВРЕМЕННЫЕ ДАННЫЕ ИГР
# ============================================================

active = {}

guess = {}
math = {}
tic = {}

last_tap = {}
last_game = {}
last_boss = {}

boss_hp = 10000


# ============================================================
# БАЗА
# ============================================================

try:
    database.init_database()
    print("Database initialized")
except Exception as e:
    print("Database initialization error:", e)


# ============================================================
# TELEGRAM AUTH
# ============================================================

def get_telegram_user():

    raw = request.headers.get(
        "X-Telegram-Init-Data",
        ""
    )

    if not raw:
        return None, "Открой Mini App через Telegram."

    if not BOT_TOKEN:
        return None, "На сервере не задан BOT_TOKEN."

    try:

        params = dict(
            parse_qsl(
                raw,
                keep_blank_values=True
            )
        )

        received_hash = params.pop(
            "hash",
            None
        )

        if not received_hash:
            return None, "Не найден Telegram hash."

        check_string = "\n".join(
            f"{key}={params[key]}"
            for key in sorted(params)
        )

        secret_key = hmac.new(
            b"WebAppData",
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
            return None, "Неверная Telegram авторизация."

        auth_date = int(
            params.get(
                "auth_date",
                "0"
            )
        )

        if time.time() - auth_date > 86400:
            return None, "Данные Telegram устарели."

        if "user" not in params:
            return None, "Не найден пользователь Telegram."

        telegram_user = json.loads(
            params["user"]
        )

        user_id = int(
            telegram_user["id"]
        )

        username = telegram_user.get(
            "username",
            ""
        )

        database.ensure_player(
            user_id,
            username
        )

        database.update_username(
            user_id,
            username
        )

        if database.is_blocked(user_id):
            return None, "Ваш аккаунт заблокирован."

        return telegram_user, None

    except Exception as e:

        print(
            "Telegram auth error:",
            repr(e)
        )

        return None, "Ошибка авторизации Telegram."


def auth():

    telegram_user, error = get_telegram_user()

    if error:
        return None, (
            jsonify({
                "ok": False,
                "error": error
            }),
            401
        )

    return telegram_user, None


# ============================================================
# ПРЕДМЕТЫ — ПРОВЕРКА АКТИВНОСТИ
# ============================================================

def item_key(user_id, item_id):

    return f"{user_id}:{item_id}"


def activate_item_memory(
    user_id,
    item_id,
    duration
):

    active[
        item_key(
            user_id,
            item_id
        )
    ] = time.time() + duration


def has_active_item(
    user_id,
    item_id
):

    key = item_key(
        user_id,
        item_id
    )

    expires = active.get(key)

    if not expires:
        return False

    if expires <= time.time():

        active.pop(
            key,
            None
        )

        return False

    return True


def item_expiry(
    user_id,
    item_id
):

    key = item_key(
        user_id,
        item_id
    )

    expires = active.get(key)

    if not expires:
        return None

    if expires <= time.time():

        active.pop(
            key,
            None
        )

        return None

    return int(expires)


# ============================================================
# XP
# ============================================================

def add_xp(
    user_id,
    amount
):

    if has_active_item(
        user_id,
        3
    ):
        amount *= 2

    database.add_xp(
        user_id,
        amount
    )


# ============================================================
# EGG COINS
# ============================================================

def add_egg_coins(
    user_id,
    amount
):

    if has_active_item(
        user_id,
        2
    ):
        amount += 1

    database.add_egg_coins(
        user_id,
        amount
    )


# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================

def check_achievement(
    user_id,
    achievement_id
):

    if database.has_achievement(
        user_id,
        achievement_id
    ):
        return False

    reward = ACHIEVEMENTS[
        achievement_id
    ]["reward"]

    database.add_achievement(
        user_id,
        achievement_id
    )

    database.add_egg_coins(
        user_id,
        reward
    )

    return True


def check_achievements(
    user_id
):

    unlocked = []

    tap_count = get_tap_count(user_id)
    game_count = get_game_count(user_id)
    eggs_count = database.get_total_eggs(user_id)
    boss_damage = database.get_boss_damage(user_id)
    xp_value, level = database.get_progress(
        user_id
    )

    if tap_count >= 1:
        if check_achievement(user_id, 1):
            unlocked.append(1)

    if tap_count >= 100:
        if check_achievement(user_id, 2):
            unlocked.append(2)

    if tap_count >= 1000:
        if check_achievement(user_id, 3):
            unlocked.append(3)

    if eggs_count >= 1:
        if check_achievement(user_id, 4):
            unlocked.append(4)

    if game_count >= 10:
        if check_achievement(user_id, 5):
            unlocked.append(5)

    if level >= 5:
        if check_achievement(user_id, 6):
            unlocked.append(6)

    if eggs_count >= 10:
        if check_achievement(user_id, 7):
            unlocked.append(7)

    if boss_damage >= 1000:
        if check_achievement(user_id, 8):
            unlocked.append(8)

    return unlocked


# ============================================================
# ЛОКАЛЬНЫЕ СЧЁТЧИКИ
# ============================================================

tap_counter = {}
game_counter = {}


def get_tap_count(user_id):

    return tap_counter.get(
        user_id,
        0
    )


def get_game_count(user_id):

    return game_counter.get(
        user_id,
        0
    )


# ============================================================
# СОСТОЯНИЕ ИГРОКА
# ============================================================

def snap(user_id):

    tap_coins, egg_coins = database.get_balance(
        user_id
    )

    xp_value, level = database.get_progress(
        user_id
    )

    streak, last_login = database.get_login_info(
        user_id
    )

    tasks = database.get_daily_tasks(
        user_id
    )

    # ВАЖНО:
    # database.get_daily_tasks() возвращает:
    #
    # tasks[0] = task_taps
    # tasks[1] = task_games
    # tasks[2] = task_eggs
    #
    # Никакого tasks[3] здесь нет.

    task_taps = tasks[0]
    task_games = tasks[1]
    task_eggs = tasks[2]

    eggs = database.get_player_eggs(
        user_id
    )

    achievements = database.get_achievements(
        user_id
    )

    active_items = []

    for item_id, item in ITEMS.items():

        expires = item_expiry(
            user_id,
            item_id
        )

        if expires:

            active_items.append({
                "id": item_id,
                "name": item["name"],
                "expires": expires,
                "remaining": max(
                    0,
                    expires - int(time.time())
                )
            })

    tasks_data = {
        "taps": task_taps,
        "games": task_games,
        "eggs": task_eggs,

        "tap_target": 100,
        "games_target": 5,
        "eggs_target": 3,

        "tap_claimed": False,
        "games_claimed": False,
        "eggs_claimed": False
    }

    return {
        "tap_coins": tap_coins,
        "egg_coins": egg_coins,

        "xp": xp_value,
        "level": level,

        "xp_required": level * 100,

        "streak": streak,
        "last_login": last_login,

        "eggs_total": len(eggs),

        "eggs": eggs,

        "achievements": achievements,

        "active_items": active_items,

        "tasks": tasks_data,

        "tap_count": get_tap_count(user_id),
        "game_count": get_game_count(user_id),

        "boss_damage": database.get_boss_damage(
            user_id
        )
    }


# ============================================================
# ГЛАВНАЯ
# ============================================================

@app.route("/", methods=["GET"])
def index():

    return jsonify({
        "ok": True,
        "message": "STEAL THE EGG server is running!"
    })


# ============================================================
# INIT
# ============================================================

@app.route(
    "/api/init",
    methods=["POST"]
)
def init():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    streak = database.update_login(
        uid
    )

    check_achievements(uid)

    return jsonify({
        "ok": True,
        "user": user_data,
        "data": snap(uid)
    })


# ============================================================
# STATE
# ============================================================

@app.route(
    "/api/state",
    methods=["GET"]
)
def state():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    return jsonify({
        "ok": True,
        "data": snap(uid)
    })


# ============================================================
# TAP
# ============================================================

@app.route(
    "/api/tap",
    methods=["POST"]
)
def tap():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    now = time.time()

    previous = last_tap.get(
        uid,
        0
    )

    # Защита от слишком быстрых запросов
    if now - previous < 0.03:
        return jsonify({
            "ok": False,
            "error": "Слишком быстро."
        }), 429

    last_tap[uid] = now

    amount = 1

    # Tap Booster = +2
    if has_active_item(
        uid,
        1
    ):
        amount += 2

    database.add_tap_coins(
        uid,
        amount
    )

    database.add_task_tap(
        uid
    )

    add_xp(
        uid,
        1
    )

    tap_counter[uid] = (
        tap_counter.get(uid, 0)
        + 1
    )

    check_achievements(uid)

    return jsonify({
        "ok": True,
        "reward": amount,
        "data": snap(uid)
    })


# ============================================================
# ОБМЕН TAP COINS → EGG COINS
# ============================================================

@app.route(
    "/api/exchange",
    methods=["POST"]
)
def exchange():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    # 1000 Tap Coins = 10 Egg Coins

    success = database.remove_tap_coins(
        uid,
        1000
    )

    if not success:

        return jsonify({
            "ok": False,
            "error": "Недостаточно Tap Coins. Нужно 1000."
        }), 400

    database.add_egg_coins(
        uid,
        10
    )

    add_xp(
        uid,
        5
    )

    return jsonify({
        "ok": True,
        "tap_coins_spent": 1000,
        "egg_coins_received": 10,
        "data": snap(uid)
    })


# ============================================================
# ИГРА — УГАДАЙ ЧИСЛО
# ============================================================

@app.route(
    "/api/game/guess/start",
    methods=["POST"]
)
def guess_start():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    guess[uid] = random.randint(
        1,
        10
    )

    return jsonify({
        "ok": True,
        "min": 1,
        "max": 10
    })


@app.route(
    "/api/game/guess/answer",
    methods=["POST"]
)
def guess_answer():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    data = request.get_json(
        silent=True
    ) or {}

    try:
        answer = int(
            data.get("answer")
        )
    except:
        return jsonify({
            "ok": False,
            "error": "Введите число."
        }), 400

    if uid not in guess:

        return jsonify({
            "ok": False,
            "error": "Сначала начните игру."
        }), 400

    correct = guess.pop(uid)

    game_counter[uid] = (
        game_counter.get(uid, 0)
        + 1
    )

    database.add_task_game(
        uid
    )

    if answer == correct:

        reward = 10

        add_egg_coins(
            uid,
            reward
        )

        add_xp(
            uid,
            10
        )

        check_achievements(uid)

        return jsonify({
            "ok": True,
            "correct": True,
            "number": correct,
            "reward": reward,
            "data": snap(uid)
        })

    add_xp(
        uid,
        2
    )

    check_achievements(uid)

    return jsonify({
        "ok": True,
        "correct": False,
        "number": correct,
        "reward": 0,
        "data": snap(uid)
    })


# ============================================================
# ИГРА — МАТЕМАТИКА
# ============================================================

@app.route(
    "/api/game/math/start",
    methods=["POST"]
)
def math_start():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    a = random.randint(
        1,
        20
    )

    b = random.randint(
        1,
        20
    )

    operation = random.choice([
        "+",
        "-"
    ])

    if operation == "+":
        answer = a + b

    else:
        answer = a - b

    math[uid] = answer

    return jsonify({
        "ok": True,
        "a": a,
        "b": b,
        "operation": operation,
        "question": f"{a} {operation} {b}"
    })


@app.route(
    "/api/game/math/answer",
    methods=["POST"]
)
def math_answer():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    data = request.get_json(
        silent=True
    ) or {}

    try:
        answer = int(
            data.get("answer")
        )
    except:

        return jsonify({
            "ok": False,
            "error": "Введите число."
        }), 400

    if uid not in math:

        return jsonify({
            "ok": False,
            "error": "Сначала начните игру."
        }), 400

    correct = math.pop(uid)

    game_counter[uid] = (
        game_counter.get(uid, 0)
        + 1
    )

    database.add_task_game(
        uid
    )

    if answer == correct:

        reward = 15

        add_egg_coins(
            uid,
            reward
        )

        add_xp(
            uid,
            15
        )

        check_achievements(uid)

        return jsonify({
            "ok": True,
            "correct": True,
            "answer": correct,
            "reward": reward,
            "data": snap(uid)
        })

    add_xp(
        uid,
        2
    )

    check_achievements(uid)

    return jsonify({
        "ok": True,
        "correct": False,
        "answer": correct,
        "reward": 0,
        "data": snap(uid)
    })


# ============================================================
# ИГРА — КРЕСТИКИ-НОЛИКИ
# ============================================================

def tic_winner(board):

    combinations = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],

        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],

        [0, 4, 8],
        [2, 4, 6]
    ]

    for combo in combinations:

        a, b, c = combo

        if (
            board[a] != ""
            and board[a] == board[b]
            and board[b] == board[c]
        ):
            return board[a]

    if all(
        cell != ""
        for cell in board
    ):
        return "draw"

    return None


def tic_bot_move(board):

    free = [
        i
        for i, cell in enumerate(board)
        if cell == ""
    ]

    if not free:
        return None

    # Попробовать выиграть
    for position in free:

        test = board.copy()

        test[position] = "O"

        if tic_winner(test) == "O":
            return position

    # Попробовать заблокировать игрока
    for position in free:

        test = board.copy()

        test[position] = "X"

        if tic_winner(test) == "X":
            return position

    return random.choice(
        free
    )


@app.route(
    "/api/game/tic/start",
    methods=["POST"]
)
def tic_start():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    board = [
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        ""
    ]

    tic[uid] = board

    return jsonify({
        "ok": True,
        "board": board
    })


@app.route(
    "/api/game/tic/move",
    methods=["POST"]
)
def tic_move():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    if uid not in tic:

        return jsonify({
            "ok": False,
            "error": "Сначала начните игру."
        }), 400

    data = request.get_json(
        silent=True
    ) or {}

    try:
        position = int(
            data.get("position")
        )
    except:

        return jsonify({
            "ok": False,
            "error": "Неверная клетка."
        }), 400

    board = tic[uid]

    if position < 0 or position > 8:

        return jsonify({
            "ok": False,
            "error": "Неверная клетка."
        }), 400

    if board[position] != "":

        return jsonify({
            "ok": False,
            "error": "Клетка уже занята."
        }), 400

    board[position] = "X"

    winner = tic_winner(board)

    if winner:

        tic.pop(
            uid,
            None
        )

        game_counter[uid] = (
            game_counter.get(uid, 0)
            + 1
        )

        database.add_task_game(
            uid
        )

        if winner == "X":

            reward = 20

            add_egg_coins(
                uid,
                reward
            )

            add_xp(
                uid,
                20
            )

        else:

            reward = 5

            add_egg_coins(
                uid,
                reward
            )

            add_xp(
                uid,
                5
            )

        check_achievements(uid)

        return jsonify({
            "ok": True,
            "board": board,
            "winner": winner,
            "reward": reward,
            "data": snap(uid)
        })

    bot_position = tic_bot_move(
        board
    )

    if bot_position is not None:

        board[bot_position] = "O"

    winner = tic_winner(
        board
    )

    if winner:

        tic.pop(
            uid,
            None
        )

        game_counter[uid] = (
            game_counter.get(uid, 0)
            + 1
        )

        database.add_task_game(
            uid
        )

        if winner == "draw":

            reward = 3

        else:

            reward = 0

        if reward:

            add_egg_coins(
                uid,
                reward
            )

        add_xp(
            uid,
            3
        )

        check_achievements(uid)

        return jsonify({
            "ok": True,
            "board": board,
            "winner": winner,
            "reward": reward,
            "data": snap(uid)
        })

    return jsonify({
        "ok": True,
        "board": board,
        "winner": None,
        "reward": 0,
        "data": snap(uid)
    })


# ============================================================
# ЯЙЦА — СПИСОК
# ============================================================

@app.route(
    "/api/eggs",
    methods=["GET"]
)
def eggs():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    owned = database.get_player_eggs(
        uid
    )

    result = []

    for egg_id, egg in EGGS.items():

        result.append({
            **egg,
            "owned": owned.count(
                egg_id
            )
        })

    return jsonify({
        "ok": True,
        "eggs": result
    })


# ============================================================
# КУПИТЬ ЯЙЦО
# ============================================================

@app.route(
    "/api/eggs/buy",
    methods=["POST"]
)
def buy_egg():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    data = request.get_json(
        silent=True
    ) or {}

    try:
        egg_id = int(
            data.get("egg_id")
        )
    except:

        return jsonify({
            "ok": False,
            "error": "Неверный egg_id."
        }), 400

    egg = EGGS.get(
        egg_id
    )

    if not egg:

        return jsonify({
            "ok": False,
            "error": "Такого яйца нет."
        }), 404

    success = database.remove_egg_coins(
        uid,
        egg["price"]
    )

    if not success:

        return jsonify({
            "ok": False,
            "error": "Недостаточно Egg Coins."
        }), 400

    database.add_egg(
        uid,
        egg_id
    )

    database.add_task_egg(
        uid
    )

    add_xp(
        uid,
        10
    )

    check_achievements(uid)

    return jsonify({
        "ok": True,
        "egg": egg,
        "data": snap(uid)
    })


# ============================================================
# ПРЕДМЕТЫ
# ============================================================

@app.route(
    "/api/items",
    methods=["GET"]
)
def items():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    result = []

    for item_id, item in ITEMS.items():

        result.append({
            **item,
            "owned": database.get_item_count(
                uid,
                item_id
            ),
            "active": has_active_item(
                uid,
                item_id
            ),
            "expires": item_expiry(
                uid,
                item_id
            )
        })

    return jsonify({
        "ok": True,
        "items": result
    })


# ============================================================
# КУПИТЬ ПРЕДМЕТ
# ============================================================

@app.route(
    "/api/items/buy",
    methods=["POST"]
)
def buy_item():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    data = request.get_json(
        silent=True
    ) or {}

    try:
        item_id = int(
            data.get("item_id")
        )
    except:

        return jsonify({
            "ok": False,
            "error": "Неверный item_id."
        }), 400

    item = ITEMS.get(
        item_id
    )

    if not item:

        return jsonify({
            "ok": False,
            "error": "Такого предмета нет."
        }), 404

    success = database.remove_egg_coins(
        uid,
        item["price"]
    )

    if not success:

        return jsonify({
            "ok": False,
            "error": "Недостаточно Egg Coins."
        }), 400

    database.add_item(
        uid,
        item_id
    )

    return jsonify({
        "ok": True,
        "item": item,
        "data": snap(uid)
    })


# ============================================================
# АКТИВИРОВАТЬ ПРЕДМЕТ
# ============================================================

@app.route(
    "/api/items/activate",
    methods=["POST"]
)
def activate_item():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    data = request.get_json(
        silent=True
    ) or {}

    try:
        item_id = int(
            data.get("item_id")
        )
    except:

        return jsonify({
            "ok": False,
            "error": "Неверный item_id."
        }), 400

    item = ITEMS.get(
        item_id
    )

    if not item:

        return jsonify({
            "ok": False,
            "error": "Такого предмета нет."
        }), 404

    if has_active_item(
        uid,
        item_id
    ):

        return jsonify({
            "ok": False,
            "error": "Этот предмет уже активен."
        }), 400

    success = database.remove_item(
        uid,
        item_id
    )

    if not success:

        return jsonify({
            "ok": False,
            "error": "У вас нет этого предмета."
        }), 400

    activate_item_memory(
        uid,
        item_id,
        item["duration"]
    )

    return jsonify({
        "ok": True,
        "item": item,
        "expires": item_expiry(
            uid,
            item_id
        ),
        "data": snap(uid)
    })


# ============================================================
# ДОСТИЖЕНИЯ
# ============================================================

@app.route(
    "/api/achievements",
    methods=["GET"]
)
def achievements():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    check_achievements(uid)

    owned = database.get_achievements(
        uid
    )

    result = []

    for achievement_id, achievement in ACHIEVEMENTS.items():

        result.append({
            **achievement,
            "unlocked": achievement_id in owned
        })

    return jsonify({
        "ok": True,
        "achievements": result
    })


# ============================================================
# ЛИДЕРБОРД
# ============================================================

@app.route(
    "/api/leaderboard",
    methods=["GET"]
)
def leaderboard():

    user_data, error = auth()

    if error:
        return error

    players = database.get_top_players(
        10
    )

    result = []

    for index, player in enumerate(
        players,
        start=1
    ):

        user_id = player[0]
        username = player[1]
        egg_coins = player[2]
        tap_coins = player[3]
        level = player[4]

        result.append({
            "place": index,
            "user_id": user_id,
            "username": username or "Игрок",
            "egg_coins": egg_coins,
            "tap_coins": tap_coins,
            "level": level
        })

    return jsonify({
        "ok": True,
        "players": result
    })


# ============================================================
# ЕЖЕДНЕВНЫЙ БОНУС
# ============================================================

@app.route(
    "/api/daily/bonus",
    methods=["POST"]
)
def daily_bonus():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    today = date.today().isoformat()

    claimed = database.get_daily_bonus_date(
        uid
    )

    if claimed == today:

        return jsonify({
            "ok": False,
            "error": "Бонус уже получен сегодня."
        }), 400

    database.set_daily_bonus_date(
        uid
    )

    reward = 25

    add_egg_coins(
        uid,
        reward
    )

    add_xp(
        uid,
        10
    )

    return jsonify({
        "ok": True,
        "reward": reward,
        "data": snap(uid)
    })


# ============================================================
# ЕЖЕДНЕВНЫЕ ЗАДАНИЯ
# ============================================================

@app.route(
    "/api/daily/tasks",
    methods=["GET"]
)
def daily_tasks():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    tasks = database.get_daily_tasks(
        uid
    )

    return jsonify({
        "ok": True,
        "tasks": {
            "taps": tasks[0],
            "games": tasks[1],
            "eggs": tasks[2],

            "tap_target": 100,
            "games_target": 5,
            "eggs_target": 3
        }
    })


@app.route(
    "/api/daily/tasks/claim",
    methods=["POST"]
)
def claim_daily_task():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    data = request.get_json(
        silent=True
    ) or {}

    task_type = data.get(
        "type"
    )

    tasks = database.get_daily_tasks(
        uid
    )

    reward = 0

    if task_type == "taps":

        if tasks[0] < 100:

            return jsonify({
                "ok": False,
                "error": "Задание ещё не выполнено."
            }), 400

        reward = 10

    elif task_type == "games":

        if tasks[1] < 5:

            return jsonify({
                "ok": False,
                "error": "Задание ещё не выполнено."
            }), 400

        reward = 15

    elif task_type == "eggs":

        if tasks[2] < 3:

            return jsonify({
                "ok": False,
                "error": "Задание ещё не выполнено."
            }), 400

        reward = 20

    else:

        return jsonify({
            "ok": False,
            "error": "Неизвестное задание."
        }), 400

    add_egg_coins(
        uid,
        reward
    )

    add_xp(
        uid,
        10
    )

    return jsonify({
        "ok": True,
        "reward": reward,
        "data": snap(uid)
    })


# ============================================================
# БОСС
# ============================================================

@app.route(
    "/api/boss",
    methods=["GET"]
)
def boss():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    global boss_hp

    return jsonify({
        "ok": True,
        "hp": boss_hp,
        "max_hp": 10000,
        "my_damage": database.get_boss_damage(
            uid
        )
    })


@app.route(
    "/api/boss/attack",
    methods=["POST"]
)
def boss_attack():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    global boss_hp

    now = time.time()

    previous = last_boss.get(
        uid,
        0
    )

    if now - previous < 0.3:

        return jsonify({
            "ok": False,
            "error": "Слишком быстро."
        }), 429

    last_boss[uid] = now

    if boss_hp <= 0:

        return jsonify({
            "ok": False,
            "error": "Босс уже побеждён."
        }), 400

    damage = random.randint(
        5,
        15
    )

    boss_hp = max(
        0,
        boss_hp - damage
    )

    database.add_boss_damage(
        uid,
        damage
    )

    add_xp(
        uid,
        damage
    )

    reward = 0

    if boss_hp == 0:

        reward = 100

        add_egg_coins(
            uid,
            reward
        )

    check_achievements(uid)

    return jsonify({
        "ok": True,
        "damage": damage,
        "hp": boss_hp,
        "max_hp": 10000,
        "reward": reward,
        "data": snap(uid)
    })


# ============================================================
# ВЫВОД
# ============================================================

@app.route(
    "/api/withdrawal",
    methods=["GET"]
)
def withdrawal():

    user_data, error = auth()

    if error:
        return error

    uid = int(
        user_data["id"]
    )

    tap_coins, egg_coins = database.get_balance(
        uid
    )

    return jsonify({
        "ok": True,
        "bot": WITHDRAWAL_BOT,
        "egg_coins": egg_coins,
        "tap_coins": tap_coins
    })


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":

    print(
        "BOT_TOKEN задан:",
        bool(BOT_TOKEN)
    )

    print(
        "Длина BOT_TOKEN:",
        len(BOT_TOKEN)
    )

    print(
        f"Server starting on port {PORT}"
    )

    app.run(
        host="0.0.0.0",
        port=PORT
    )
