import os
import time
import hmac
import hashlib
import json
import random
from datetime import date
from urllib.parse import parse_qsl

from flask import Flask, request, jsonify, send_from_directory

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

app = Flask(__name__, static_folder=os.path.dirname(os.path.abspath(__file__)), static_url_path='')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
PORT = int(os.getenv('PORT', '8080'))
WITHDRAWAL_BOT = 'https://t.me/stealtheegg_vyvod_bot'

# id: (name, price, rarity)
EGGS = {
    1: ('🥚 Обычное яйцо', 100, '⚪ Обычное'),
    2: ('🥈 Серебряное яйцо', 600, '🟢 Необычное'),
    3: ('🥇 Золотое яйцо', 700, '🔵 Редкое'),
    4: ('💎 Алмазное яйцо', 800, '🟣 Эпическое'),
    5: ('🔥 Огненное яйцо', 900, '🟣 Эпическое'),
    6: ('❄️ Ледяное яйцо', 1000, '🟡 Легендарное'),
    7: ('🌌 Космическое яйцо', 1100, '🟡 Легендарное'),
    8: ('👑 Королевское яйцо', 1200, '🔴 Мифическое'),
    9: ('⚡ Молниевое яйцо', 1300, '🔴 Мифическое'),
    10: ('🌑 Тёмное яйцо', 1400, '🔴 Мифическое'),
}

ITEMS = {
    1: ('⚡ Бустер тапов', 150, '+2 Tap Coins за тап на 10 минут'),
    2: ('🥚 Бустер Egg Coins', 250, '+1 Egg Coin к наградам игр на 10 минут'),
    3: ('🎁 XP Бустер', 200, 'В 2 раза больше XP на 10 минут'),
}

ACH = {
    1: ('👆 Первый тап', 'Сделать первый тап', 10),
    2: ('💰 Богатей', 'Накопить 1000 Tap Coins', 25),
    3: ('🥚 Коллекционер', 'Собрать 5 яиц', 50),
    4: ('🥚 Яичный мастер', 'Собрать 10 разных яиц', 100),
    5: ('🎮 Игрок', 'Сыграть 10 мини-игр', 50),
    6: ('🔥 Серия', 'Получить серию 7 дней', 100),
    7: ('⭐ Уровень 10', 'Достичь 10 уровня', 150),
    8: ('👾 Охотник на боссов', 'Нанести 100 урона боссу', 100),
}

AVATARS = ['🥚', '🐣', '🐥', '🐔', '🦊', '🐼', '🐸', '🐵', '😎', '🤖', '👽', '👾', '🤑', '🔥', '⚡', '💎', '👑', '🌌', '🌑', '🍀']

active = {}
guess = {}
math = {}
tic = {}
last_tap = {}
last_game = {}
last_boss = {}
boss_hp = 10000

database.init_database()


def user():
    raw = request.headers.get('X-Telegram-Init-Data', '')
    if not raw:
        return None, 'Открой Mini App через Telegram.'
    if not BOT_TOKEN:
        return None, 'На сервере не задан BOT_TOKEN.'

    p = dict(parse_qsl(raw, keep_blank_values=True))
    received = p.pop('hash', None)
    if not received:
        return None, 'Нет hash Telegram.'

    check = '\n'.join(f'{k}={p[k]}' for k in sorted(p))
    secret = hmac.new(b'WebAppData', BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, received):
        return None, 'Неверная подпись Telegram.'

    try:
        if time.time() - int(p.get('auth_date', '0')) > 86400:
            return None, 'Сессия Telegram устарела.'
        u = json.loads(p['user'])
    except Exception:
        return None, 'Некорректные данные Telegram.'

    uid = int(u['id'])
    database.ensure_player(uid, u.get('username', '') or '')
    if database.is_blocked(uid):
        return None, 'Твой аккаунт заблокирован.'
    return u, None


def auth():
    u, e = user()
    return (u, None) if not e else (None, (jsonify(ok=False, error=e), 401))


def expiry(uid, item_id):
    return active.get((uid, item_id), 0)


def has(uid, item_id):
    return expiry(uid, item_id) > time.time()


def add_xp(uid, amount):
    database.add_xp(uid, amount * (2 if has(uid, 3) else 1))


def add_game_coins(uid, amount):
    database.add_egg_coins(uid, amount + (1 if has(uid, 2) else 0))


