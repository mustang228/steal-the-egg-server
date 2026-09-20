import os
import time
import hmac
import hashlib
import json
import random

from datetime import date
from urllib.parse import parse_qsl

from flask import Flask, request, jsonify
from flask_cors import CORS

import database


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
        "name": "🥚 Обычное яйцо",
        "price": 100,
        "rarity": "Обычное"
    },

    2: {
        "name": "🥈 Серебряное яйцо",
        "price": 600,
        "rarity": "Серебряное"
    },

    3: {
        "name": "🥇 Золотое яйцо",
        "price": 700,
        "rarity": "Золотое"
    },

    4: {
        "name": "💎 Алмазное яйцо",
        "price": 800,
        "rarity": "Алмазное"
    },

    5: {
        "name": "🔥 Огненное яйцо",
        "price": 900,
        "rarity": "Огненное"
    },

    6: {
        "name": "❄️ Ледяное яйцо",
        "price": 1000,
        "rarity": "Ледяное"
    },

    7: {
        "name": "🌌 Космическое яйцо",
        "price": 1100,
        "rarity": "Космическое"
    },

    8: {
        "name": "👑 Королевское яйцо",
        "price": 1200,
        "rarity": "Королевское"
    },

    9: {
        "name": "⚡ Молниеносное яйцо",
        "price": 1300,
        "rarity": "Молниеносное"
    },

    10: {
        "name": "🌑 Тёмное яйцо",
        "price": 1400,
        "rarity": "Тёмное"
    }
}


# =========================================================
# ITEMS
# =========================================================

ITEMS = {
    1: {
        "name": "⚡ Tap Booster",
        "description": "+2 Tap Coins за тап",
        "price": 150,
        "active_seconds": 600
    },

    2: {
        "name": "🥚 Egg Coin Booster",
        "description": "+1 Egg Coin за награды мини-игр",
        "price": 250,
        "active_seconds": 600
    },

    3: {
        "name": "⭐ XP Booster",
        "description": "2x XP",
        "price": 200,
        "active_seconds": 600
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
        "description": "Купить первое яйцо",
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
        "description": "Собрать 10 яиц",
        "reward": 150
    },

    8: {
        "name": "Босс",
        "description": "Нанести 1000 урона боссу",
        "reward": 200
    }
}


# =========================================================
# AVATARS
# =========================================================

AVATARS = [
    "🥚",
    "🐣",
    "🐥",
    "🐔",
    "🦆",
    "🐧",
    "🦉",
    "🐲",
    "👑",
    "😎",
    "🤖",
    "👽",
    "👾",
    "🔥",
    "💎",
    "⚡"
]


# =========================================================
# MEMORY
# =========================================================

guess_games = {}
math_games = {}
tic_games = {}

last_tap = {}
last_boss = {}

active_items = {}

tap_counter = {}
game_counter = {}


# =========================================================
# BOSS
# =========================================================

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
        raise ValueError("Нет Telegram Init Data")

    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не настроен")

    data = dict(parse_qsl(init_data, keep_blank_values=True))

    received_hash = data.pop("hash", None)

    if not received_hash:
        raise ValueError("Нет hash")

    auth_date = int(data.get("auth_date", "0"))

    if not auth_date:
        raise ValueError("Нет auth_date")

    if time.time() - auth_date > 86400:
        raise ValueError("Telegram данные устарели")

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(data.items())
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
        raise ValueError("Неверная Telegram подпись")

    user = json.loads(data.get("user", "{}"))

    if not user:
        raise ValueError("Не найден пользователь Telegram")

    return user


def get_current_user():

    init_data = request.headers.get(
        "X-Telegram-Init-Data",
        ""
    )

    user = validate_telegram_data(init_data)

    user_id = int(user["id"])

    database.ensure_player(
        user_id,
        user.get("username"),
        user.get("first_name")
    )

    if database.is_blocked(user_id):
        raise ValueError("Пользователь заблокирован")

    return user


def require_user():

    try:
        return get_current_user()

    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 401


def uid_from_user(user):

    return int(user["id"])


def get_username(user):

    return (
        user.get("username")
        or user.get("first_name")
        or "Игрок"
    )


