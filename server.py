import os
import time
import hmac
import hashlib
import json
import random

from flask import Flask, request, jsonify
from flask_cors import CORS

import database


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)
CORS(app)


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

PORT = int(os.getenv("PORT", "10000"))

WITHDRAWAL_BOT = "https://t.me/stealtheegg_vyvod_bot"


# =========================================================
# EGGS
# =========================================================

EGGS = {
    1: {
        "name": "Обычное яйцо",
        "price": 100
    },

    2: {
        "name": "Серебряное яйцо",
        "price": 600
    },

    3: {
        "name": "Золотое яйцо",
        "price": 700
    },

    4: {
        "name": "Алмазное яйцо",
        "price": 800
    },

    5: {
        "name": "Огненное яйцо",
        "price": 900
    },

    6: {
        "name": "Ледяное яйцо",
        "price": 1000
    },

    7: {
        "name": "Космическое яйцо",
        "price": 1100
    },

    8: {
        "name": "Королевское яйцо",
        "price": 1200
    },

    9: {
        "name": "Молниеносное яйцо",
        "price": 1300
    },

    10: {
        "name": "Тёмное яйцо",
        "price": 1400
    }
}


# =========================================================
# ITEMS
# =========================================================

ITEMS = {
    1: {
        "name": "Tap Booster",
        "description": "+2 Tap Coins за тап",
        "price": 150,
        "duration": 600
    },

    2: {
        "name": "Egg Coin Booster",
        "description": "+1 Egg Coin за награды мини-игр",
        "price": 250,
        "duration": 600
    },

    3: {
        "name": "XP Booster",
        "description": "2x XP",
        "price": 200,
        "duration": 600
    }
}


# =========================================================
# ACHIEVEMENTS
# =========================================================

ACHIEVEMENTS = {
    1: {
        "name": "Первый тап",
        "description": "Сделать первый тап",
        "reward": 10
    },

    2: {
        "name": "100 тапов",
        "description": "Сделать 100 тапов",
        "reward": 25
    },

    3: {
        "name": "1000 тапов",
        "description": "Сделать 1000 тапов",
        "reward": 100
    },

    4: {
        "name": "Первое яйцо",
        "description": "Получить первое яйцо",
        "reward": 25
    },

    5: {
        "name": "Игрок",
        "description": "Сыграть 10 мини-игр",
        "reward": 50
    },

    6: {
        "name": "Уровень 5",
        "description": "Достичь 5 уровня",
        "reward": 100
    },

    7: {
        "name": "Коллекционер",
        "description": "Получить 10 яиц",
        "reward": 150
    },

    8: {
        "name": "Босс",
        "description": "Нанести 1000 урона боссу",
        "reward": 200
    }
}


# =========================================================
# GAMES
# =========================================================

active = {}

guess_games = {}
math_games = {}
tic_games = {}

last_tap = {}
last_game = {}
last_boss = {}

# активные предметы
active_items = {}

# счётчики за текущую жизнь процесса
# основные данные всё равно сохраняются через БД
tap_counter = {}
game_counter = {}

# Босс
BOSS_MAX_HP = 10000
boss_hp = BOSS_MAX_HP


# =========================================================
# DATABASE
# =========================================================

database.init_database()


# =========================================================
# TELEGRAM AUTH
# =========================================================

