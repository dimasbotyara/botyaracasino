import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'casino.db')

# ─── Admin config ───
OWNER_USERNAME = 'dimasbotyara'
LOCALHOST_IPS = {'127.0.0.1', '::1', 'localhost'}

ACHIEVEMENTS = {
    'first_game': {'name': 'Первая игра', 'icon': '🎮', 'desc': 'Сыграй свою первую игру'},
    'first_win': {'name': 'Первая победа', 'icon': '🏆', 'desc': 'Выиграй свою первую игру'},
    'high_roller': {'name': 'Хай-роллер', 'icon': '💎', 'desc': 'Поставь 10 000₽ за раз'},
    'whale': {'name': 'Кит', 'icon': '🐋', 'desc': 'Поставь 50 000₽ за раз'},
    'lucky_streak_3': {'name': 'Удачная серия', 'icon': '🔥', 'desc': '3 победы подряд'},
    'lucky_streak_5': {'name': 'В огне!', 'icon': '🔥🔥', 'desc': '5 побед подряд'},
    'lucky_streak_10': {'name': 'НЕОСТАНОВИМ', 'icon': '☄️', 'desc': '10 побед подряд'},
    'games_10': {'name': 'Завсегдатай', 'icon': '🎲', 'desc': 'Сыграй 10 игр'},
    'games_50': {'name': 'Ветеран', 'icon': '⭐', 'desc': 'Сыграй 50 игр'},
    'games_100': {'name': 'Легенда', 'icon': '👑', 'desc': 'Сыграй 100 игр'},
    'big_win_5k': {'name': 'Крупный куш', 'icon': '💰', 'desc': 'Выиграй 5 000₽ за раз'},
    'big_win_50k': {'name': 'Джекпот!', 'icon': '🤑', 'desc': 'Выиграй 50 000₽ за раз'},
    'big_win_100k': {'name': 'МЕГАДЖЕКПОТ', 'icon': '💎👑', 'desc': 'Выиграй 100 000₽ за раз'},
    'broke': {'name': 'Банкрот', 'icon': '😢', 'desc': 'Останься с 0₽'},
    'millionaire': {'name': 'Миллионер', 'icon': '🏦', 'desc': 'Накопи 1 000 000₽'},
    'all_games': {'name': 'Мастер на все руки', 'icon': '🎯', 'desc': 'Сыграй во все 10 игр'},
    'profit_king': {'name': 'Король профита', 'icon': '📈', 'desc': 'Профит +100 000₽'},
    'depositor': {'name': 'Инвестор', 'icon': '🏧', 'desc': 'Пополни счёт 10 раз'},
}

# Настройки сервера (изменяемые из админки)
SERVER_SETTINGS = {
    'deposit_limit': 150000,
    'min_bet': 1,
    'max_bet': 0,  # 0 = без лимита (ограничен балансом)
    'registration_open': True,
    'maintenance_mode': False,
    'welcome_bonus': 0,
    'broadcast_message': '',
    'disabled_games': [],  # список отключённых игр
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL DEFAULT 0,
            total_deposited REAL DEFAULT 0,
            total_wagered REAL DEFAULT 0,
            total_won REAL DEFAULT 0,
            total_lost REAL DEFAULT 0,
            games_played INTEGER DEFAULT 0,
            games_won INTEGER DEFAULT 0,
            biggest_win REAL DEFAULT 0,
            biggest_loss REAL DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            worst_streak INTEGER DEFAULT 0,
            deposit_count INTEGER DEFAULT 0,
            peak_balance REAL DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0,
            ban_reason TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_active TEXT DEFAULT CURRENT_TIMESTAMP,
            is_online INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS game_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            game_type TEXT NOT NULL,
            bet_amount REAL NOT NULL,
            result TEXT NOT NULL,
            payout REAL NOT NULL,
            profit REAL NOT NULL,
            details TEXT,
            played_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_key TEXT NOT NULL,
            unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, achievement_key),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_username TEXT NOT NULL,
            action TEXT NOT NULL,
            target_username TEXT DEFAULT '',
            details TEXT DEFAULT '',
            ip TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS server_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS broadcast_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            from_admin TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Загружаем или инициализируем настройки
    for key, val in SERVER_SETTINGS.items():
        existing = c.execute('SELECT value FROM server_settings WHERE key=?', (key,)).fetchone()
        if not existing:
            c.execute('INSERT INTO server_settings (key, value) VALUES (?,?)',
                      (key, json.dumps(val)))

    conn.commit()
    conn.close()
    init_chat_table()