# =========================================================
# ITEMS
# =========================================================

def activate_item(user_id, item_id):

    item_id = int(item_id)

    if item_id not in ITEMS:
        raise ValueError("Предмет не найден")

    count = database.get_item_count(
        user_id,
        item_id
    )

    if count <= 0:
        raise ValueError("У тебя нет этого предмета")

    database.remove_item(
        user_id,
        item_id
    )

    active_items.setdefault(
        user_id,
        {}
    )[item_id] = (
        time.time()
        + ITEMS[item_id]["active_seconds"]
    )


def is_item_active(user_id, item_id):

    user_items = active_items.get(
        user_id,
        {}
    )

    expires = user_items.get(item_id)

    if not expires:
        return False

    if time.time() >= expires:

        user_items.pop(
            item_id,
            None
        )

        return False

    return True


def give_xp(user_id, amount):

    if is_item_active(user_id, 3):
        amount *= 2

    return database.add_xp(
        user_id,
        amount
    )


def give_game_reward(user_id, amount):

    if is_item_active(user_id, 2):
        amount += 1

    database.add_egg_coins(
        user_id,
        amount
    )

    give_xp(
        user_id,
        10
    )


# =========================================================
# ACHIEVEMENTS
# =========================================================

def check_achievements(user_id):

    result = []

    taps = tap_counter.get(
        user_id,
        0
    )

    games = game_counter.get(
        user_id,
        0
    )

    xp, level = database.get_progress(
        user_id
    )

    eggs_total = database.get_total_eggs(
        user_id
    )

    boss_damage = database.get_boss_damage(
        user_id
    )

    checks = {

        1: taps >= 1,

        2: taps >= 100,

        3: taps >= 1000,

        4: eggs_total >= 1,

        5: games >= 10,

        6: level >= 5,

        7: eggs_total >= 10,

        8: boss_damage >= 1000
    }

    for achievement_id, unlocked in checks.items():

        if not unlocked:
            continue

        if database.has_achievement(
            user_id,
            achievement_id
        ):
            continue

        achievement = ACHIEVEMENTS[
            achievement_id
        ]

        database.add_achievement(
            user_id,
            achievement_id
        )

        database.add_egg_coins(
            user_id,
            achievement["reward"]
        )

        result.append({
            "id": achievement_id,
            "name": achievement["name"],
            "reward": achievement["reward"]
        })

    return result


# =========================================================
# SNAP
# =========================================================

def snap(user_id):

    tap_coins = database.get_tap_coins(
        user_id
    )

    egg_coins = database.get_egg_coins(
        user_id
    )

    xp, level = database.get_progress(
        user_id
    )

    streak = database.get_login_streak(
        user_id
    )

    taps, games, eggs = database.get_daily_tasks(
        user_id
    )

    player_eggs = database.get_player_eggs(
        user_id
    )

    egg_counts = {}

    for egg_id in player_eggs:

        egg_id = int(egg_id)

        egg_counts[str(egg_id)] = (
            egg_counts.get(
                str(egg_id),
                0
            ) + 1
        )

    achievements = database.get_achievements(
        user_id
    )

    items = database.get_player_items(
        user_id
    )

    boss_damage = database.get_boss_damage(
        user_id
    )

    avatar = database.get_avatar(
        user_id
    )

    # XP внутри уровня.
    # 100 XP = один уровень.
    xp_required = 100

    # XP в текущем уровне.
    current_xp = xp % xp_required

    return {

        "tap_coins": tap_coins,

        "egg_coins": egg_coins,

        "xp": current_xp,

        "xp_total": xp,

        "xp_required": xp_required,

        "level": level,

        "streak": streak,

        "tasks": {

            "taps": taps,

            "games": games,

            "eggs": eggs
        },

        "boss_damage": boss_damage,

        "eggs": player_eggs,

        "eggs_total": len(player_eggs),

        "egg_counts": egg_counts,

        "items": items,

        "achievements": achievements,

        "avatar": avatar,

        "avatars": AVATARS
    }


# =========================================================
# INIT
# =========================================================