def egg_counts(uid):
    eggs = database.get_player_eggs(uid)
    return {str(i): eggs.count(i) for i in EGGS}


def snap(uid):
    tap, egg = database.get_balance(uid)
    current_xp, level = database.get_progress(uid)
    streak, last = database.get_login_info(uid)
    t = database.get_daily_tasks(uid)
    owned = egg_counts(uid)

    xp_required = max(100, level * 100)

    return {
        'tap_coins': int(tap),
        'egg_coins': int(egg),
        'xp': int(current_xp),
        'level': int(level),
        'xp_required': int(xp_required),
        'streak': int(streak),
        'last_login': last,
        'eggs_total': sum(owned.values()),
        'eggs': owned,
        'avatar': database.get_avatar(uid),
        'avatars': AVATARS,
        'achievements': database.get_achievements(uid),
        'active_items': {
            str(i): max(0, int(expiry(uid, i) - time.time()))
            for i in ITEMS if has(uid, i)
        },
        'tasks': {
            'taps': int(t[0]),
            'games': int(t[1]),
            'eggs': int(t[2]),
            'tap_claimed': database.has_daily_task_claim(uid, 'tap'),
            'game_claimed': database.has_daily_task_claim(uid, 'game'),
            'egg_claimed': database.has_daily_task_claim(uid, 'egg'),
        },
    }


def achievements(uid):
    tap, _ = database.get_balance(uid)
    eggs = database.get_player_eggs(uid)
    _, lev = database.get_progress(uid)
    streak, _ = database.get_login_info(uid)
    tasks = database.get_daily_tasks(uid)

    # games is stored as today's task counter; this keeps the original game's behavior.
    checks = {
        1: tap >= 1,
        2: tap >= 1000,
        3: len(eggs) >= 5,
        4: len(set(eggs)) >= 10,
        5: tasks[1] >= 10,
        6: streak >= 7,
        7: lev >= 10,
        8: database.get_boss_damage(uid) >= 100,
    }
    unlocked = []
    for i, ok in checks.items():
        if ok and not database.has_achievement(uid, i):
            database.add_achievement(uid, i)
            database.add_egg_coins(uid, ACH[i][2])
            unlocked.append({'id': i, 'name': ACH[i][0], 'reward': ACH[i][2]})
    return unlocked


def json_error(msg, status=400):
    return jsonify(ok=False, error=msg), status