def validate_telegram_data(init_data):
    if not init_data:
        return None

    if not BOT_TOKEN:
        return None

    try:
        from urllib.parse import parse_qsl

        data = dict(parse_qsl(init_data, keep_blank_values=True))

        received_hash = data.pop("hash", None)

        if not received_hash:
            return None

        auth_date = int(data.get("auth_date", 0))

        # максимум сутки
        if time.time() - auth_date > 86400:
            return None

        data_check_string = "\n".join(
            f"{key}={data[key]}"
            for key in sorted(data.keys())
        )

        secret_key = hmac.new(
            b"WebAppData",
            BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        user_json = data.get("user")

        if not user_json:
            return None

        user = json.loads(user_json)

        return user

    except Exception as e:
        print("Telegram auth error:", e)
        return None


# =========================================================
# CURRENT USER
# =========================================================

def get_current_user():
    init_data = request.headers.get(
        "X-Telegram-Init-Data",
        ""
    )

    user = validate_telegram_data(init_data)

    if not user:
        return None

    user_id = int(user["id"])

    username = user.get("username", "")

    database.ensure_player(
        user_id,
        username
    )

    if database.is_blocked(user_id):
        return None

    return user


# =========================================================
# HELPERS
# =========================================================

def require_user():
    user = get_current_user()

    if not user:
        return None

    return user


def uid_from_user(user):
    return int(user["id"])


def get_username(user):
    return (
        user.get("username")
        or user.get("first_name")
        or "Игрок"
    )


# =========================================================
# ITEM SYSTEM
# =========================================================

def activate_item(user_id, item_id):
    if item_id not in ITEMS:
        return False, "Предмет не найден"

    if database.get_item_count(
        user_id,
        item_id
    ) <= 0:
        return False, "У тебя нет этого предмета"

    if not database.remove_item(
        user_id,
        item_id
    ):
        return False, "Не удалось использовать предмет"

    active_items.setdefault(
        user_id,
        {}
    )

    active_items[user_id][item_id] = (
        time.time() + ITEMS[item_id]["duration"]
    )

    return True, "Предмет активирован"


def is_item_active(user_id, item_id):
    user_items = active_items.get(
        user_id,
        {}
    )

    expires = user_items.get(item_id)

    if not expires:
        return False

    if time.time() >= expires:
        del user_items[item_id]
        return False

    return True


# =========================================================
# XP
# =========================================================

def give_xp(user_id, amount):
    if is_item_active(user_id, 3):
        amount *= 2

    return database.add_xp(
        user_id,
        amount
    )


# =========================================================
# GAME REWARD
# =========================================================

def give_game_reward(user_id, egg_coins):
    if is_item_active(user_id, 2):
        egg_coins += 1

    database.add_egg_coins(
        user_id,
        egg_coins
    )

    give_xp(
        user_id,
        10
    )


# =========================================================
# ACHIEVEMENTS
# =========================================================

def check_achievements(user_id):
    rewards = []

    taps = tap_counter.get(
        user_id,
        0
    )

    games = game_counter.get(
        user_id,
        0
    )

    total_eggs = database.get_total_eggs(
        user_id
    )

    xp, level = database.get_progress(
        user_id
    )

    boss_damage = database.get_boss_damage(
        user_id
    )

    checks = [
        (
            1,
            taps >= 1
        ),

        (
            2,
            taps >= 100
        ),

        (
            3,
            taps >= 1000
        ),

        (
            4,
            total_eggs >= 1
        ),

        (
            5,
            games >= 10
        ),

        (
            6,
            level >= 5
        ),

        (
            7,
            total_eggs >= 10
        ),

        (
            8,
            boss_damage >= 1000
        )
    ]

    for achievement_id, condition in checks:

        if condition and not database.has_achievement(
            user_id,
            achievement_id
        ):

            database.add_achievement(
                user_id,
                achievement_id
            )

            reward = ACHIEVEMENTS[
                achievement_id
            ]["reward"]

            database.add_egg_coins(
                user_id,
                reward
            )

            rewards.append({
                "id": achievement_id,
                "name": ACHIEVEMENTS[
                    achievement_id
                ]["name"],
                "reward": reward
            })

    return rewards


# =========================================================
# SNAPSHOT
# =========================================================

def snap(user_id):

    tap_coins, egg_coins = database.get_balance(
        user_id
    )

    xp, level = database.get_progress(
        user_id
    )

    streak, last_login = database.get_login_info(
        user_id
    )

    tasks = database.get_daily_tasks(
        user_id
    )

    task_taps = min(
        tasks[0],
        100
    )

    task_games = min(
        tasks[1],
        5
    )

    task_eggs = min(
        tasks[2],
        3
    )

    return {
        "tap_coins": tap_coins,
        "egg_coins": egg_coins,

        "xp": xp,
        "level": level,

        "streak": streak,

        "tasks": {
            "taps": task_taps,
            "games": task_games,
            "eggs": task_eggs,

            "tap_target": 100,
            "games_target": 5,
            "eggs_target": 3,

            "tap_claimed": database.has_daily_task_claim(
                user_id,
                "taps"
            ),

            "games_claimed": database.has_daily_task_claim(
                user_id,
                "games"
            ),

            "eggs_claimed": database.has_daily_task_claim(
                user_id,
                "eggs"
            )
        },

        "boss_damage": database.get_boss_damage(
            user_id
        ),

        "eggs": database.get_player_eggs(
            user_id
        ),

        "items": database.get_items(
            user_id
        ),

        "achievements": database.get_achievements(
            user_id
        )
    }


# =========================================================
# ROOT
# =========================================================

@app.route("/")
def index():
    return jsonify({
        "ok": True,
        "message": "STEAL THE EGG server is running!"
    })


# =========================================================
# INIT
# =========================================================

@app.route("/api/init", methods=["POST"])
def api_init():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    login = database.update_login(
        user_id
    )

    # Награда за ежедневный вход
    if login["claimed"]:
        database.add_egg_coins(
            user_id,
            login["reward"]
        )

    return jsonify({
        "ok": True,

        "user": {
            "id": user_id,
            "username": get_username(user)
        },

        "login": login,

        "data": snap(user_id)
    })


# =========================================================
# STATE
# =========================================================

@app.route("/api/state", methods=["POST"])
def api_state():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    return jsonify({
        "ok": True,
        "data": snap(user_id)
    })


# =========================================================
# TAP
# =========================================================

@app.route("/api/tap", methods=["POST"])
def api_tap():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    now = time.time()

    # защита от слишком быстрых запросов
    if now - last_tap.get(user_id, 0) < 0.05:
        return jsonify({
            "ok": False,
            "error": "Too fast"
        }), 429

    last_tap[user_id] = now

    amount = 1

    if is_item_active(user_id, 1):
        amount += 2

    database.add_tap_coins(
        user_id,
        amount
    )

    database.add_task_tap(
        user_id,
        1
    )

    tap_counter[user_id] = (
        tap_counter.get(user_id, 0) + 1
    )

    achievements = check_achievements(
        user_id
    )

    return jsonify({
        "ok": True,
        "amount": amount,
        "achievements": achievements,
        "data": snap(user_id)
    })


# =========================================================
# EXCHANGE
# 1000 TAP COINS = 10 EGG COINS
# =========================================================

@app.route("/api/exchange", methods=["POST"])
def api_exchange():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    if not database.remove_tap_coins(
        user_id,
        1000
    ):
        return jsonify({
            "ok": False,
            "error": "Недостаточно Tap Coins"
        }), 400

    database.add_egg_coins(
        user_id,
        10
    )

    return jsonify({
        "ok": True,
        "tap_coins": database.get_balance(
            user_id
        )[0],
        "egg_coins": database.get_balance(
            user_id
        )[1],

        "data": snap(user_id)
    })


# =========================================================
# GUESS NUMBER
# =========================================================

@app.route("/api/game/guess/start", methods=["POST"])
def guess_start():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    number = random.randint(
        1,
        10
    )

    guess_games[user_id] = {
        "number": number,
        "attempts": 0
    }

    return jsonify({
        "ok": True,
        "min": 1,
        "max": 10,
        "attempts": 0
    })


@app.route("/api/game/guess/try", methods=["POST"])
def guess_try():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    game = guess_games.get(user_id)

    if not game:
        return jsonify({
            "ok": False,
            "error": "Игра не запущена"
        }), 400

    data = request.get_json(
        silent=True
    ) or {}

    try:
        number = int(
            data.get("number")
        )
    except:
        return jsonify({
            "ok": False,
            "error": "Введите число"
        }), 400

    game["attempts"] += 1

    target = game["number"]

    if number == target:

        reward = 10

        give_game_reward(
            user_id,
            reward
        )

        database.add_task_game(
            user_id,
            1
        )

        game_counter[user_id] = (
            game_counter.get(user_id, 0) + 1
        )

        achievements = check_achievements(
            user_id
        )

        del guess_games[user_id]

        return jsonify({
            "ok": True,
            "result": "win",
            "correct": True,
            "number": target,
            "reward": reward,
            "attempts": game["attempts"],
            "achievements": achievements,
            "data": snap(user_id)
        })

    if number < target:
        hint = "Больше"
    else:
        hint = "Меньше"

    return jsonify({
        "ok": True,
        "result": "continue",
        "correct": False,
        "hint": hint,
        "attempts": game["attempts"]
    })


# =========================================================
# MATH GAME
# =========================================================

@app.route("/api/game/math/start", methods=["POST"])
def math_start():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    a = random.randint(1, 20)
    b = random.randint(1, 20)

    operation = random.choice([
        "+",
        "-",
        "*"
    ])

    if operation == "+":
        answer = a + b

    elif operation == "-":
        answer = a - b

    else:
        answer = a * b

    math_games[user_id] = {
        "question": f"{a} {operation} {b}",
        "answer": answer
    }

    return jsonify({
        "ok": True,
        "question": math_games[user_id]["question"]
    })


@app.route("/api/game/math/answer", methods=["POST"])
def math_answer():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    game = math_games.get(user_id)

    if not game:
        return jsonify({
            "ok": False,
            "error": "Игра не запущена"
        }), 400

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
            "error": "Введите число"
        }), 400

    correct_answer = game["answer"]

    del math_games[user_id]

    if answer != correct_answer:

        return jsonify({
            "ok": True,
            "result": "lose",
            "correct": False,
            "answer": correct_answer
        })

    reward = 10

    give_game_reward(
        user_id,
        reward
    )

    database.add_task_game(
        user_id,
        1
    )

    game_counter[user_id] = (
        game_counter.get(user_id, 0) + 1
    )

    achievements = check_achievements(
        user_id
    )

    return jsonify({
        "ok": True,
        "result": "win",
        "correct": True,
        "answer": correct_answer,
        "reward": reward,
        "achievements": achievements,
        "data": snap(user_id)
    })


