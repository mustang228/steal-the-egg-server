"""
STEAL THE EGG - админ-бот (панель управления).

Управление игрой прямо из Telegram, без Mini App:
  - найти игрока по ID или @username
  - выдать / удалить яйца
  - выдать / забрать Egg Coins, Tap Coins, XP
  - выдать сундук, предмет-бустер, питомца
  - заблокировать / разблокировать игрока
  - бонус Egg Coins сразу всем игрокам
  - статистика, топ игроков, журнал действий

Доступ ТОЛЬКО у Telegram ID из переменной ADMIN_IDS.

Переменные окружения:
  ADMIN_BOT_TOKEN  токен ОТДЕЛЬНОГО бота из @BotFather
  ADMIN_IDS        твой Telegram ID (несколько - через запятую)
  DB_PATH          та же база, что у игры (если задавал для игры)

Запуск:
  1) вместе с игрой: server.py сам стартует бота в фоне,
     если заданы ADMIN_BOT_TOKEN и ADMIN_IDS;
  2) отдельно:  python admin_bot.py
     (только если бот и игра работают на одной машине с одной базой).

Зависимостей нет - только стандартная библиотека Python.
"""

import html
import json
import logging
import os
import re
import threading
import time
import urllib.error
import urllib.request
from collections import Counter

import database

log = logging.getLogger('admin_bot')

API_BASE = os.getenv(
    'TELEGRAM_API_BASE',
    'https://api.telegram.org'
).rstrip('/')

MAX_AMOUNT = 100_000_000
MAX_EGG_QTY = 100

# Названия из игры. server.py передаёт их через configure().
CATALOG = {
    'eggs': {},
    'chests': {},
    'items': {},
    'pets': {}
}

# Что сейчас ждёт от админа: {admin_id: {...}}
pending = {}


# =========================================================
# НАСТРОЙКИ
# =========================================================
def token():
    return os.getenv(
        'ADMIN_BOT_TOKEN',
        ''
    ).strip()


def admin_ids():
    raw = os.getenv(
        'ADMIN_IDS',
        ''
    )
    result = set()
    for part in re.split(r'[,\s;]+', raw):
        part = part.strip()
        if part.lstrip('-').isdigit():
            result.add(int(part))
    return result


def configure(eggs, chests, items, pets):
    """Передать каталоги из server.py (id -> кортеж, где [0] - название)."""
    CATALOG['eggs'] = {
        int(k): v[0] for k, v in eggs.items()
    }
    CATALOG['chests'] = {
        int(k): v[0] for k, v in chests.items()
    }
    CATALOG['items'] = {
        int(k): v[0] for k, v in items.items()
    }
    CATALOG['pets'] = {
        int(k): v[0] for k, v in pets.items()
    }


def names(kind):
    """{id: название}. Яйца и питомцев при необходимости берём из БД."""
    if CATALOG.get(kind):
        return CATALOG[kind]
    result = {}
    try:
        if kind == 'eggs':
            for row in database.get_all_egg_types():
                result[int(row['egg_id'])] = row['name']
        elif kind == 'pets':
            for row in database.get_all_pets():
                result[int(row['pet_id'])] = row['name']
    except Exception:
        pass
    if not result:
        label = {
            'eggs': 'Яйцо',
            'chests': 'Сундук',
            'items': 'Предмет',
            'pets': 'Питомец'
        }[kind]
        count = {
            'eggs': 20,
            'chests': 10,
            'items': 3,
            'pets': 7
        }[kind]
        result = {
            i: f'{label} #{i}'
            for i in range(1, count + 1)
        }
    return result


def name_of(kind, item_id):
    return names(kind).get(
        int(item_id),
        f'#{item_id}'
    )