@app.get('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


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
        reward = min(10 + streak * 5, 100)
        database.add_egg_coins(uid, reward)
        add_xp(uid, 10)
        claimed = True

    return jsonify(
        ok=True,
        user={'id': uid, 'username': u.get('username', ''), 'first_name': u.get('first_name', '')},
        login={'claimed': claimed, 'streak': streak, 'reward': reward},
        data=snap(uid),
        new_achievements=achievements(uid),
    )


@app.get('/api/state')
def state():
    u, f = auth()
    if f:
        return f
    return jsonify(ok=True, data=snap(int(u['id'])))


@app.post('/api/tap')
def tap():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    now = time.time()
    amount = max(1, min(int((request.json or {}).get('amount', 1)), 40))
    old = [t for t in last_tap.get(uid, []) if now - t < 2]
    if len(old) + amount > 80:
        return json_error('Слишком быстро. Подожди немного.', 429)
    old += [now] * amount
    last_tap[uid] = old

    gain = amount * (3 if has(uid, 1) else 1)
    database.add_tap_coins(uid, gain)
    database.add_task_tap(uid, amount)
    add_xp(uid, amount)
    return jsonify(ok=True, gained=gain, data=snap(uid), new_achievements=achievements(uid))


@app.post('/api/exchange')
def exchange():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    tap, _ = database.get_balance(uid)
    n = tap // 30
    if n < 1:
        return json_error('Нужно минимум 30 Tap Coins.')
    spent = n * 30
    received = n * 10
    if not database.remove_tap_coins(uid, spent):
        return json_error('Не удалось выполнить обмен.')
    database.add_egg_coins(uid, received)
    add_xp(uid, 5)
    return jsonify(ok=True, spent=spent, received=received, data=snap(uid))


def game_ok(uid):
    now = time.time()
    if now - last_game.get(uid, 0) < 1:
        return False
    last_game[uid] = now
    return True


@app.post('/api/game/guess/start')
def guess_start():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    if not game_ok(uid):
        return json_error('Подожди немного.', 429)
    guess[uid] = {'n': random.randint(1, 20), 'a': 0}
    return jsonify(ok=True, min=1, max=20, attempts=10)


@app.post('/api/game/guess/answer')
def guess_answer():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    g = guess.get(uid)
    if not g:
        return json_error('Игра не запущена.')
    try:
        v = int((request.json or {}).get('guess'))
    except (TypeError, ValueError):
        return json_error('Введите число.')
    if not 1 <= v <= 20:
        return json_error('Число от 1 до 20.')

    g['a'] += 1
    attempts = g['a']
    rewards = {1: 5, 2: 4, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1, 10: 1}

    if v == g['n']:
        reward = rewards[attempts]
        add_game_coins(uid, reward)
        database.add_task_game(uid)
        add_xp(uid, 10)
        number = g['n']
        guess.pop(uid, None)
        return jsonify(ok=True, result='win', reward=reward, number=number, attempts=attempts,
                        data=snap(uid), new_achievements=achievements(uid))

    if attempts >= 10:
        number = g['n']
        guess.pop(uid, None)
        database.add_task_game(uid)
        return jsonify(ok=True, result='lose', reward=0, number=number, attempts=attempts,
                        data=snap(uid), new_achievements=achievements(uid))

    return jsonify(ok=True, result='continue', hint='Больше!' if v < g['n'] else 'Меньше!', attempts=attempts)


@app.post('/api/game/math/start')
def math_start():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    if not game_ok(uid):
        return json_error('Подожди немного.', 429)

    a = random.randint(5, 30)
    b = random.randint(2, 20)
    op = random.choice(['+', '-', '*'])
    ans = a + b if op == '+' else a - b if op == '-' else a * b
    math[uid] = {'a': a, 'b': b, 'op': op, 'answer': ans}
    return jsonify(ok=True, question=f'{a} {op} {b} = ?')


def new_math_question(uid):
    a = random.randint(5, 30)
    b = random.randint(2, 20)
    op = random.choice(['+', '-', '*'])
    ans = a + b if op == '+' else a - b if op == '-' else a * b
    math[uid] = {'a': a, 'b': b, 'op': op, 'answer': ans}
    return f'{a} {op} {b} = ?'


@app.post('/api/game/math/answer')
def math_answer():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    game = math.get(uid)
    if not game:
        return json_error('Задание не запущено.')

    try:
        value = int((request.json or {}).get('answer'))
    except (TypeError, ValueError):
        return json_error('Введите число.')

    correct = game['answer']
    database.add_task_game(uid)

    if value == correct:
        math.pop(uid, None)
        reward = 4
        add_game_coins(uid, reward)
        add_xp(uid, 10)
        return jsonify(ok=True, result='win', correct=correct, reward=reward,
                        data=snap(uid), new_achievements=achievements(uid))

    # Wrong answer: immediately give a fresh example instead of ending the game.
    new_question = new_math_question(uid)
    return jsonify(ok=True, result='wrong', correct=correct, reward=0,
                    question=new_question, data=snap(uid), new_achievements=achievements(uid))


def winner(board):
    for a, b, c in ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7),
                    (2, 5, 8), (0, 4, 8), (2, 4, 6)):
        if board[a] != ' ' and board[a] == board[b] == board[c]:
            return board[a]
    return 'draw' if ' ' not in board else None


@app.post('/api/game/tic/start')
def tic_start():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    if not game_ok(uid):
        return json_error('Подожди немного.', 429)
    tic[uid] = [' '] * 9
    return jsonify(ok=True, board=tic[uid])


def finish_tic(uid, result, reward=0, xp_amount=0):
    if reward:
        add_game_coins(uid, reward)
    if xp_amount:
        add_xp(uid, xp_amount)
    database.add_task_game(uid)
    board = tic.pop(uid, [' '] * 9)
    return jsonify(ok=True, board=board, result=result, reward=reward,
                   data=snap(uid), new_achievements=achievements(uid))