# =========================================================
# TIC TAC TOE
# =========================================================

@app.route("/api/game/tic/start", methods=["POST"])
def tic_start():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    tic_games[user_id] = {
        "board": [
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
    }

    return jsonify({
        "ok": True,
        "board": tic_games[user_id]["board"]
    })


def check_tic_winner(board):

    combinations = [
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),

        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),

        (0, 4, 8),
        (2, 4, 6)
    ]

    for a, b, c in combinations:

        if (
            board[a]
            and board[a] == board[b]
            and board[b] == board[c]
        ):
            return board[a]

    if all(board[i] for i in range(9)):
        return "draw"

    return None


@app.route("/api/game/tic/move", methods=["POST"])
def tic_move():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    game = tic_games.get(user_id)

    if not game:
        return jsonify({
            "ok": False,
            "error": "Игра не запущена"
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
            "error": "Неверная клетка"
        }), 400

    if position < 0 or position > 8:
        return jsonify({
            "ok": False,
            "error": "Неверная клетка"
        }), 400

    board = game["board"]

    if board[position]:
        return jsonify({
            "ok": False,
            "error": "Клетка уже занята"
        }), 400

    # Игрок
    board[position] = "X"

    winner = check_tic_winner(board)

    if winner == "X":

        reward = 15

        give_game_reward(
            user_id,
            reward
        )

        database.add_task_game(
            user_id,
            1
        )

        game_counter[user_id] = (
            game_counter.get(user_id, 0) + 1
        )

        achievements = check_achievements(
            user_id
        )

        del tic_games[user_id]

        return jsonify({
            "ok": True,
            "result": "win",
            "board": board,
            "reward": reward,
            "achievements": achievements,
            "data": snap(user_id)
        })

    if winner == "draw":

        database.add_task_game(
            user_id,
            1
        )

        game_counter[user_id] = (
            game_counter.get(user_id, 0) + 1
        )

        del tic_games[user_id]

        return jsonify({
            "ok": True,
            "result": "draw",
            "board": board,
            "data": snap(user_id)
        })

    # Ход компьютера
    empty = [
        i
        for i in range(9)
        if not board[i]
    ]

    if empty:

        computer_position = random.choice(
            empty
        )

        board[computer_position] = "O"

    winner = check_tic_winner(board)

    if winner == "O":

        database.add_task_game(
            user_id,
            1
        )

        game_counter[user_id] = (
            game_counter.get(user_id, 0) + 1
        )

        del tic_games[user_id]

        return jsonify({
            "ok": True,
            "result": "lose",
            "board": board
        })

    if winner == "draw":

        database.add_task_game(
            user_id,
            1
        )

        game_counter[user_id] = (
            game_counter.get(user_id, 0) + 1
        )

        del tic_games[user_id]

        return jsonify({
            "ok": True,
            "result": "draw",
            "board": board
        })

    return jsonify({
        "ok": True,
        "result": "continue",
        "board": board
    })


