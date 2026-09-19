import os, time, hmac, hashlib, json, random
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

EGGS={1:('🥚 Обычное яйцо',100,'⚪ Обычное'),2:('🥚 Серебряное яйцо',600,'🟢 Необычное'),3:('🥚 Золотое яйцо',700,'🔵 Редкое'),4:('💎 Алмазное яйцо',800,'🟣 Эпическое'),5:('🔥 Огненное яйцо',900,'🟣 Эпическое'),6:('❄️ Ледяное яйцо',1000,'🟡 Легендарное'),7:('🌌 Космическое яйцо',1100,'🟡 Легендарное'),8:('👑 Королевское яйцо',1200,'🔴 Мифическое'),9:('⚡ Молниевое яйцо',1300,'🔴 Мифическое'),10:('🌑 Тёмное яйцо',1400,'🔴 Мифическое')}
ITEMS={1:('⚡ Бустер тапов',150,'+2 Tap Coins за тап на 10 минут'),2:('🥚 Бустер Egg Coins',250,'+1 Egg Coin к наградам игр на 10 минут'),3:('🎁 XP Бустер',200,'В 2 раза больше XP на 10 минут')}
ACH={1:('👆 Первый тап','Сделать первый тап',10),2:('💰 Богатей','Накопить 1000 Tap Coins',25),3:('🥚 Коллекционер','Собрать 5 яиц',50),4:('🥚 Яичный мастер','Собрать 10 разных яиц',100),5:('🎮 Игрок','Сыграть 10 мини-игр',50),6:('🔥 Серия','Получить серию 7 дней',100),7:('⭐ Уровень 10','Достичь 10 уровня',150),8:('👾 Охотник на боссов','Нанести 100 урона боссу',100)}
active={}; guess={}; math={}; tic={}; last_tap={}; last_game={}; last_boss={}
boss_hp=10000


def user():
    raw=request.headers.get('X-Telegram-Init-Data','')
    if not raw:return None,'Открой Mini App через Telegram.'
    if not BOT_TOKEN:return None,'На сервере не задан BOT_TOKEN.'
    p=dict(parse_qsl(raw,keep_blank_values=True)); received=p.pop('hash',None)
    if not received:return None,'Нет hash Telegram.'
    check='\n'.join(f'{k}={p[k]}' for k in sorted(p))
    secret=hmac.new(b'WebAppData',BOT_TOKEN.encode(),hashlib.sha256).digest()
    calc=hmac.new(secret,check.encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc,received):return None,'Неверная подпись Telegram.'
    try:
        if time.time()-int(p.get('auth_date','0'))>86400:return None,'Сессия Telegram устарела.'
        u=json.loads(p['user'])
    except Exception:return None,'Некорректные данные Telegram.'
    database.ensure_player(int(u['id']), u.get('username', '') or '')
    if database.is_blocked(int(u['id'])):return None, 'Твой аккаунт заблокирован.'
    return u,None

def auth():
    u,e=user()
    return (u,None) if not e else (None,(jsonify(ok=False,error=e),401))

def expiry(uid,i):
    return active.get((uid,i),0)
def has(uid,i):return expiry(uid,i)>time.time()
def xp(uid,n): database.add_xp(uid, n * (2 if has(uid, 3) else 1))
def eggcoins(uid,n): database.add_egg_coins(uid, n + (1 if has(uid, 2) else 0))

def snap(uid):
    tap,egg= database.get_balance(uid); x,l= database.get_progress(uid); streak,last= database.get_login_info(uid); t= database.get_daily_tasks(uid); eggs= database.get_player_eggs(uid)
    return {'tap_coins':tap,'egg_coins':egg,'xp':x,'level':l,'xp_required':l*100,'streak':streak,'last_login':last,'eggs_total':len(eggs),'achievements': database.get_achievements(uid), 'active_items':{str(i):max(0, int(expiry(uid, i) - time.time())) for i in ITEMS if has(uid, i)}, 'tasks':{'taps':t[0], 'games':t[1], 'eggs':t[2], 'tap_claimed':bool(t[3]), 'game_claimed':bool(t[4]), 'egg_claimed':bool(t[5])}}