# =========================================================
# TELEGRAM API (urllib, без сторонних библиотек)
# =========================================================
def tg(method, **params):
    data = json.dumps(
        params
    ).encode('utf-8')
    request = urllib.request.Request(
        f'{API_BASE}/bot{token()}/{method}',
        data=data,
        headers={
            'Content-Type': 'application/json'
        }
    )
    timeout = int(
        params.get('timeout', 0)
    ) + 15
    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout
        ) as response:
            return json.loads(
                response.read().decode('utf-8')
            )
    except urllib.error.HTTPError as error:
        try:
            return json.loads(
                error.read().decode('utf-8')
            )
        except Exception:
            return {
                'ok': False,
                'description': str(error)
            }


def btn(text, data):
    return {
        'text': text,
        'callback_data': data
    }


def kb(rows):
    return {
        'inline_keyboard': rows
    }


def show(chat_id, message_id, text, markup=None):
    """Изменить сообщение (если есть message_id), иначе отправить новое."""
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    if markup:
        payload['reply_markup'] = markup
    if message_id:
        result = tg(
            'editMessageText',
            message_id=message_id,
            **payload
        )
        if result.get('ok'):
            return
        if 'not modified' in str(
            result.get('description', '')
        ):
            return
    tg(
        'sendMessage',
        **payload
    )


def esc(value):
    return html.escape(
        str(value)
    )


# =========================================================
# БАЗА: журнал, поиск, статистика
# =========================================================
def init_log():
    conn = database.get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                target_id INTEGER,
                details TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def add_log(admin_id, action, target_id=None, details=''):
    conn = database.get_connection()
    try:
        conn.execute(
            """
            INSERT INTO admin_log (
                admin_id,
                action,
                target_id,
                details
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                int(admin_id),
                action,
                target_id,
                details
            )
        )
        conn.commit()
    finally:
        conn.close()
    log.info(
        'ADMIN %s: %s target=%s %s',
        admin_id,
        action,
        target_id,
        details
    )


def recent_log(limit=15):
    conn = database.get_connection()
    try:
        return conn.execute(
            """
            SELECT *
            FROM admin_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),)
        ).fetchall()
    finally:
        conn.close()


def player_label(player):
    name = (
        player['username'] or ''
    ).strip()
    if not name:
        return f"ID {player['user_id']}"
    if re.fullmatch(r'[A-Za-z0-9_]{3,}', name):
        return '@' + name
    return name


def find_players(query):
    query = query.strip()
    if not query:
        return []
    bare = query.lstrip('@').strip()
    if bare.isdigit():
        player = database.get_player(int(bare))
        if player:
            return [player]
    needle = bare.casefold()
    conn = database.get_connection()
    try:
        rows = conn.execute(
            """
            SELECT *
            FROM players
            ORDER BY egg_coins DESC
            """
        ).fetchall()
    finally:
        conn.close()
    exact = [
        r for r in rows
        if (r['username'] or '').casefold() == needle
    ]
    if exact:
        return exact[:10]
    return [
        r for r in rows
        if needle in (r['username'] or '').casefold()
    ][:10]


def stats_text():
    conn = database.get_connection()
    try:
        players = conn.execute(
            'SELECT COUNT(*) c, COALESCE(SUM(egg_coins),0) e, '
            'COALESCE(SUM(tap_coins),0) t, '
            'COALESCE(SUM(blocked),0) b FROM players'
        ).fetchone()
        eggs = conn.execute(
            'SELECT COUNT(*) c FROM player_eggs'
        ).fetchone()
        market = conn.execute(
            "SELECT COUNT(*) c FROM market_listings "
            "WHERE status = 'active'"
        ).fetchone()
        today = conn.execute(
            'SELECT COUNT(*) c FROM players WHERE last_login = ?',
            (time.strftime('%Y-%m-%d'),)
        ).fetchone()
    finally:
        conn.close()
    return (
        '📊 <b>Статистика</b>\n\n'
        f"👥 Игроков: <b>{players['c']}</b>"
        f" (заблокировано: {players['b']})\n"
        f"🟢 Заходили сегодня: <b>{today['c']}</b>\n"
        f"🥚 Egg Coins у всех: <b>{players['e']:,}</b>\n"
        f"👆 Tap Coins у всех: <b>{players['t']:,}</b>\n"
        f"🥚 Яиц на руках: <b>{eggs['c']}</b>\n"
        f"🏪 Лотов на рынке: <b>{market['c']}</b>"
    )