@app.post('/api/game/tic/move')
def tic_move():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    board = tic.get(uid)
    if board is None:
        return json_error('Игра не запущена.')

    try:
        i = int((request.json or {}).get('index'))
    except (TypeError, ValueError):
        return json_error('Неверная клетка.')

    if i < 0 or i > 8:
        return json_error('Неверная клетка.')
    if board[i] != ' ':
        return json_error('Клетка уже занята.')

    board[i] = 'X'
    w = winner(board)
    if w == 'X':
        return finish_tic(uid, 'win', 5, 15)
    if w == 'draw':
        return finish_tic(uid, 'draw', 2, 10)

    empty = [pos for pos, value in enumerate(board) if value == ' ']
    if empty:
        board[random.choice(empty)] = 'O'

    w = winner(board)
    if w == 'O':
        return finish_tic(uid, 'lose', 0, 0)
    if w == 'draw':
        return finish_tic(uid, 'draw', 2, 10)

    return jsonify(ok=True, board=board, result='continue')


@app.get('/api/eggs')
def eggs():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    owned = egg_counts(uid)
    shop = {
        str(i): {'id': i, 'name': x[0], 'price': x[1], 'rarity': x[2]}
        for i, x in EGGS.items()
    }
    return jsonify(ok=True, shop=shop, owned=owned, total=sum(owned.values()))


@app.post('/api/eggs/buy')
def buy_egg():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    try:
        egg_id = int((request.json or {}).get('egg_id'))
    except (TypeError, ValueError):
        return json_error('Неверное яйцо.')

    if egg_id not in EGGS:
        return json_error('Такого яйца нет.')

    price = EGGS[egg_id][1]
    if not database.remove_egg_coins(uid, price):
        return json_error(f'Недостаточно Egg Coins. Нужно {price} 🥚.')

    database.add_egg(uid, egg_id)
    database.add_task_egg(uid)
    add_xp(uid, 15)
    return jsonify(ok=True, egg={'id': egg_id, 'name': EGGS[egg_id][0]},
                    data=snap(uid), new_achievements=achievements(uid))


@app.post('/api/eggs/open')
def open_egg():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    try:
        egg_id = int((request.json or {}).get('egg_id'))
    except (TypeError, ValueError):
        return json_error('Неверное яйцо.')
    if egg_id not in EGGS:
        return json_error('Такого яйца нет.')
    if not database.remove_one_egg(uid, egg_id):
        return json_error('У тебя нет этого яйца.')
    reward = 5 + egg_id * 2
    database.add_egg_coins(uid, reward)
    add_xp(uid, 20)
    return jsonify(ok=True, reward=reward, egg={'id': egg_id, 'name': EGGS[egg_id][0]}, data=snap(uid),
                    new_achievements=achievements(uid))


@app.get('/api/items')
def items():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    return jsonify(ok=True, items={
        str(i): {
            'id': i,
            'name': x[0],
            'price': x[1],
            'description': x[2],
            'count': database.get_item_count(uid, i),
            'active_seconds': max(0, int(expiry(uid, i) - time.time())),
        } for i, x in ITEMS.items()
    })


@app.post('/api/items/buy')
def buy_item():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    try:
        item_id = int((request.json or {}).get('item_id'))
    except (TypeError, ValueError):
        return json_error('Неверный предмет.')
    if item_id not in ITEMS:
        return json_error('Такого предмета нет.')
    price = ITEMS[item_id][1]
    if not database.remove_egg_coins(uid, price):
        return json_error(f'Недостаточно Egg Coins. Нужно {price} 🥚.')
    database.add_item(uid, item_id)
    add_xp(uid, 10)
    return jsonify(ok=True, data=snap(uid))


@app.post('/api/items/activate')
def activate_item():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    try:
        item_id = int((request.json or {}).get('item_id'))
    except (TypeError, ValueError):
        return json_error('Неверный предмет.')
    if item_id not in ITEMS or not database.remove_item(uid, item_id):
        return json_error('У тебя нет этого предмета.')
    active[(uid, item_id)] = time.time() + 600
    return jsonify(ok=True, data=snap(uid))


@app.get('/api/achievements')
def achievement_list():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    s = set(database.get_achievements(uid))
    return jsonify(ok=True, items=[
        {'id': i, 'name': x[0], 'description': x[1], 'reward': x[2], 'unlocked': i in s}
        for i, x in ACH.items()
    ])