@app.post("/api/init")
def api_init():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        database.update_login(
            user_id
        )

        claimed, streak, reward = (
            database.get_login_status(
                user_id
            )
        )

        if not claimed:

            database.add_egg_coins(
                user_id,
                reward
            )

            database.set_daily_login(
                user_id
            )

        new_achievements = check_achievements(
            user_id
        )

        return jsonify({

            "ok": True,

            "user": user,

            "login": {
                "claimed": not claimed,
                "streak": streak,
                "reward": reward
            },

            "new_achievements":
                new_achievements,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# STATE
# =========================================================

@app.get("/api/state")
def api_state():

    try:

        user = get_current_user()

        return jsonify({
            "ok": True,
            "data": snap(
                uid_from_user(user)
            )
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# TAP
# =========================================================

@app.post("/api/tap")
def api_tap():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        now = time.time()

        previous = last_tap.get(
            user_id,
            0
        )

        if now - previous < 0.05:
            raise ValueError("Слишком быстро")

        last_tap[user_id] = now

        amount = 1

        if is_item_active(
            user_id,
            1
        ):
            amount += 2

        database.add_tap_coins(
            user_id,
            amount
        )

        database.add_task_tap(
            user_id
        )

        tap_counter[user_id] = (
            tap_counter.get(
                user_id,
                0
            ) + 1
        )

        new_achievements = check_achievements(
            user_id
        )

        return jsonify({

            "ok": True,

            "amount": amount,

            "new_achievements":
                new_achievements,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# EXCHANGE
# =========================================================

@app.post("/api/exchange")
def api_exchange():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        if database.get_tap_coins(
            user_id
        ) < 1000:

            raise ValueError(
                "Нужно минимум 1000 Tap Coins"
            )

        database.remove_tap_coins(
            user_id,
            1000
        )

        database.add_egg_coins(
            user_id,
            10
        )

        return jsonify({

            "ok": True,

            "received": 10,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# GUESS THE NUMBER
# =========================================================

@app.post("/api/game/guess/start")
def guess_start():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        guess_games[user_id] = {

            "number": random.randint(
                1,
                20
            ),

            "attempts": 0
        }

        return jsonify({
            "ok": True
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.post("/api/game/guess/try")
@app.post("/api/game/guess/answer")
def guess_try():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        game = guess_games.get(
            user_id
        )

        if not game:
            raise ValueError(
                "Сначала начни игру"
            )

        data = request.get_json(
            silent=True
        ) or {}

        try:
            guess = int(
                data.get("guess")
            )
        except:
            raise ValueError(
                "Введи число от 1 до 20"
            )

        if guess < 1 or guess > 20:
            raise ValueError(
                "Число должно быть от 1 до 20"
            )

        game["attempts"] += 1

        number = game["number"]

        if guess == number:

            reward = 10

            give_game_reward(
                user_id,
                reward
            )

            database.add_task_game(
                user_id
            )

            game_counter[user_id] = (
                game_counter.get(
                    user_id,
                    0
                ) + 1
            )

            new_achievements = (
                check_achievements(
                    user_id
                )
            )

            del guess_games[user_id]

            return jsonify({

                "ok": True,

                "result": "win",

                "number": number,

                "attempts":
                    game["attempts"],

                "reward": reward,

                "new_achievements":
                    new_achievements,

                "data":
                    snap(user_id)
            })

        if game["attempts"] >= 10:

            del guess_games[user_id]

            return jsonify({

                "ok": True,

                "result": "lose",

                "number": number,

                "attempts": 10,

                "reward": 0,

                "data":
                    snap(user_id)
            })

        hint = (
            "Больше"
            if guess < number
            else
            "Меньше"
        )

        return jsonify({

            "ok": True,

            "result": "continue",

            "hint": hint,

            "attempts":
                game["attempts"]
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# MATH
# =========================================================

def create_math_game(user_id):

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

        "a": a,

        "b": b,

        "operation": operation,

        "answer": answer,

        "question":
            f"{a} {operation} {b} = ?"
    }

    return math_games[user_id]


@app.post("/api/game/math/start")
def math_start():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        game = create_math_game(
            user_id
        )

        return jsonify({

            "ok": True,

            "question":
                game["question"]
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.post("/api/game/math/answer")
def math_answer():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        game = math_games.get(
            user_id
        )

        if not game:

            raise ValueError(
                "Сначала начни игру"
            )

        data = request.get_json(
            silent=True
        ) or {}

        try:
            answer = int(
                data.get("answer")
            )
        except:
            raise ValueError(
                "Введи число"
            )

        correct_answer = game["answer"]

        # =============================================
        # НЕПРАВИЛЬНЫЙ ОТВЕТ
        # =============================================

        if answer != correct_answer:

            # Сразу создаём новый пример
            new_game = create_math_game(
                user_id
            )

            return jsonify({

                "ok": True,

                "result": "lose",

                "correct": correct_answer,

                "reward": 0,

                "message":
                    "❌ Неправильно! Попробуй новый пример.",

                "question":
                    new_game["question"],

                "new_question":
                    new_game["question"]
            })

        # =============================================
        # ПРАВИЛЬНЫЙ ОТВЕТ
        # =============================================

        reward = 10

        give_game_reward(
            user_id,
            reward
        )

        database.add_task_game(
            user_id
        )

        game_counter[user_id] = (
            game_counter.get(
                user_id,
                0
            ) + 1
        )

        new_achievements = (
            check_achievements(
                user_id
            )
        )

        # После правильного ответа игра заканчивается.
        math_games.pop(
            user_id,
            None
        )

        return jsonify({

            "ok": True,

            "result": "win",

            "correct":
                correct_answer,

            "reward": reward,

            "new_achievements":
                new_achievements,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# TIC TAC TOE
# =========================================================

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
            board[a] != " "
            and board[a] == board[b]
            and board[b] == board[c]
        ):
            return board[a]

    if all(
        cell != " "
        for cell in board
    ):
        return "draw"

    return None


@app.post("/api/game/tic/start")
def tic_start():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        tic_games[user_id] = {

            "board": [
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " ",
                " "
            ]
        }

        return jsonify({

            "ok": True,

            "board":
                tic_games[user_id]["board"]
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.post("/api/game/tic/move")
def tic_move():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        game = tic_games.get(
            user_id
        )

        if not game:
            raise ValueError(
                "Сначала начни игру"
            )

        data = request.get_json(
            silent=True
        ) or {}

        try:
            index = int(
                data.get("index")
            )
        except:
            raise ValueError(
                "Неверная клетка"
            )

        if index < 0 or index > 8:
            raise ValueError(
                "Неверная клетка"
            )

        board = game["board"]

        if board[index] != " ":
            raise ValueError(
                "Эта клетка уже занята"
            )

        # Игрок
        board[index] = "X"

        winner = check_tic_winner(
            board
        )

        if winner == "X":

            reward = 15

            give_game_reward(
                user_id,
                reward
            )

            database.add_task_game(
                user_id
            )

            game_counter[user_id] = (
                game_counter.get(
                    user_id,
                    0
                ) + 1
            )

            new_achievements = (
                check_achievements(
                    user_id
                )
            )

            del tic_games[user_id]

            return jsonify({

                "ok": True,

                "result": "win",

                "board": board,

                "reward": reward,

                "new_achievements":
                    new_achievements,

                "data":
                    snap(user_id)
            })

        if winner == "draw":

            del tic_games[user_id]

            return jsonify({

                "ok": True,

                "result": "draw",

                "board": board,

                "reward": 2,

                "data":
                    snap(user_id)
            })

        # Компьютер
        empty = [
            i
            for i, cell
            in enumerate(board)
            if cell == " "
        ]

        if empty:

            bot_index = random.choice(
                empty
            )

            board[bot_index] = "O"

        winner = check_tic_winner(
            board
        )

        if winner == "O":

            game_counter[user_id] = (
                game_counter.get(
                    user_id,
                    0
                ) + 1
            )

            del tic_games[user_id]

            return jsonify({

                "ok": True,

                "result": "lose",

                "board": board,

                "reward": 0,

                "data":
                    snap(user_id)
            })

        if winner == "draw":

            del tic_games[user_id]

            return jsonify({

                "ok": True,

                "result": "draw",

                "board": board,

                "reward": 2,

                "data":
                    snap(user_id)
            })

        return jsonify({

            "ok": True,

            "result": "continue",

            "board": board
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# EGGS
# =========================================================

@app.get("/api/eggs")
def api_eggs():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        owned_list = (
            database.get_player_eggs(
                user_id
            )
        )

        owned = {}

        for egg_id in owned_list:

            egg_id = str(egg_id)

            owned[egg_id] = (
                owned.get(
                    egg_id,
                    0
                ) + 1
            )

        shop = {}

        for egg_id, egg in EGGS.items():

            shop[str(egg_id)] = {

                "id": egg_id,

                "name": egg["name"],

                "price": egg["price"],

                "rarity": egg["rarity"]
            }

        return jsonify({

            "ok": True,

            "shop": shop,

            "owned": owned,

            "eggs": shop
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.post("/api/eggs/buy")
def buy_egg():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        data = request.get_json(
            silent=True
        ) or {}

        try:
            egg_id = int(
                data.get("egg_id")
            )
        except:
            raise ValueError(
                "Неверный ID яйца"
            )

        # ВАЖНО:
        # Используем именно выбранный ID,
        # а не цену или позицию списка.
        egg = EGGS.get(
            egg_id
        )

        if not egg:

            raise ValueError(
                "Яйцо не найдено"
            )

        price = egg["price"]

        if database.get_egg_coins(
            user_id
        ) < price:

            raise ValueError(
                f"Недостаточно Egg Coins. Нужно {price}"
            )

        database.remove_egg_coins(
            user_id,
            price
        )

        # Реально добавляем выбранное яйцо
        database.add_egg(
            user_id,
            egg_id
        )

        database.add_task_egg(
            user_id
        )

        new_achievements = (
            check_achievements(
                user_id
            )
        )

        return jsonify({

            "ok": True,

            "egg": {

                "id": egg_id,

                "name": egg["name"],

                "price": price,

                "rarity":
                    egg["rarity"]
            },

            "new_achievements":
                new_achievements,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# OPEN EGG
# =========================================================

@app.post("/api/eggs/open")
def open_egg():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        data = request.get_json(
            silent=True
        ) or {}

        try:
            egg_id = int(
                data.get("egg_id")
            )
        except:
            raise ValueError(
                "Неверный ID яйца"
            )

        if egg_id not in EGGS:

            raise ValueError(
                "Яйцо не найдено"
            )

        if database.get_egg_count(
            user_id,
            egg_id
        ) <= 0:

            raise ValueError(
                "У тебя нет этого яйца"
            )

        database.remove_one_egg(
            user_id,
            egg_id
        )

        reward = 5 + egg_id * 2

        database.add_egg_coins(
            user_id,
            reward
        )

        give_xp(
            user_id,
            20
        )

        new_achievements = (
            check_achievements(
                user_id
            )
        )

        return jsonify({

            "ok": True,

            "egg_id": egg_id,

            "reward": reward,

            "new_achievements":
                new_achievements,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# ITEMS API
# =========================================================

@app.get("/api/items")
def api_items():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        result = {}

        for item_id, item in ITEMS.items():

            result[str(item_id)] = {

                "id": item_id,

                "name":
                    item["name"],

                "description":
                    item["description"],

                "price":
                    item["price"],

                "active_seconds":
                    item["active_seconds"],

                "count":
                    database.get_item_count(
                        user_id,
                        item_id
                    ),

                "active":
                    is_item_active(
                        user_id,
                        item_id
                    )
            }

        return jsonify({

            "ok": True,

            "items": result
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.post("/api/items/buy")
def buy_item():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        data = request.get_json(
            silent=True
        ) or {}

        item_id = int(
            data.get("item_id")
        )

        item = ITEMS.get(
            item_id
        )

        if not item:

            raise ValueError(
                "Предмет не найден"
            )

        price = item["price"]

        if database.get_egg_coins(
            user_id
        ) < price:

            raise ValueError(
                "Недостаточно Egg Coins"
            )

        database.remove_egg_coins(
            user_id,
            price
        )

        database.add_item(
            user_id,
            item_id
        )

        return jsonify({

            "ok": True,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.post("/api/items/activate")
def use_item():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        data = request.get_json(
            silent=True
        ) or {}

        item_id = int(
            data.get("item_id")
        )

        activate_item(
            user_id,
            item_id
        )

        return jsonify({

            "ok": True,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# ACHIEVEMENTS API
# =========================================================

@app.get("/api/achievements")
def api_achievements():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        unlocked = {
            a["achievement_id"]
            for a
            in database.get_achievements(
                user_id
            )
        }

        items = []

        for achievement_id, achievement in (
            ACHIEVEMENTS.items()
        ):

            items.append({

                "id": achievement_id,

                "name":
                    achievement["name"],

                "description":
                    achievement["description"],

                "reward":
                    achievement["reward"],

                "unlocked":
                    achievement_id in unlocked
            })

        return jsonify({

            "ok": True,

            "items": items
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# LEADERBOARD
# =========================================================

@app.get("/api/leaderboard")
def leaderboard():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        players = database.get_top_players(
            10
        )

        result = []

        for i, player in enumerate(
            players,
            start=1
        ):

            player_id = int(
                player["user_id"]
            )

            result.append({

                "rank": i,

                "user_id":
                    player_id,

                "username":
                    player["username"],

                "tap_coins":
                    player["tap_coins"],

                "egg_coins":
                    player["egg_coins"],

                "level":
                    player["level"],

                "xp":
                    player["xp"],

                "avatar":
                    database.get_avatar(
                        player_id
                    )
            })

        all_players = (
            database.get_all_players()
        )

        all_players.sort(
            key=lambda p: (
                p["egg_coins"],
                p["xp"]
            ),
            reverse=True
        )

        my_rank = None

        for i, player in enumerate(
            all_players,
            start=1
        ):

            if int(
                player["user_id"]
            ) == user_id:

                my_rank = i

                break

        return jsonify({

            "ok": True,

            "players": result,

            "my_rank": my_rank
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# AVATAR
# =========================================================

@app.get("/api/avatar")
def get_avatar_api():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        return jsonify({

            "ok": True,

            "avatar":
                database.get_avatar(
                    user_id
                ),

            "avatars":
                AVATARS
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.post("/api/avatar")
def set_avatar_api():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        data = request.get_json(
            silent=True
        ) or {}

        avatar = str(
            data.get("avatar", "")
        )

        if avatar not in AVATARS:

            raise ValueError(
                "Такой аватар недоступен"
            )

        database.set_avatar(
            user_id,
            avatar
        )

        return jsonify({

            "ok": True,

            "avatar": avatar,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# DAILY BONUS
# =========================================================

@app.post("/api/daily/bonus")
def daily_bonus():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        today = date.today().isoformat()

        last = database.get_daily_bonus_date(
            user_id
        )

        if last == today:

            raise ValueError(
                "Сегодня ты уже получил бонус"
            )

        reward = 25

        database.add_egg_coins(
            user_id,
            reward
        )

        database.set_daily_bonus_date(
            user_id,
            today
        )

        return jsonify({

            "ok": True,

            "reward": reward,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# DAILY TASKS
# =========================================================

@app.get("/api/daily/tasks")
def daily_tasks():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        taps, games, eggs = (
            database.get_daily_tasks(
                user_id
            )
        )

        tasks = [

            {
                "id": 1,
                "title": "👆 Сделать 50 тапов",
                "progress": taps,
                "target": 50,
                "reward": 10,
                "claimed":
                    database.has_daily_task_claim(
                        user_id,
                        1
                    )
            },

            {
                "id": 2,
                "title": "🎮 Сыграть 3 игры",
                "progress": games,
                "target": 3,
                "reward": 15,
                "claimed":
                    database.has_daily_task_claim(
                        user_id,
                        2
                    )
            },

            {
                "id": 3,
                "title": "🥚 Получить яйцо",
                "progress": eggs,
                "target": 1,
                "reward": 20,
                "claimed":
                    database.has_daily_task_claim(
                        user_id,
                        3
                    )
            }
        ]

        return jsonify({

            "ok": True,

            "tasks": tasks
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.post("/api/daily/tasks/claim")
def claim_task():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        data = request.get_json(
            silent=True
        ) or {}

        task_id = int(
            data.get("task_id")
        )

        taps, games, eggs = (
            database.get_daily_tasks(
                user_id
            )
        )

        task_data = {

            1: (
                taps,
                50,
                10
            ),

            2: (
                games,
                3,
                15
            ),

            3: (
                eggs,
                1,
                20
            )
        }

        if task_id not in task_data:

            raise ValueError(
                "Задание не найдено"
            )

        progress, target, reward = (
            task_data[task_id]
        )

        if database.has_daily_task_claim(
            user_id,
            task_id
        ):

            raise ValueError(
                "Задание уже получено"
            )

        if progress < target:

            raise ValueError(
                "Задание ещё не выполнено"
            )

        database.add_daily_task_claim(
            user_id,
            task_id
        )

        database.add_egg_coins(
            user_id,
            reward
        )

        return jsonify({

            "ok": True,

            "reward": reward,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# BOSS
# =========================================================

@app.get("/api/boss")
def boss():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        return jsonify({

            "ok": True,

            "hp": boss_hp,

            "max_hp":
                BOSS_MAX_HP,

            "my_damage":
                database.get_boss_damage(
                    user_id
                )
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


@app.post("/api/boss/attack")
def boss_attack():

    global boss_hp

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        now = time.time()

        previous = last_boss.get(
            user_id,
            0
        )

        if now - previous < 0.2:

            raise ValueError(
                "Слишком быстро"
            )

        last_boss[user_id] = now

        damage = random.randint(
            5,
            15
        )

        boss_hp = max(
            0,
            boss_hp - damage
        )

        database.add_boss_damage(
            user_id,
            damage
        )

        give_xp(
            user_id,
            2
        )

        new_achievements = (
            check_achievements(
                user_id
            )
        )

        defeated = False

        if boss_hp <= 0:

            defeated = True

            database.add_egg_coins(
                user_id,
                100
            )

            boss_hp = BOSS_MAX_HP

        return jsonify({

            "ok": True,

            "damage": damage,

            "defeated": defeated,

            "hp": boss_hp,

            "max_hp":
                BOSS_MAX_HP,

            "new_achievements":
                new_achievements,

            "data":
                snap(user_id)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# WITHDRAWAL
# =========================================================

@app.get("/api/withdrawal")
def withdrawal():

    try:

        user = get_current_user()

        user_id = uid_from_user(user)

        player_eggs = (
            database.get_player_eggs(
                user_id
            )
        )

        eggs = {}

        for egg_id in player_eggs:

            egg_id = int(egg_id)

            if egg_id not in EGGS:
                continue

            key = str(egg_id)

            if key not in eggs:

                eggs[key] = {

                    "id": egg_id,

                    "name":
                        EGGS[egg_id]["name"],

                    "rarity":
                        EGGS[egg_id]["rarity"],

                    "count": 0
                }

            eggs[key]["count"] += 1

        return jsonify({

            "ok": True,

            "bot":
                WITHDRAWAL_BOT,

            "tap_coins":
                database.get_tap_coins(
                    user_id
                ),

            "egg_coins":
                database.get_egg_coins(
                    user_id
                ),

            "eggs": eggs,

            "total":
                len(player_eggs)
        })

    except Exception as e:

        return jsonify({
            "ok": False,
            "error": str(e)
        }), 400


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/")
def index():

    return jsonify({

        "ok": True,

        "name":
            "STEAL THE EGG SERVER",

        "status":
            "online"
    })


@app.get("/health")
def health():

    return jsonify({
        "ok": True
    })


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    print(
        "BOT_TOKEN:",
        "SET" if BOT_TOKEN else "NOT SET"
    )

    print(
        "BOT_TOKEN length:",
        len(BOT_TOKEN)
    )

    print(
        f"Server starting on port {PORT}"
    )

    app.run(
        host="0.0.0.0",
        port=PORT
    )