# =========================================================
# ЭКРАНЫ
# =========================================================
def menu_screen():
    text = (
        '🛠 <b>Панель управления STEAL THE EGG</b>\n\n'
        'Выбери действие или просто отправь ID / @username игрока.'
    )
    markup = kb([
        [
            btn('🔎 Найти игрока', 'find'),
            btn('🏆 Топ игроков', 'top')
        ],
        [
            btn('🎁 Бонус всем', 'all'),
            btn('📊 Статистика', 'stats')
        ],
        [
            btn('📜 Журнал действий', 'log')
        ]
    ])
    return text, markup


def card_screen(uid, note=''):
    player = database.get_player(uid)
    if not player:
        return (
            '❌ Игрок не найден.',
            kb([[btn('◀️ Меню', 'menu')]])
        )
    eggs = database.get_player_eggs(uid)
    chests = database.get_player_chests(uid)
    pets = database.get_player_pets(uid)
    blocked = bool(player['blocked'])
    lines = []
    if note:
        lines.append(note)
        lines.append('')
    lines += [
        f"{esc(player['avatar'] or '🥚')} "
        f"<b>{esc(player_label(player))}</b>",
        f'ID: <code>{uid}</code>',
        '',
        f"💰 Egg Coins: <b>{int(player['egg_coins']):,}</b>",
        f"👆 Tap Coins: <b>{int(player['tap_coins']):,}</b>",
        f"⭐ Уровень {int(player['level'])} "
        f"({int(player['xp'])} XP)",
        f'🥚 Яиц: <b>{len(eggs)}</b> '
        f'(разных: {len(set(eggs))})',
        f'🎁 Сундуков: {len(chests)} · 🐾 Питомцев: {len(pets)}',
    ]
    if blocked:
        lines.append('')
        lines.append('🚫 <b>Заблокирован</b>')
    u = str(uid)
    markup = kb([
        [
            btn('🥚 + Яйцо', f'ea:{u}'),
            btn('🗑 − Яйцо', f'er:{u}')
        ],
        [
            btn('💰 + Egg Coins', f'cn:{u}:ec:a'),
            btn('💰 − Egg Coins', f'cn:{u}:ec:r')
        ],
        [
            btn('👆 + Tap Coins', f'cn:{u}:tc:a'),
            btn('👆 − Tap Coins', f'cn:{u}:tc:r')
        ],
        [
            btn('⭐ + XP', f'cn:{u}:xp:a'),
            btn('🎁 Сундук', f'ch:{u}')
        ],
        [
            btn('⚡ Бустер', f'it:{u}'),
            btn('🐾 Питомец', f'pt:{u}')
        ],
        [
            btn(
                '✅ Разблокировать' if blocked else '🚫 Заблокировать',
                f'bl:{u}'
            ),
            btn('🔄 Обновить', f'p:{u}')
        ],
        [
            btn('◀️ Меню', 'menu')
        ]
    ])
    return '\n'.join(lines), markup


def grid(buttons, per_row=2):
    return [
        buttons[i:i + per_row]
        for i in range(0, len(buttons), per_row)
    ]


def pick_list_screen(uid, kind, action, title, note=''):
    """Список из каталога: kind = eggs/chests/items/pets."""
    buttons = [
        btn(name, f'{action}:{uid}:{item_id}')
        for item_id, name in names(kind).items()
    ]
    rows = grid(buttons)
    rows.append([btn('◀️ К игроку', f'p:{uid}')])
    text = f'{note}\n\n{title}' if note else title
    return text, kb(rows)