def achievements(uid):
    tap,_= database.get_balance(uid); eggs= database.get_player_eggs(uid); _,lev= database.get_progress(uid); streak,_= database.get_login_info(uid); tasks= database.get_daily_tasks(uid); unlocked=[]
    checks={1:tap>=1, 2:tap>=1000, 3:len(eggs)>=5, 4:len(set(eggs))>=10, 5:tasks[1]>=10, 6:streak>=7, 7:lev>=10, 8: database.get_boss_damage(uid) >= 100}
    for i,ok in checks.items():
        if ok and not database.has_achievement(uid, i):
            database.add_achievement(uid, i); database.add_egg_coins(uid, ACH[i][2]); unlocked.append({'id':i, 'name':ACH[i][0], 'reward':ACH[i][2]})
    return unlocked

def json_error(msg,status=400):return jsonify(ok=False,error=msg),status

@app.get('/')
def index():return send_from_directory(app.static_folder, '../mini_app/index.html')

@app.post('/api/init')
def init():
    u,f=auth()
    if f:return f
    uid=int(u['id']); streak,last= database.get_login_info(uid); today=date.today().isoformat(); claimed=False; reward=0
    if last!=today:
        streak= database.update_login(uid); reward=min(10 + streak * 5, 100); database.add_egg_coins(uid, reward); xp(uid, 10); claimed=True
    return jsonify(ok=True,user={'id':uid,'username':u.get('username',''),'first_name':u.get('first_name','')},login={'claimed':claimed,'streak':streak,'reward':reward},data=snap(uid),new_achievements=achievements(uid))

@app.get('/api/state')
def state():
    u,f=auth()
    if f:return f
    return jsonify(ok=True,data=snap(int(u['id'])))

@app.post('/api/tap')
def tap():
    u,f=auth()
    if f:return f
    uid=int(u['id']); now=time.time()
    amount=max(1,min(int((request.json or {}).get('amount',1)),40))
    old=[t for t in last_tap.get(uid,[]) if now-t<2]
    if len(old)+amount>80:return json_error('Слишком быстро. Подожди немного.',429)
    old += [now]*amount; last_tap[uid]=old
    gain=amount*(3 if has(uid,1) else 1); database.add_tap_coins(uid, gain); database.add_task_tap(uid, amount); xp(uid, amount)
    return jsonify(ok=True,gained=gain,data=snap(uid),new_achievements=achievements(uid))

@app.post('/api/exchange')
def exchange():
    u,f=auth()
    if f:return f
    uid=int(u['id']); tap,_= database.get_balance(uid); n= tap // 30
    if n<1:return json_error('Нужно минимум 30 Tap Coins.')
    spent=n*30; received=n*10
    if not database.remove_tap_coins(uid, spent):return json_error('Не удалось выполнить обмен.')
    database.add_egg_coins(uid, received); xp(uid, 5)
    return jsonify(ok=True,spent=spent,received=received,data=snap(uid))

def game_ok(uid):
    now=time.time()
    if now-last_game.get(uid,0)<2:return False
    last_game[uid]=now; return True

@app.post('/api/game/guess/start')
def guess_start():
    u,f=auth()
    if f:return f
    uid=int(u['id'])
    if not game_ok(uid):return json_error('Подожди немного.',429)
    guess[uid]={'n':random.randint(1,20),'a':0};return jsonify(ok=True,min=1,max=20,attempts=10)
@app.post('/api/game/guess/answer')
def guess_answer():
    u,f=auth()
    if f:return f
    uid=int(u['id']);g=guess.get(uid)
    if not g:return json_error('Игра не запущена.')
    try:v=int(request.json.get('guess'))
    except:return json_error('Введите число.')
    if not 1<=v<=20:return json_error('Число от 1 до 20.')
    g['a']+=1; a=g['a']; rewards={1:5,2:4,3:3,4:3,5:2,6:1,7:1,8:1,9:1,10:1}
    if v==g['n']:
        r=rewards[a];eggcoins(uid,r);
        database.add_task_game(uid);xp(uid, 10);guess.pop(uid, None);return jsonify(ok=True, result='win', reward=r, number=g['n'], attempts=a, data=snap(uid), new_achievements=achievements(uid))
    if a>=10:
        guess.pop(uid,None);
        database.add_task_game(uid);return jsonify(ok=True, result='lose', reward=0, number=g['n'], attempts=a, data=snap(uid), new_achievements=achievements(uid))
    return jsonify(ok=True,result='continue',hint='Больше!' if v<g['n'] else 'Меньше!',attempts=a)