# ─── Settings ───

def get_setting(key):
    conn = get_db()
    row = conn.execute('SELECT value FROM server_settings WHERE key=?', (key,)).fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row['value'])
        except:
            return row['value']
    return SERVER_SETTINGS.get(key)


def set_setting(key, value):
    conn = get_db()
    conn.execute('''
        INSERT OR REPLACE INTO server_settings (key, value, updated_at)
        VALUES (?, ?, ?)
    ''', (key, json.dumps(value), datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_all_settings():
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM server_settings').fetchall()
    conn.close()
    result = {}
    for r in rows:
        try:
            result[r['key']] = json.loads(r['value'])
        except:
            result[r['key']] = r['value']
    return result


# ─── Admin Access ───

def get_admin_level(username, ip):
    """
    Возвращает уровень доступа:
    'owner'        - OWNER_USERNAME + localhost
    'super_admin'  - OWNER_USERNAME ИЛИ localhost
    'admin'        - назначен через OWNER
    'user'         - обычный пользователь
    """
    is_owner_name = (username == OWNER_USERNAME)
    is_local = (ip in LOCALHOST_IPS)

    if is_owner_name and is_local:
        return 'owner'
    elif is_owner_name or is_local:
        return 'super_admin'

    # Проверяем назначение админом
    conn = get_db()
    user = conn.execute('SELECT is_admin FROM users WHERE username=?', (username,)).fetchone()
    conn.close()
    if user and user['is_admin']:
        return 'admin'

    return 'user'


def set_admin_status(username, is_admin):
    conn = get_db()
    conn.execute('UPDATE users SET is_admin=? WHERE username=?', (1 if is_admin else 0, username))
    conn.commit()
    conn.close()


# ─── Admin Logging ───

def log_admin_action(admin_username, action, target_username='', details='', ip=''):
    conn = get_db()
    conn.execute('''
        INSERT INTO admin_logs (admin_username, action, target_username, details, ip)
        VALUES (?,?,?,?,?)
    ''', (admin_username, action, target_username, details, ip))
    conn.commit()
    conn.close()


def get_admin_logs(limit=100):
    conn = get_db()
    rows = conn.execute('''
        SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?
    ''', (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Users CRUD ───

def create_user(username, password):
    if not get_setting('registration_open'):
        return False, "Регистрация временно закрыта"

    conn = get_db()
    try:
        welcome = get_setting('welcome_bonus') or 0
        conn.execute(
            'INSERT INTO users (username, password_hash, balance) VALUES (?,?,?)',
            (username, generate_password_hash(password), welcome)
        )
        conn.commit()
        return True, "Регистрация успешна!"
    except sqlite3.IntegrityError:
        return False, "Этот ник уже занят!"
    finally:
        conn.close()


def authenticate_user(username, password):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    conn.close()
    if user is None:
        return None, "Пользователь не найден!"
    if not check_password_hash(user['password_hash'], password):
        return None, "Неверный пароль!"
    user = dict(user)  # ← конвертируем в dict
    try:
        if user.get('is_banned'):
            reason = user.get('ban_reason', '') or 'Не указана'
            return None, f"Аккаунт заблокирован! Причина: {reason}"
    except:
        pass
    return user, "OK"


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_username(username):
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
    conn.close()
    return dict(user) if user else None


def get_all_users():
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY balance DESC').fetchall()
    conn.close()
    return [dict(u) for u in users]


def set_user_online(user_id, online=True):
    conn = get_db()
    conn.execute(
        'UPDATE users SET is_online=?, last_active=? WHERE id=?',
        (1 if online else 0, datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_db()
    conn.execute('DELETE FROM game_history WHERE user_id=?', (user_id,))
    conn.execute('DELETE FROM transactions WHERE user_id=?', (user_id,))
    conn.execute('DELETE FROM user_achievements WHERE user_id=?', (user_id,))
    conn.execute('DELETE FROM users WHERE id=?', (user_id,))
    conn.commit()
    conn.close()


def ban_user(user_id, reason=''):
    conn = get_db()
    conn.execute('UPDATE users SET is_banned=1, ban_reason=?, is_online=0 WHERE id=?',
                 (reason, user_id))
    conn.commit()
    conn.close()


def unban_user(user_id):
    conn = get_db()
    conn.execute('UPDATE users SET is_banned=0, ban_reason="" WHERE id=?', (user_id,))
    conn.commit()
    conn.close()


def set_user_balance(user_id, new_balance):
    conn = get_db()
    conn.execute('UPDATE users SET balance=?, peak_balance=MAX(peak_balance,?) WHERE id=?',
                 (new_balance, new_balance, user_id))
    conn.commit()
    conn.close()


def reset_user_stats(user_id):
    conn = get_db()
    conn.execute('''
        UPDATE users SET
            total_wagered=0, total_won=0, total_lost=0,
            games_played=0, games_won=0,
            biggest_win=0, biggest_loss=0,
            current_streak=0, best_streak=0, worst_streak=0
        WHERE id=?
    ''', (user_id,))
    conn.execute('DELETE FROM game_history WHERE user_id=?', (user_id,))
    conn.commit()
    conn.close()


# ─── Balance ───

def deposit(user_id, amount):
    limit = get_setting('deposit_limit') or 150000
    if amount <= 0 or amount > limit:
        return False, f"Сумма от 1 до {limit:,.0f}₽"
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    user = dict(row)  # ← фикс
    new_balance = user['balance'] + amount
    peak = max(user.get('peak_balance', 0) or 0, new_balance)
    dep_count = (user.get('deposit_count', 0) or 0) + 1

    conn.execute('''
        UPDATE users SET balance=?, total_deposited=total_deposited+?,
        peak_balance=?, deposit_count=?, last_active=? WHERE id=?
    ''', (new_balance, amount, peak, dep_count, datetime.now().isoformat(), user_id))
    conn.execute(
        'INSERT INTO transactions (user_id,type,amount,balance_after,description) VALUES (?,?,?,?,?)',
        (user_id, 'deposit', amount, new_balance, f'Пополнение +{amount:.0f}₽')
    )
    conn.commit()
    conn.close()
    if dep_count >= 10:
        unlock_achievement(user_id, 'depositor')
    return True, f"Баланс пополнен на {amount:.0f}₽"


# ─── Game Recording ───

def record_game(user_id, game_type, bet_amount, is_win, payout, details=""):
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    user = dict(row)  # ← КЛЮЧЕВОЙ ФИКС: конвертируем Row в dict

    profit = payout - bet_amount
    new_balance = user['balance'] - bet_amount + payout
    result = 'win' if is_win else 'loss'

    if is_win:
        new_streak = max(user['current_streak'], 0) + 1
    else:
        new_streak = min(user['current_streak'], 0) - 1

    best_streak = max(user['best_streak'], new_streak)

    # Безопасно получаем worst_streak (может не быть в старой БД)
    try:
        ws = user['worst_streak'] if user['worst_streak'] is not None else 0
    except (KeyError, IndexError):
        ws = 0
    worst_streak = min(ws, new_streak)

    biggest_win = max(user['biggest_win'], profit) if is_win else user['biggest_win']
    biggest_loss = max(user['biggest_loss'], abs(profit)) if not is_win else user['biggest_loss']
    peak = max(user['peak_balance'], new_balance)

    try:
        tl = user['total_lost'] if user['total_lost'] is not None else 0
    except (KeyError, IndexError):
        tl = 0
    total_lost = tl + (bet_amount if not is_win else 0)

    conn.execute('''
        UPDATE users SET
            balance=?, total_wagered=total_wagered+?,
            total_won=total_won+?, total_lost=?,
            games_played=games_played+1, games_won=games_won+?,
            biggest_win=?, biggest_loss=?,
            current_streak=?, best_streak=?, worst_streak=?,
            peak_balance=?, last_active=?
        WHERE id=?
    ''', (new_balance, bet_amount, payout if is_win else 0, total_lost,
          1 if is_win else 0, biggest_win, biggest_loss,
          new_streak, best_streak, worst_streak,
          peak, datetime.now().isoformat(), user_id))

    conn.execute('''
        INSERT INTO game_history (user_id,game_type,bet_amount,result,payout,profit,details)
        VALUES (?,?,?,?,?,?,?)
    ''', (user_id, game_type, bet_amount, result, payout, profit, details))
    conn.execute('''
        INSERT INTO transactions (user_id,type,amount,balance_after,description)
        VALUES (?,?,?,?,?)
    ''', (user_id, 'game', profit, new_balance, f'{game_type}: {details}'))

    conn.commit()

    gp = user['games_played'] + 1
    gw = user['games_won'] + (1 if is_win else 0)
    check_achievements(user_id, conn, gp, gw, new_balance, bet_amount,
                       profit, new_streak, user['total_deposited'], game_type)
    conn.close()
    return new_balance, profit, is_win


def check_achievements(user_id, conn, gp, gw, balance, bet, profit, streak, deposited, game_type):
    achs = []
    if gp >= 1: achs.append('first_game')
    if gw >= 1: achs.append('first_win')
    if bet >= 10000: achs.append('high_roller')
    if bet >= 50000: achs.append('whale')
    if streak >= 3: achs.append('lucky_streak_3')
    if streak >= 5: achs.append('lucky_streak_5')
    if streak >= 10: achs.append('lucky_streak_10')
    if gp >= 10: achs.append('games_10')
    if gp >= 50: achs.append('games_50')
    if gp >= 100: achs.append('games_100')
    if profit >= 5000: achs.append('big_win_5k')
    if profit >= 50000: achs.append('big_win_50k')
    if profit >= 100000: achs.append('big_win_100k')
    if balance <= 0: achs.append('broke')
    if balance >= 1000000: achs.append('millionaire')
    if (balance - deposited) >= 100000: achs.append('profit_king')

    game_types = conn.execute(
        'SELECT DISTINCT game_type FROM game_history WHERE user_id=?', (user_id,)
    ).fetchall()
    played = {r['game_type'] for r in game_types}
    played.add(game_type)
    all_games = {'Слоты','Кости','Рулетка','Монетка','Краш','Блэкджек',
             'Мины','Хай-Лоу','Скачки','Колесо','Башня','Лимбо','Пенальти','Кено'}
    if played >= all_games: achs.append('all_games')

    for a in achs:
        unlock_achievement(user_id, a)


def unlock_achievement(user_id, key):
    try:
        conn = get_db()
        conn.execute('INSERT OR IGNORE INTO user_achievements (user_id,achievement_key) VALUES (?,?)',
                     (user_id, key))
        conn.commit()
        conn.close()
    except:
        pass


def get_user_achievements(user_id):
    conn = get_db()
    rows = conn.execute(
        'SELECT achievement_key, unlocked_at FROM user_achievements WHERE user_id=?', (user_id,)
    ).fetchall()
    conn.close()
    unlocked = {r['achievement_key']: r['unlocked_at'] for r in rows}
    result = []
    for key, ach in ACHIEVEMENTS.items():
        if key in unlocked:
            result.append({**ach, 'key': key, 'unlocked': True, 'unlocked_at': unlocked[key]})
        else:
            result.append({**ach, 'key': key, 'unlocked': False})
    return result


# ─── Leaderboard ───

def get_leaderboard():
    conn = get_db()
    users = conn.execute('''
        SELECT username, balance, total_deposited, total_wagered, total_won,
               total_lost, games_played, games_won, biggest_win, best_streak,
               peak_balance, is_online, last_active
        FROM users WHERE is_banned=0 ORDER BY balance DESC
    ''').fetchall()
    conn.close()
    result = []
    for u in users:
        u = dict(u)
        u['profit'] = u['balance'] - u['total_deposited']
        u['winrate'] = (u['games_won']/u['games_played']*100) if u['games_played'] > 0 else 0
        u['roi'] = ((u['profit']/u['total_deposited'])*100) if u['total_deposited'] > 0 else 0
        result.append(u)
    return result


def get_user_history(user_id, limit=30):
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM game_history WHERE user_id=? ORDER BY played_at DESC LIMIT ?',
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_user_stats(user_id):
    user = get_user_by_id(user_id)
    if not user: return None
    user['profit'] = user['balance'] - user['total_deposited']
    user['winrate'] = (user['games_won']/user['games_played']*100) if user['games_played'] > 0 else 0
    user['loss_count'] = user['games_played'] - user['games_won']
    user['roi'] = ((user['profit']/user['total_deposited'])*100) if user['total_deposited'] > 0 else 0

    conn = get_db()
    game_stats = conn.execute('''
        SELECT game_type, COUNT(*) as total,
               SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) as wins,
               SUM(profit) as total_profit, MAX(profit) as best_profit
        FROM game_history WHERE user_id=? GROUP BY game_type
    ''', (user_id,)).fetchall()
    user['game_stats'] = [dict(g) for g in game_stats]

    recent = conn.execute('''
        SELECT balance_after FROM transactions WHERE user_id=?
        ORDER BY created_at DESC LIMIT 50
    ''', (user_id,)).fetchall()
    user['balance_history'] = [r['balance_after'] for r in reversed(recent)]
    conn.close()
    return user


# ─── Broadcast ───

def create_broadcast(message, admin_username):
    conn = get_db()
    conn.execute('UPDATE broadcast_messages SET is_active=0')  # деактивируем старые
    conn.execute(
        'INSERT INTO broadcast_messages (message, from_admin) VALUES (?,?)',
        (message, admin_username)
    )
    conn.commit()
    conn.close()


def get_active_broadcast():
    conn = get_db()
    row = conn.execute(
        'SELECT * FROM broadcast_messages WHERE is_active=1 ORDER BY created_at DESC LIMIT 1'
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def clear_broadcast():
    conn = get_db()
    conn.execute('UPDATE broadcast_messages SET is_active=0')
    conn.commit()
    conn.close()


# ─── Server Stats ───

def get_server_stats():
    conn = get_db()
    stats = {}
    stats['total_users'] = conn.execute('SELECT COUNT(*) as c FROM users').fetchone()['c']
    stats['online_users'] = conn.execute('SELECT COUNT(*) as c FROM users WHERE is_online=1').fetchone()['c']
    stats['banned_users'] = conn.execute('SELECT COUNT(*) as c FROM users WHERE is_banned=1').fetchone()['c']
    stats['total_games'] = conn.execute('SELECT COUNT(*) as c FROM game_history').fetchone()['c']

    money = conn.execute('''
        SELECT
            COALESCE(SUM(balance),0) as total_balance,
            COALESCE(SUM(total_deposited),0) as total_deposited,
            COALESCE(SUM(total_wagered),0) as total_wagered,
            COALESCE(SUM(total_won),0) as total_won
        FROM users
    ''').fetchone()
    stats['total_balance'] = money['total_balance']
    stats['total_deposited'] = money['total_deposited']
    stats['total_wagered'] = money['total_wagered']
    stats['total_won'] = money['total_won']

    # Игры по типам
    game_breakdown = conn.execute('''
        SELECT game_type, COUNT(*) as count,
               SUM(bet_amount) as wagered,
               SUM(CASE WHEN result='win' THEN 1 ELSE 0 END) as wins
        FROM game_history GROUP BY game_type ORDER BY count DESC
    ''').fetchall()
    stats['game_breakdown'] = [dict(g) for g in game_breakdown]

    # Последние транзакции
    recent_tx = conn.execute('''
        SELECT t.*, u.username FROM transactions t
        JOIN users u ON t.user_id = u.id
        ORDER BY t.created_at DESC LIMIT 20
    ''').fetchall()
    stats['recent_transactions'] = [dict(t) for t in recent_tx]

    # Последние регистрации
    recent_users = conn.execute('''
        SELECT username, created_at, balance, is_online, is_banned
        FROM users ORDER BY created_at DESC LIMIT 10
    ''').fetchall()
    stats['recent_users'] = [dict(u) for u in recent_users]

    conn.close()
    return stats

# ─── Chat ───

def init_chat_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            msg_type TEXT DEFAULT 'chat',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()


def send_chat_message(user_id, username, message, msg_type='chat'):
    conn = get_db()
    conn.execute(
        'INSERT INTO chat_messages (user_id, username, message, msg_type) VALUES (?,?,?,?)',
        (user_id, username, message[:500], msg_type)  # лимит 500 символов
    )
    # Держим только последние 200 сообщений
    conn.execute('''
        DELETE FROM chat_messages WHERE id NOT IN (
            SELECT id FROM chat_messages ORDER BY created_at DESC LIMIT 200
        )
    ''')
    conn.commit()
    conn.close()


def get_chat_messages(limit=50, after_id=0):
    conn = get_db()
    rows = conn.execute('''
        SELECT * FROM chat_messages
        WHERE id > ?
        ORDER BY created_at DESC LIMIT ?
    ''', (after_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def send_system_message(text):
    """Системное сообщение в чат (выигрыши, достижения)"""
    conn = get_db()
    conn.execute(
        'INSERT INTO chat_messages (user_id, username, message, msg_type) VALUES (?,?,?,?)',
        (0, 'CASINO', text, 'system')
    )
    conn.commit()
    conn.close()