def qty_screen(op, uid, egg_id):
    name = esc(name_of('eggs', egg_id))
    verb = 'выдать' if op == 'a' else 'удалить'
    quick = [1, 3, 5, 10, 25]
    row = [
        btn(str(q), f'eq:{op}:{uid}:{egg_id}:{q}')
        for q in quick
    ]
    rows = [row]
    if op == 'r':
        rows.append([
            btn('Все яйца этого типа', f'eq:r:{uid}:{egg_id}:all')
        ])
    rows.append([
        btn('◀️ Назад', f'{"ea" if op == "a" else "er"}:{uid}')
    ])
    return (
        f'Сколько штук <b>{name}</b> {verb}?\n'
        f'Нажми кнопку или отправь число (1–{MAX_EGG_QTY}).',
        kb(rows)
    )


AMOUNT_LABELS = {
    'ec': '💰 Egg Coins',
    'tc': '👆 Tap Coins',
    'xp': '⭐ XP'
}


def amount_screen(uid, kind, op):
    verb = 'выдать' if op == 'a' else 'забрать'
    label = AMOUNT_LABELS[kind]
    quick = [100, 500, 1000, 5000, 10000]
    rows = grid([
        btn(f'{q:,}', f'cq:{uid}:{kind}:{op}:{q}')
        for q in quick
    ], 3)
    rows.append([btn('◀️ Назад', f'p:{uid}')])
    return (
        f'Сколько {label} {verb}?\n'
        'Нажми кнопку или отправь число.',
        kb(rows)
    )


def all_confirm_screen(amount):
    conn = database.get_connection()
    try:
        count = conn.execute(
            'SELECT COUNT(*) c FROM players WHERE blocked = 0'
        ).fetchone()['c']
    finally:
        conn.close()
    return (
        f'🎁 Выдать по <b>{amount:,}</b> Egg Coins '
        f'всем игрокам ({count})?\n'
        f'Всего будет выдано: <b>{amount * count:,}</b>.',
        kb([
            [
                btn('✅ Да, выдать', f'ak:{amount}'),
                btn('❌ Отмена', 'menu')
            ]
        ])
    )


# =========================================================
# ДЕЙСТВИЯ (меняют базу и пишут журнал)
# =========================================================
def do_give_eggs(admin, uid, egg_id, qty):
    for _ in range(qty):
        database.add_egg(uid, egg_id)
    name = name_of('eggs', egg_id)
    add_log(admin, 'egg_add', uid, f'{name} x{qty}')
    return f'✅ Выдано: <b>{esc(name)}</b> × {qty}'


def do_remove_eggs(admin, uid, egg_id, qty):
    have = database.get_egg_count(uid, egg_id)
    qty = have if qty == 'all' else min(int(qty), have)
    removed = 0
    for _ in range(qty):
        if database.remove_one_egg(uid, egg_id):
            removed += 1
    name = name_of('eggs', egg_id)
    add_log(admin, 'egg_remove', uid, f'{name} x{removed}')
    if not removed:
        return '⚠️ У игрока нет такого яйца.'
    return f'🗑 Удалено: <b>{esc(name)}</b> × {removed}'


def do_amount(admin, uid, kind, op, amount):
    player = database.get_player(uid)
    if not player:
        return '❌ Игрок не найден.'
    field = {
        'ec': 'egg_coins',
        'tc': 'tap_coins',
        'xp': 'xp'
    }[kind]
    before = int(player[field])
    if kind == 'xp':
        database.add_xp(uid, amount)
    elif kind == 'ec':
        database.add_egg_coins(
            uid,
            amount if op == 'a' else -amount
        )
    else:
        database.add_tap_coins(
            uid,
            amount if op == 'a' else -amount
        )
    after = int(database.get_player(uid)[field])
    delta = after - before
    add_log(
        admin,
        f'{kind}_{"add" if op == "a" else "remove"}',
        uid,
        f'{delta:+d} ({before} -> {after})'
    )
    return (
        f'✅ {AMOUNT_LABELS[kind]}: {before:,} → <b>{after:,}</b> '
        f'({delta:+,})'
    )