# =========================================================
# EGGS SHOP
# =========================================================

@app.route("/api/eggs", methods=["POST"])
def eggs():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    shop = []

    for egg_id, egg in EGGS.items():

        shop.append({
            "id": egg_id,
            "name": egg["name"],
            "price": egg["price"]
        })

    owned = database.get_player_eggs(
        user_id
    )

    return jsonify({
        "ok": True,
        "shop": shop,
        "owned": owned,
        "eggs": shop
    })


# =========================================================
# BUY EGG
# =========================================================

@app.route("/api/eggs/buy", methods=["POST"])
def buy_egg():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

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
            "error": "Неверное яйцо"
        }), 400

    if egg_id not in EGGS:
        return jsonify({
            "ok": False,
            "error": "Яйцо не найдено"
        }), 404

    price = EGGS[egg_id]["price"]

    if not database.remove_egg_coins(
        user_id,
        price
    ):
        return jsonify({
            "ok": False,
            "error": "Недостаточно Egg Coins"
        }), 400

    database.add_egg(
        user_id,
        egg_id
    )

    database.add_task_egg(
        user_id,
        1
    )

    achievements = check_achievements(
        user_id
    )

    return jsonify({
        "ok": True,

        "egg": {
            "id": egg_id,
            "name": EGGS[egg_id]["name"]
        },

        "data": snap(user_id),

        "achievements": achievements
    })