@app.get('/api/leaderboard')
def leaderboard():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    players = database.get_top_players(10)
    for p in players:
        p['avatar'] = database.get_avatar(p['user_id'])
    return jsonify(ok=True, players=players, my_rank=database.get_player_rank(uid))


@app.post('/api/profile/avatar')
def set_avatar():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    avatar = str((request.json or {}).get('avatar', '')).strip()
    if avatar not in AVATARS:
        return json_error('Такой аватар недоступен.')
    database.set_avatar(uid, avatar)
    return jsonify(ok=True, avatar=avatar, data=snap(uid))


@app.get('/api/profile/avatars')
def avatars():
    u, f = auth()
    if f:
        return f
    return jsonify(ok=True, avatars=AVATARS, current=database.get_avatar(int(u['id'])))


@app.post('/api/daily/bonus')
def bonus():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    today = date.today().isoformat()
    if database.get_daily_bonus_date(uid) == today:
        return json_error('Бонус уже получен сегодня.')
    streak, _ = database.get_login_info(uid)
    reward = min(20 + streak * 5, 100)
    database.add_egg_coins(uid, reward)
    database.set_daily_bonus_date(uid)
    add_xp(uid, 20)
    return jsonify(ok=True, reward=reward, data=snap(uid))


@app.get('/api/daily/tasks')
def tasks():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    t = database.get_daily_tasks(uid)
    return jsonify(ok=True, tasks=[
        {'id': 'tap', 'title': '👆 Сделать 100 тапов', 'progress': min(t[0], 100), 'target': 100, 'reward': 25,
         'claimed': database.has_daily_task_claim(uid, 'tap')},
        {'id': 'game', 'title': '🎮 Сыграть 3 игры', 'progress': min(t[1], 3), 'target': 3, 'reward': 30,
         'claimed': database.has_daily_task_claim(uid, 'game')},
        {'id': 'egg', 'title': '🥚 Купить 1 яйцо', 'progress': min(t[2], 1), 'target': 1, 'reward': 40,
         'claimed': database.has_daily_task_claim(uid, 'egg')},
    ])


@app.post('/api/daily/tasks/claim')
def claim():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    task_id = (request.json or {}).get('task_id')
    rewards = {'tap': 25, 'game': 30, 'egg': 40}
    targets = {'tap': 100, 'game': 3, 'egg': 1}
    t = database.get_daily_tasks(uid)
    progress = {'tap': t[0], 'game': t[1], 'egg': t[2]}
    if task_id not in rewards or progress[task_id] < targets[task_id]:
        return json_error('Задание ещё не выполнено или неверное задание.')
    if not database.add_daily_task_claim(uid, task_id):
        return json_error('Задание уже получено.')
    database.add_egg_coins(uid, rewards[task_id])
    add_xp(uid, 15)
    return jsonify(ok=True, reward=rewards[task_id], data=snap(uid))


@app.get('/api/boss')
def boss():
    u, f = auth()
    if f:
        return f
    return jsonify(ok=True, hp=boss_hp, max_hp=10000, my_damage=database.get_boss_damage(int(u['id'])))


@app.post('/api/boss/attack')
def boss_attack():
    global boss_hp
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    now = time.time()
    if now - last_boss.get(uid, 0) < .7:
        return json_error('Подожди немного.', 429)
    last_boss[uid] = now
    damage = random.randint(5, 15)
    actual = min(damage, boss_hp)
    boss_hp -= actual
    database.add_boss_damage(uid, actual)
    add_xp(uid, 2)
    defeated = boss_hp <= 0
    if defeated:
        database.add_egg_coins(uid, 100)
        boss_hp = 10000
    return jsonify(ok=True, damage=actual, hp=boss_hp, max_hp=10000, defeated=defeated,
                    data=snap(uid), new_achievements=achievements(uid))


@app.get('/api/withdrawal')
def withdrawal():
    u, f = auth()
    if f:
        return f
    uid = int(u['id'])
    owned = egg_counts(uid)
    eggs = {
        str(i): {'id': i, 'name': EGGS[i][0], 'count': count}
        for i, count in ((int(k), v) for k, v in owned.items()) if count > 0
    }
    return jsonify(ok=True, bot=WITHDRAWAL_BOT, total=sum(owned.values()), eggs=eggs)


if __name__ == '__main__':
    database.init_database()
    app.run(host='0.0.0.0', port=PORT, debug=False)