def do_give_all(admin, amount):
    conn = database.get_connection()
    try:
        cursor = conn.execute(
            'UPDATE players SET egg_coins = egg_coins + ? '
            'WHERE blocked = 0',
            (int(amount),)
        )
        conn.commit()
        count = cursor.rowcount
    finally:
        conn.close()
    add_log(admin, 'bonus_all', None, f'+{amount} x {count} игроков')
    return count


# =========================================================
# ВВОД ТЕКСТА
# =========================================================
def parse_number(text, maximum):
    cleaned = re.sub(r'[\s_,]', '', text)
    if not cleaned.isdigit():
        return None
    value = int(cleaned)
    if not 1 <= value <= maximum:
        return None
    return value


def open_search_result(chat, mid, query):
    found = find_players(query)
    if not found:
        show(
            chat,
            mid,
            '❌ Никого не нашёл. Отправь ID или @username ещё раз.',
            kb([[btn('◀️ Меню', 'menu')]])
        )
        return
    if len(found) == 1:
        text, markup = card_screen(int(found[0]['user_id']))
        show(chat, mid, text, markup)
        return
    rows = [
        [btn(
            f"{player_label(p)} · {int(p['egg_coins']):,} 🥚",
            f"p:{p['user_id']}"
        )]
        for p in found
    ]
    rows.append([btn('◀️ Меню', 'menu')])
    show(chat, mid, 'Нашлось несколько игроков:', kb(rows))


def handle_text(admin, chat, text):
    text = (text or '').strip()
    if text.split('@')[0] in ('/start', '/menu'):
        pending.pop(admin, None)
        show(chat, None, *menu_screen())
        return
    if text.startswith('/cancel'):
        pending.pop(admin, None)
        show(chat, None, 'Отменено.', kb([[btn('◀️ Меню', 'menu')]]))
        return
    if text.startswith('/log'):
        show(chat, None, *log_screen())
        return
    state = pending.get(admin)
    if not state:
        open_search_result(chat, None, text)
        return
    kind = state['t']
    if kind == 'search':
        pending.pop(admin, None)
        open_search_result(chat, None, text)
    elif kind == 'qty':
        value = parse_number(text, MAX_EGG_QTY)
        if value is None:
            show(chat, None, f'Нужно целое число от 1 до {MAX_EGG_QTY}.')
            return
        pending.pop(admin, None)
        if state['op'] == 'a':
            note = do_give_eggs(admin, state['uid'], state['egg'], value)
        else:
            note = do_remove_eggs(admin, state['uid'], state['egg'], value)
        show(chat, None, *card_screen(state['uid'], note))
    elif kind == 'amount':
        value = parse_number(text, MAX_AMOUNT)
        if value is None:
            show(chat, None, f'Нужно целое число от 1 до {MAX_AMOUNT:,}.')
            return
        pending.pop(admin, None)
        note = do_amount(admin, state['uid'], state['kind'], state['op'], value)
        show(chat, None, *card_screen(state['uid'], note))
    elif kind == 'all':
        value = parse_number(text, MAX_AMOUNT)
        if value is None:
            show(chat, None, f'Нужно целое число от 1 до {MAX_AMOUNT:,}.')
            return
        pending.pop(admin, None)
        show(chat, None, *all_confirm_screen(value))


def log_screen():
    rows = recent_log(15)
    if not rows:
        return (
            '📜 Журнал пуст.',
            kb([[btn('◀️ Меню', 'menu')]])
        )
    lines = ['📜 <b>Последние действия</b> (время UTC)\n']
    for r in rows:
        target = f" → <code>{r['target_id']}</code>" if r['target_id'] else ''
        lines.append(
            f"{esc(r['created_at'][5:16])} · {esc(r['action'])}"
            f"{target} · {esc(r['details'] or '')}"
        )
    return '\n'.join(lines), kb([[btn('◀️ Меню', 'menu')]])