# =========================================================
# OPEN EGG
# =========================================================

@app.route("/api/eggs/open", methods=["POST"])
def open_egg():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

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
            "error": "Неверное яйцо"
        }), 400

    if database.get_egg_count(
        user_id,
        egg_id
    ) <= 0:

        return jsonify({
            "ok": False,
            "error": "У тебя нет этого яйца"
        }), 400

    database.remove_one_egg(
        user_id,
        egg_id
    )

    # Награда зависит от яйца
    reward = 5 + egg_id * 2

    database.add_egg_coins(
        user_id,
        reward
    )

    give_xp(
        user_id,
        20
    )

    achievements = check_achievements(
        user_id
    )

    return jsonify({
        "ok": True,
        "reward": reward,
        "egg": {
            "id": egg_id,
            "name": EGGS[egg_id]["name"]
        },
        "achievements": achievements,
        "data": snap(user_id)
    })


# =========================================================
# ITEMS
# =========================================================

@app.route("/api/items", methods=["POST"])
def items():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    result = []

    owned = {
        item["item_id"]: item["count"]
        for item in database.get_items(user_id)
    }

    for item_id, item in ITEMS.items():

        result.append({
            "id": item_id,
            "name": item["name"],
            "description": item["description"],
            "price": item["price"],
            "duration": item["duration"],
            "count": owned.get(item_id, 0),
            "owned": owned.get(item_id, 0),

            "active": is_item_active(
                user_id,
                item_id
            )
        })

    return jsonify({
        "ok": True,
        "items": result
    })


# =========================================================
# BUY ITEM
# =========================================================