@app.post('/api/game/math/start')
def math_start():
    u,f=auth()
    if f:return f
    uid=int(u['id'])
    if not game_ok(uid):return json_error('Подожди немного.',429)
    a=random.randint(5,30);b=random.randint(2,20);op=random.choice(['+','-','*']);ans=a+b if op=='+' else a-b if op=='-' else a*b;math[uid]=ans;return jsonify(ok=True,question=f'{a} {op} {b} = ?')
@app.post('/api/game/math/answer')
def math_answer():
    u,f=auth()
    if f:return f
    uid=int(u['id']);ans=math.pop(uid,None)
    if ans is None:return json_error('Задание не запущено.')
    try:v=int(request.json.get('answer'))
    except:return json_error('Введите число.')
    database.add_task_game(uid)
    if v==ans:eggcoins(uid,4);xp(uid,10);r=4;res='win'
    else:r=0;res='lose'
    return jsonify(ok=True,result=res,correct=ans,reward=r,data=snap(uid),new_achievements=achievements(uid))

def winner(b):
    for a,c,d in ((0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)):
        if b[a]!=' ' and b[a]==b[c]==b[d]:return b[a]
    return 'draw' if ' ' not in b else None
@app.post('/api/game/tic/start')
def tic_start():
    u,f=auth()
    if f:return f
    uid=int(u['id'])
    if not game_ok(uid):return json_error('Подожди немного.',429)
    tic[uid]=[' ']*9;return jsonify(ok=True,board=tic[uid])
@app.post('/api/game/tic/move')
def tic_move():
    u,f=auth()
    if f:return f
    uid=int(u['id']);b=tic.get(uid)
    if b is None:return json_error('Игра не запущена.')
    try:i=int(request.json.get('index'))
    except:return json_error('Неверная клетка.')
    if i<0 or i>8 or b[i]!=' ':return json_error('Клетка занята.')
    b[i]='X';w=winner(b)
    if w=='X': database.add_egg_coins(uid, 5);database.add_task_game(uid);xp(uid, 15);tic.pop(uid, None);return jsonify(ok=True, board=b, result='win', reward=5, data=snap(uid), new_achievements=achievements(uid))
    if w=='draw': database.add_egg_coins(uid, 2);database.add_task_game(uid);xp(uid, 10);tic.pop(uid, None);return jsonify(ok=True, board=b, result='draw', reward=2, data=snap(uid), new_achievements=achievements(uid))
    empty=[i for i,x in enumerate(b) if x==' ']
    if empty:b[random.choice(empty)]='O'
    w=winner(b)
    if w=='O': database.add_task_game(uid);tic.pop(uid, None);return jsonify(ok=True, board=b, result='lose', reward=0, data=snap(uid), new_achievements=achievements(uid))
    if w=='draw': database.add_egg_coins(uid, 2);database.add_task_game(uid);xp(uid, 10);tic.pop(uid, None);return jsonify(ok=True, board=b, result='draw', reward=2, data=snap(uid), new_achievements=achievements(uid))
    return jsonify(ok=True,board=b,result='continue')

@app.get('/api/eggs')
def eggs():
    u,f=auth()
    if f:return f
    uid=int(u['id']);owned= database.get_player_eggs(uid);return jsonify(ok=True, shop={str(i):{'name':x[0], 'price':x[1], 'rarity':x[2]} for i,x in EGGS.items()}, owned={str(i):owned.count(i) for i in EGGS}, total=len(owned))
@app.post('/api/eggs/buy')
def buy_egg():
    u,f=auth()
    if f:return f
    uid=int(u['id'])
    try:i=int(request.json.get('egg_id'))
    except:return json_error('Неверное яйцо.')
    if i not in EGGS:return json_error('Такого яйца нет.')
    if not database.remove_egg_coins(uid, EGGS[i][1]):return json_error('Недостаточно Egg Coins.')
    database.add_egg(uid, i);
    database.add_task_egg(uid);xp(uid, 15);return jsonify(ok=True, egg={'name':EGGS[i][0]}, data=snap(uid), new_achievements=achievements(uid))

@app.get('/api/items')
def items():
    u,f=auth()
    if f:return f
    uid=int(u['id']);return jsonify(ok=True, items={str(i):{'name':x[0],'price':x[1],'description':x[2],'count': database.get_item_count(uid, i), 'active_seconds':max(0, int(expiry(uid, i) - time.time()))} for i,x in ITEMS.items()})