# =========================================================
# КНОПКИ
# =========================================================
def handle_callback(admin, chat, mid, data):
    parts = data.split(':')
    cmd = parts[0]
    # любая кнопка отменяет ожидание текста;
    # нужные ветки ниже ставят его заново
    pending.pop(admin, None)

    if cmd == 'menu':
        show(chat, mid, *menu_screen())

    elif cmd == 'find':
        pending[admin] = {'t': 'search'}
        show(
            chat, mid,
            '🔎 Отправь ID или @username игрока '
            '(можно часть имени).',
            kb([[btn('◀️ Меню', 'menu')]])
        )

    elif cmd == 'stats':
        show(chat, mid, stats_text(), kb([[btn('◀️ Меню', 'menu')]]))

    elif cmd == 'log':
        show(chat, mid, *log_screen())

    elif cmd == 'top':
        top = database.get_top_players(10)
        rows = [
            [btn(
                f"{i}. {player_label(p)} · {int(p['egg_coins']):,} 🥚",
                f"p:{p['user_id']}"
            )]
            for i, p in enumerate(top, start=1)
        ]
        rows.append([btn('◀️ Меню', 'menu')])
        show(chat, mid, '🏆 <b>Топ игроков</b> — нажми, чтобы открыть:', kb(rows))

    elif cmd == 'p':
        show(chat, mid, *card_screen(int(parts[1])))

    # ---------------- яйца ----------------
    elif cmd == 'ea':
        uid = int(parts[1])
        show(chat, mid, *pick_list_screen(
            uid, 'eggs', 'ea2', '🥚 Какое яйцо выдать?'
        ))

    elif cmd == 'ea2':
        uid, egg = int(parts[1]), int(parts[2])
        pending[admin] = {'t': 'qty', 'op': 'a', 'uid': uid, 'egg': egg}
        show(chat, mid, *qty_screen('a', uid, egg))

    elif cmd == 'er':
        uid = int(parts[1])
        owned = Counter(database.get_player_eggs(uid))
        if not owned:
            show(chat, mid, *card_screen(uid, '⚠️ У игрока нет яиц.'))
            return
        buttons = [
            btn(f'{name_of("eggs", e)} × {n}', f'er2:{uid}:{e}')
            for e, n in sorted(owned.items())
        ]
        rows = grid(buttons)
        rows.append([btn('◀️ К игроку', f'p:{uid}')])
        show(chat, mid, '🗑 Какое яйцо удалить?', kb(rows))

    elif cmd == 'er2':
        uid, egg = int(parts[1]), int(parts[2])
        pending[admin] = {'t': 'qty', 'op': 'r', 'uid': uid, 'egg': egg}
        show(chat, mid, *qty_screen('r', uid, egg))

    elif cmd == 'eq':
        op, uid, egg, qty = parts[1], int(parts[2]), int(parts[3]), parts[4]
        if op == 'a':
            note = do_give_eggs(admin, uid, egg, int(qty))
        else:
            note = do_remove_eggs(
                admin, uid, egg,
                'all' if qty == 'all' else int(qty)
            )
        show(chat, mid, *card_screen(uid, note))

    # ---------------- монеты / XP ----------------
    elif cmd == 'cn':
        uid, kind, op = int(parts[1]), parts[2], parts[3]
        pending[admin] = {'t': 'amount', 'uid': uid, 'kind': kind, 'op': op}
        show(chat, mid, *amount_screen(uid, kind, op))

    elif cmd == 'cq':
        uid, kind, op, amount = int(parts[1]), parts[2], parts[3], int(parts[4])
        note = do_amount(admin, uid, kind, op, amount)
        show(chat, mid, *card_screen(uid, note))

    # ---------------- сундуки / бустеры / питомцы ----------------
    elif cmd == 'ch':
        show(chat, mid, *pick_list_screen(
            int(parts[1]), 'chests', 'chg', '🎁 Какой сундук выдать?'
        ))

    elif cmd == 'chg':
        uid, item = int(parts[1]), int(parts[2])
        database.add_chest(uid, item)
        name = name_of('chests', item)
        add_log(admin, 'chest_add', uid, name)
        show(chat, mid, *pick_list_screen(
            uid, 'chests', 'chg', '🎁 Выдать ещё сундук?',
            f'✅ Выдан: <b>{esc(name)}</b>'
        ))

    elif cmd == 'it':
        show(chat, mid, *pick_list_screen(
            int(parts[1]), 'items', 'itg', '⚡ Какой бустер выдать?'
        ))

    elif cmd == 'itg':
        uid, item = int(parts[1]), int(parts[2])
        database.add_item(uid, item)
        name = name_of('items', item)
        add_log(admin, 'item_add', uid, name)
        show(chat, mid, *pick_list_screen(
            uid, 'items', 'itg', '⚡ Выдать ещё бустер?',
            f'✅ Выдан: <b>{esc(name)}</b>'
        ))

    elif cmd == 'pt':
        show(chat, mid, *pick_list_screen(
            int(parts[1]), 'pets', 'ptg', '🐾 Какого питомца выдать?'
        ))

    elif cmd == 'ptg':
        uid, item = int(parts[1]), int(parts[2])
        name = name_of('pets', item)
        added, auto = database.grant_pet(uid, item)
        if added:
            add_log(admin, 'pet_add', uid, name)
            note = f'✅ Выдан: <b>{esc(name)}</b>'
            if auto:
                note += ' (включён автоматически)'
        else:
            note = f'⚠️ У игрока уже есть {esc(name)}.'
        show(chat, mid, *pick_list_screen(
            uid, 'pets', 'ptg', '🐾 Выдать ещё питомца?', note
        ))

    # ---------------- блокировка ----------------
    elif cmd == 'bl':
        uid = int(parts[1])
        if uid in admin_ids():
            show(chat, mid, *card_screen(uid, '⚠️ Админа блокировать нельзя.'))
            return
        if database.is_blocked(uid):
            database.unblock_player(uid)
            add_log(admin, 'unblock', uid)
            note = '✅ Игрок разблокирован.'
        else:
            database.block_player(uid)
            add_log(admin, 'block', uid)
            note = '🚫 Игрок заблокирован.'
        show(chat, mid, *card_screen(uid, note))

    # ---------------- бонус всем ----------------
    elif cmd == 'all':
        pending[admin] = {'t': 'all'}
        rows = grid([
            btn(f'{q:,}', f'aq:{q}')
            for q in (50, 100, 500, 1000, 5000)
        ], 3)
        rows.append([btn('◀️ Меню', 'menu')])
        show(
            chat, mid,
            '🎁 <b>Бонус всем игрокам</b>\n'
            'Сколько Egg Coins выдать каждому? '
            'Нажми кнопку или отправь число.',
            kb(rows)
        )

    elif cmd == 'aq':
        show(chat, mid, *all_confirm_screen(int(parts[1])))

    elif cmd == 'ak':
        amount = int(parts[1])
        count = do_give_all(admin, amount)
        show(
            chat, mid,
            f'✅ Выдано по <b>{amount:,}</b> Egg Coins '
            f'игрокам: <b>{count}</b>.',
            kb([[btn('◀️ Меню', 'menu')]])
        )

    else:
        show(chat, mid, *menu_screen())