@app.route("/api/items/buy", methods=["POST"])
def buy_item():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

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
            "error": "Неверный предмет"
        }), 400

    if item_id not in ITEMS:
        return jsonify({
            "ok": False,
            "error": "Предмет не найден"
        }), 404

    price = ITEMS[item_id]["price"]

    if not database.remove_egg_coins(
        user_id,
        price
    ):
        return jsonify({
            "ok": False,
            "error": "Недостаточно Egg Coins"
        }), 400

    database.add_item(
        user_id,
        item_id
    )

    return jsonify({
        "ok": True,
        "item": ITEMS[item_id],
        "data": snap(user_id)
    })


# =========================================================
# USE ITEM
# =========================================================

@app.route("/api/items/use", methods=["POST"])
def use_item():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

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
            "error": "Неверный предмет"
        }), 400

    success, message = activate_item(
        user_id,
        item_id
    )

    if not success:
        return jsonify({
            "ok": False,
            "error": message
        }), 400

    return jsonify({
        "ok": True,
        "message": message,
        "data": snap(user_id)
    })


# =========================================================
# ACHIEVEMENTS
# =========================================================

@app.route("/api/achievements", methods=["POST"])
def achievements():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    owned = set(
        database.get_achievements(
            user_id
        )
    )

    result = []

    for achievement_id, achievement in ACHIEVEMENTS.items():

        result.append({
            "id": achievement_id,
            "name": achievement["name"],
            "description": achievement["description"],
            "reward": achievement["reward"],
            "claimed": achievement_id in owned
        })

    return jsonify({
        "ok": True,
        "items": result,
        "achievements": result
    })


# =========================================================
# LEADERBOARD
# =========================================================

@app.route("/api/leaderboard", methods=["POST"])
def leaderboard():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    players = database.get_top_players(
        10
    )

    result = []

    for index, player in enumerate(
        players,
        start=1
    ):

        result.append({
            "rank": index,
            "user_id": player["user_id"],
            "username": player["username"] or "Игрок",
            "tap_coins": player["tap_coins"],
            "egg_coins": player["egg_coins"],
            "level": player["level"],
            "xp": player["xp"]
        })

    my_rank = None

    all_players = database.get_all_players()

    sorted_players = sorted(
        [
            p for p in all_players
            if not p["blocked"]
        ],
        key=lambda x: (
            x["egg_coins"],
            x["xp"]
        ),
        reverse=True
    )

    for index, player in enumerate(
        sorted_players,
        start=1
    ):

        if player["user_id"] == user_id:
            my_rank = index
            break

    return jsonify({
        "ok": True,
        "players": result,
        "leaderboard": result,
        "my_rank": my_rank
    })


# =========================================================
# DAILY BONUS
# =========================================================

@app.route("/api/daily/bonus", methods=["POST"])
def daily_bonus():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    today = database.get_daily_bonus_date(
        user_id
    )

    from datetime import date

    current_date = date.today().isoformat()

    if today == current_date:
        return jsonify({
            "ok": False,
            "error": "Бонус уже получен сегодня"
        }), 400

    reward = 25

    database.add_egg_coins(
        user_id,
        reward
    )

    database.set_daily_bonus_date(
        user_id
    )

    return jsonify({
        "ok": True,
        "reward": reward,
        "data": snap(user_id)
    })


# =========================================================
# DAILY TASKS
# =========================================================

@app.route("/api/daily/tasks", methods=["POST"])
def daily_tasks():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    tasks = database.get_daily_tasks(
        user_id
    )

    result = [
        {
            "id": "taps",
            "title": "Сделать 100 тапов",
            "progress": min(tasks[0], 100),
            "target": 100,
            "reward": 10,

            "claimed":
                database.has_daily_task_claim(
                    user_id,
                    "taps"
                )
        },

        {
            "id": "games",
            "title": "Сыграть 5 мини-игр",
            "progress": min(tasks[1], 5),
            "target": 5,
            "reward": 15,

            "claimed":
                database.has_daily_task_claim(
                    user_id,
                    "games"
                )
        },

        {
            "id": "eggs",
            "title": "Получить 3 яйца",
            "progress": min(tasks[2], 3),
            "target": 3,
            "reward": 20,

            "claimed":
                database.has_daily_task_claim(
                    user_id,
                    "eggs"
                )
        }
    ]

    return jsonify({
        "ok": True,
        "tasks": result
    })