@app.post('/api/items/buy')
def buy_item():
    u,f=auth()
    if f:return f
    uid=int(u['id'])
    try:i=int(request.json.get('item_id'))
    except:return json_error('Неверный предмет.')
    if i not in ITEMS:return json_error('Такого предмета нет.')
    if not database.remove_egg_coins(uid, ITEMS[i][1]):return json_error('Недостаточно Egg Coins.')
    database.add_item(uid, i);xp(uid, 10);return jsonify(ok=True, data=snap(uid))
@app.post('/api/items/activate')
def activate_item():
    u,f=auth()
    if f:return f
    uid=int(u['id'])
    try:i=int(request.json.get('item_id'))
    except:return json_error('Неверный предмет.')
    if i not in ITEMS or not database.remove_item(uid, i):return json_error('У тебя нет этого предмета.')
    active[(uid,i)]=time.time()+600;return jsonify(ok=True,data=snap(uid))

@app.get('/api/achievements')
def achievement_list():
    u,f=auth()
    if f:return f
    uid=int(u['id']);s=set(database.get_achievements(uid));return jsonify(ok=True, items=[{'id':i, 'name':x[0], 'description':x[1], 'reward':x[2], 'unlocked': i in s} for i,x in ACH.items()])
@app.get('/api/leaderboard')
def leaderboard():
    u,f=auth()
    if f:return f
    uid=int(u['id']);return jsonify(ok=True, players=database.get_top_players(10), my_rank=database.get_player_rank(uid))
@app.post('/api/daily/bonus')
def bonus():
    u,f=auth()
    if f:return f
    uid=int(u['id']);today=date.today().isoformat()
    if database.get_daily_bonus_date(uid)==today:return json_error('Бонус уже получен сегодня.')
    streak,_= database.get_login_info(uid);r=min(20 + streak * 5, 100);
    database.add_egg_coins(uid, r);
    database.set_daily_bonus_date(uid);xp(uid, 20);return jsonify(ok=True, reward=r, data=snap(uid))
@app.get('/api/daily/tasks')
def tasks():
    u,f=auth()
    if f:return f
    uid=int(u['id']);t= database.get_daily_tasks(uid);return jsonify(ok=True, tasks=[{'id': 'tap', 'title': '👆 Сделать 100 тапов', 'progress':min(t[0], 100), 'target':100, 'reward':25, 'claimed':bool(t[3])}, {'id': 'game', 'title': '🎮 Сыграть 3 игры', 'progress':min(t[1], 3), 'target':3, 'reward':30, 'claimed':bool(t[4])}, {'id': 'egg', 'title': '🥚 Купить 1 яйцо', 'progress':min(t[2], 1), 'target':1, 'reward':40, 'claimed':bool(t[5])}])
@app.post('/api/daily/tasks/claim')
def claim():
    u,f=auth()
    if f:return f
    uid=int(u['id']);i=(request.json or {}).get('task_id');rewards={'tap':25,'game':30,'egg':40}
    if i not in rewards:return json_error('Неверное задание.')
    if not database.claim_task(uid, i):return json_error('Задание ещё не выполнено или уже получено.')
    database.add_egg_coins(uid, rewards[i]);xp(uid, 15);return jsonify(ok=True, reward=rewards[i], data=snap(uid))

@app.get('/api/boss')
def boss():
    u,f=auth()
    if f:return f
    return jsonify(ok=True, hp=boss_hp, max_hp=10000, my_damage=database.get_boss_damage(int(u['id'])))
@app.post('/api/boss/attack')
def boss_attack():
    global boss_hp
    u,f=auth()
    if f:return f
    uid=int(u['id']);now=time.time()
    if now-last_boss.get(uid,0)<.7:return json_error('Подожди немного.',429)
    last_boss[uid]=now;d=random.randint(5,15);actual=min(d,boss_hp);boss_hp-=actual;
    database.add_boss_damage(uid, actual);xp(uid, 2);defeated= boss_hp <= 0
    if defeated: database.add_egg_coins(uid, 100);boss_hp=10000
    return jsonify(ok=True,damage=actual,hp=boss_hp,max_hp=10000,defeated=defeated,data=snap(uid),new_achievements=achievements(uid))
@app.get('/api/withdrawal')
def withdrawal():
    u,f=auth()
    if f:return f
    uid=int(u['id']);owned= database.get_player_eggs(uid);return jsonify(ok=True, bot=WITHDRAWAL_BOT, total=len(owned), eggs={str(i):owned.count(i) for i in EGGS if owned.count(i)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080,debug=False)