# =========================================================
# ДИСПЕТЧЕР ОБНОВЛЕНИЙ
# =========================================================
def handle_update(update):
    message = update.get('message')
    callback = update.get('callback_query')
    admins = admin_ids()

    if message:
        sender = (message.get('from') or {}).get('id')
        chat = message['chat']['id']
        text = message.get('text') or ''
        if text.startswith('/id'):
            # ID может узнать кто угодно - это нужно для настройки
            show(chat, None, f'Твой Telegram ID: <code>{sender}</code>')
            return
        if message['chat'].get('type') != 'private':
            return
        if sender not in admins:
            log.warning('Отказ в доступе: %s', sender)
            show(chat, None, '⛔ Нет доступа.')
            return
        handle_text(sender, chat, text)

    elif callback:
        sender = callback['from']['id']
        tg('answerCallbackQuery', callback_query_id=callback['id'])
        if sender not in admins:
            return
        msg = callback.get('message') or {}
        chat = (msg.get('chat') or {}).get('id')
        if chat is None:
            return
        try:
            handle_callback(
                sender, chat, msg.get('message_id'),
                callback.get('data') or ''
            )
        except Exception:
            log.exception('Ошибка в кнопке %s', callback.get('data'))
            show(
                chat, None,
                '❌ Ошибка при выполнении. Подробности в логе сервера.',
                kb([[btn('◀️ Меню', 'menu')]])
            )