# =========================================================
# CLAIM DAILY TASK
# =========================================================

@app.route("/api/daily/tasks/claim", methods=["POST"])
def claim_daily_task():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    data = request.get_json(
        silent=True
    ) or {}

    task_id = data.get(
        "task_id"
    )

    if task_id not in [
        "taps",
        "games",
        "eggs"
    ]:
        return jsonify({
            "ok": False,
            "error": "Неверное задание"
        }), 400

    if database.has_daily_task_claim(
        user_id,
        task_id
    ):
        return jsonify({
            "ok": False,
            "error": "Награда уже получена"
        }), 400

    tasks = database.get_daily_tasks(
        user_id
    )

    progress = {
        "taps": tasks[0],
        "games": tasks[1],
        "eggs": tasks[2]
    }

    targets = {
        "taps": 100,
        "games": 5,
        "eggs": 3
    }

    rewards = {
        "taps": 10,
        "games": 15,
        "eggs": 20
    }

    if progress[task_id] < targets[task_id]:
        return jsonify({
            "ok": False,
            "error": "Задание ещё не выполнено"
        }), 400

    if not database.add_daily_task_claim(
        user_id,
        task_id
    ):
        return jsonify({
            "ok": False,
            "error": "Награда уже получена"
        }), 400

    reward = rewards[task_id]

    database.add_egg_coins(
        user_id,
        reward
    )

    return jsonify({
        "ok": True,
        "reward": reward,
        "data": snap(user_id)
    })


# =========================================================
# BOSS
# =========================================================

@app.route("/api/boss", methods=["POST"])
def boss():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    global boss_hp

    return jsonify({
        "ok": True,
        "hp": boss_hp,
        "max_hp": BOSS_MAX_HP,
        "damage": database.get_boss_damage(
            user_id
        )
    })


@app.route("/api/boss/attack", methods=["POST"])
def boss_attack():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    global boss_hp

    now = time.time()

    if now - last_boss.get(
        user_id,
        0
    ) < 0.2:

        return jsonify({
            "ok": False,
            "error": "Слишком быстро"
        }), 429

    last_boss[user_id] = now

    damage = random.randint(
        5,
        15
    )

    boss_hp -= damage

    if boss_hp < 0:
        boss_hp = 0

    database.add_boss_damage(
        user_id,
        damage
    )

    give_xp(
        user_id,
        2
    )

    achievements = check_achievements(
        user_id
    )

    # Когда босс побеждён
    if boss_hp <= 0:

        database.add_egg_coins(
            user_id,
            100
        )

        boss_hp = BOSS_MAX_HP

        return jsonify({
            "ok": True,
            "damage": damage,
            "hp": boss_hp,
            "max_hp": BOSS_MAX_HP,
            "reward": 100,
            "boss_defeated": True,
            "achievements": achievements,
            "data": snap(user_id)
        })

    return jsonify({
        "ok": True,
        "damage": damage,
        "hp": boss_hp,
        "max_hp": BOSS_MAX_HP,
        "boss_defeated": False,
        "achievements": achievements,
        "data": snap(user_id)
    })


# =========================================================
# WITHDRAWAL
# =========================================================

@app.route("/api/withdrawal", methods=["POST"])
def withdrawal():

    user = require_user()

    if not user:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    user_id = uid_from_user(user)

    tap_coins, egg_coins = database.get_balance(
        user_id
    )

    total = egg_coins

    return jsonify({
        "ok": True,

        "bot": WITHDRAWAL_BOT,

        "tap_coins": tap_coins,
        "egg_coins": egg_coins,

        "eggs": database.get_total_eggs(
            user_id
        ),

        "total": total
    })


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print(
        "BOT_TOKEN задан:",
        bool(BOT_TOKEN)
    )

    print(
        "Длина BOT_TOKEN:",
        len(BOT_TOKEN)
    )

    app.run(
        host="0.0.0.0",
        port=PORT
    )