# =========================================================
# ЗАПУСК
# =========================================================
_started = False
_stop = threading.Event()
_lock_file = None


def _acquire_single_instance():
    """
    Только один процесс на машине может опрашивать Telegram
    (иначе будет ошибка 409 и двойные ответы, например при
    нескольких воркерах gunicorn). Замок снимается сам при
    завершении процесса.
    """
    global _lock_file
    try:
        import fcntl
    except ImportError:
        return True  # Windows: замок не нужен для локальных тестов
    import tempfile
    path = os.path.join(
        tempfile.gettempdir(),
        'steal_the_egg_admin_bot.lock'
    )
    try:
        _lock_file = open(path, 'w')
        fcntl.flock(
            _lock_file,
            fcntl.LOCK_EX | fcntl.LOCK_NB
        )
        return True
    except OSError:
        return False


def run():
    init_log()
    tg('deleteWebhook')
    me = tg('getMe')
    if not me.get('ok'):
        log.error('Админ-бот: неверный ADMIN_BOT_TOKEN (%s)', me)
        return
    log.warning(
        'Админ-бот запущен: @%s, админов: %d',
        me['result'].get('username'),
        len(admin_ids())
    )
    offset = 0
    while not _stop.is_set():
        try:
            reply = tg(
                'getUpdates',
                offset=offset,
                timeout=30,
                allowed_updates=['message', 'callback_query']
            )
            if not reply.get('ok'):
                time.sleep(5)
                continue
            for update in reply.get('result', []):
                offset = update['update_id'] + 1
                try:
                    handle_update(update)
                except Exception:
                    log.exception('Ошибка обработки обновления')
        except Exception:
            log.exception('Сбой опроса Telegram')
            time.sleep(5)


def start_in_thread():
    """Запустить бота в фоне. Вернёт True, если бот стартовал."""
    global _started
    if _started:
        return True
    if not token():
        print('[admin_bot] ADMIN_BOT_TOKEN не задан - админ-бот выключен.')
        return False
    if not admin_ids():
        print('[admin_bot] ADMIN_IDS не задан - админ-бот выключен.')
        return False
    if not _acquire_single_instance():
        print('[admin_bot] уже запущен в другом процессе - пропускаю.')
        return False
    thread = threading.Thread(
        target=run,
        name='admin-bot',
        daemon=True
    )
    thread.start()
    _started = True
    return True


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )
    if not token() or not admin_ids():
        raise SystemExit(
            'Задай ADMIN_BOT_TOKEN и ADMIN_IDS в переменных окружения.'
        )
    try:
        import server
        configure(
            server.EGGS,
            server.CHESTS,
            server.ITEMS,
            server.PETS
        )
    except Exception as error:
        log.warning('Каталоги из server.py не загружены: %s', error)
    run()
