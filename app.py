import os
import sys
import random
import socket
import threading
import time
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, flash, Response
)
from models import (
    init_db, create_user, authenticate_user, get_user_by_id,
    set_user_online, deposit, record_game, get_leaderboard,
    get_user_history, get_user_stats, get_user_achievements,
    unlock_achievement, get_db, get_setting, get_admin_level,
    get_active_broadcast,
    send_chat_message, get_chat_messages, send_system_message
)
from admin import admin_bp

app = Flask(__name__)
SECRET_KEY_FILE = os.path.join(os.path.dirname(__file__), '.secret_key')

def get_or_create_secret_key():
    if os.path.exists(SECRET_KEY_FILE):
        with open(SECRET_KEY_FILE, 'rb') as f:
            return f.read()
    key = os.urandom(32)
    with open(SECRET_KEY_FILE, 'wb') as f:
        f.write(key)
    return key

app.secret_key = get_or_create_secret_key()
app.config['SESSION_COOKIE_NAME'] = 'botyaracasino'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 7
app.register_blueprint(admin_bp)
init_db()

DEVELOPER = "dimasbotyara"


# ═══════════════════════════════════════
#          SVG AVATAR / FAVICON
# ═══════════════════════════════════════

SITE_AVATAR_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <defs>
    <radialGradient id="bg" cx="50%" cy="50%" r="60%">
      <stop offset="0%" stop-color="#3b0764"/>
      <stop offset="100%" stop-color="#0a0a0f"/>
    </radialGradient>
    <linearGradient id="frame" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#a855f7"/>
      <stop offset="100%" stop-color="#7c3aed"/>
    </linearGradient>
    <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="128" height="128" rx="28" fill="url(#bg)"/>
  <rect x="4" y="4" width="120" height="120" rx="26" fill="none" stroke="url(#frame)" stroke-width="2" opacity="0.7"/>
  <text x="64" y="86" font-size="72" text-anchor="middle" filter="url(#glow)">🎰</text>
  <text x="64" y="112" font-size="10" font-family="Inter,sans-serif" font-weight="900"
        fill="#c4b5fd" text-anchor="middle" letter-spacing="2">BOTYARA</text>
</svg>'''


@app.route('/favicon.svg')
def favicon_svg():
    return Response(SITE_AVATAR_SVG, mimetype='image/svg+xml')

@app.route('/favicon.ico')
def favicon_ico():
    return Response(SITE_AVATAR_SVG, mimetype='image/svg+xml')

@app.route('/avatar.svg')
def avatar_svg():
    return Response(SITE_AVATAR_SVG, mimetype='image/svg+xml')


# ═══════════════════════════════════════
#          CONSOLE LOGGING SYSTEM
# ═══════════════════════════════════════

class CasinoConsole:
    RESET = '\033[0m'; BOLD = '\033[1m'; DIM = '\033[2m'
    RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
    BLUE = '\033[94m'; MAGENTA = '\033[95m'; CYAN = '\033[96m'
    WHITE = '\033[97m'; GRAY = '\033[90m'

    def __init__(self):
        self.online_users = {}
        self.total_connections = 0
        self.total_games_played = 0
        self.total_money_wagered = 0
        self.total_money_won = 0
        self.total_deposits = 0
        self.lock = threading.Lock()
        self.start_time = datetime.now()
        if sys.platform == 'win32':
            os.system('')
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except: pass

    def _time(self): return datetime.now().strftime('%H:%M:%S')
    def _print(self, msg):
        with self.lock: print(msg, flush=True)
    def _format_money(self, amount):
        return f"{self.GREEN}+{amount:,.0f}₽{self.RESET}" if amount >= 0 else f"{self.RED}{amount:,.0f}₽{self.RESET}"
    def _format_balance(self, balance):
        return f"{self.CYAN}{balance:,.0f}₽{self.RESET}"

    def _get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]; s.close(); return ip
        except: return '0.0.0.0'

    def _parse_ua(self, ua):
        ua = str(ua).lower()
        if 'edg' in ua: return 'Edge'
        if 'chrome' in ua: return 'Chrome'
        if 'firefox' in ua: return 'Firefox'
        if 'safari' in ua: return 'Safari'
        return 'Unknown'

    def _format_duration(self, delta):
        t = int(delta.total_seconds())
        if t < 60: return f"{t}с"
        elif t < 3600: return f"{t//60}м {t%60}с"
        else: return f"{t//3600}ч {(t%3600)//60}м"

    def print_banner(self, host, port):
        ip = self._get_local_ip()
        print(f"""
{self.MAGENTA}{self.BOLD}
🎰 ══════════════════════════════════════════════════════
   {self.WHITE}b o t y a r a c a s i n o{self.MAGENTA}
   {self.GRAY}by {self.CYAN}{self.BOLD}{DEVELOPER}{self.RESET}
{self.MAGENTA}══════════════════════════════════════════════════════ 🎰
{self.RESET}
   {self.WHITE}📍 Локально:{self.RESET}  {self.CYAN}http://127.0.0.1:{port}{self.RESET}
   {self.WHITE}📍 LAN:{self.RESET}       {self.CYAN}http://{ip}:{port}{self.RESET}
   {self.WHITE}📍 Админка:{self.RESET}   {self.YELLOW}http://127.0.0.1:{port}/admin{self.RESET}
   {self.GRAY}Запущен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{self.RESET}
{self.YELLOW}   ⏳ Ожидание подключений...{self.RESET}
{self.GRAY}{'─'*56}{self.RESET}
""", flush=True)

    def log_connect(self, ip, ua=''):
        self.total_connections += 1
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.GREEN}🟢 CONNECT   {self.RESET} {self.WHITE}{ip}{self.RESET} {self.GRAY}({self._parse_ua(ua)}){self.RESET}")

    def log_disconnect(self, username, uid):
        dur = ''
        if uid in self.online_users:
            dur = self._format_duration(datetime.now() - self.online_users[uid]['connected_at'])
            del self.online_users[uid]
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.RED}🔴 DISCONNECT{self.RESET} {self.BOLD}{self.WHITE}{username}{self.RESET} {self.GRAY}→ Онлайн {dur}{self.RESET}")
        self._print_online()

    def log_login(self, username, uid, ip, balance):
        self.online_users[uid] = {'username': username, 'ip': ip, 'connected_at': datetime.now(), 'last_action': datetime.now()}
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.GREEN}🔑 LOGIN     {self.RESET} {self.BOLD}{self.WHITE}{username}{self.RESET} {self.GRAY}({ip}){self.RESET} → Баланс: {self._format_balance(balance)}")
        self._print_online()

    def log_register(self, username, ip):
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.CYAN}📝 REGISTER  {self.RESET} {self.BOLD}{self.WHITE}{username}{self.RESET} {self.GRAY}({ip}){self.RESET}")

    def log_login_failed(self, username, ip, reason):
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.RED}⛔ AUTH FAIL {self.RESET} {self.WHITE}{username}{self.RESET} {self.GRAY}({ip}){self.RESET} → {self.RED}{reason}{self.RESET}")

    def log_deposit(self, username, amount, balance):
        self.total_deposits += amount
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.YELLOW}💰 DEPOSIT   {self.RESET} {self.BOLD}{self.WHITE}{username}{self.RESET} {self._format_money(amount)} → Баланс: {self._format_balance(balance)}")

    def log_game(self, username, game_type, bet, is_win, profit, payout, balance, details=''):
        self.total_games_played += 1
        self.total_money_wagered += bet
        if is_win: self.total_money_won += payout
        icons = {'Слоты':'🎰','Кости':'🎲','Рулетка':'🎡','Монетка':'🪙','Краш':'📈','Блэкджек':'🃏','Мины':'💣','Хай-Лоу':'🎱','Скачки':'🏇','Колесо':'🎯','Башня':'🗼','Лимбо':'🎯','Пенальти':'⚽','Кено':'🎱'}
        icon = icons.get(game_type, '🎮')
        r = f"{self.GREEN}{self.BOLD}WIN{self.RESET} {self._format_money(profit)}" if is_win else f"{self.RED}LOSS{self.RESET} {self._format_money(profit)}"
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.MAGENTA}{icon} GAME      {self.RESET} {self.BOLD}{self.WHITE}{username}{self.RESET} → {self.YELLOW}{game_type}{self.RESET} | Ставка: {self.WHITE}{bet:,.0f}₽{self.RESET} | {r} | Баланс: {self._format_balance(balance)}")
        if is_win and profit >= 10000:
            self._print(f"  {self.GRAY}{'':>11}{self.RESET} {self.YELLOW}⭐ КРУПНЫЙ ВЫИГРЫШ!{self.RESET} {self.WHITE}{username}{self.RESET} {self.GREEN}{self.BOLD}+{profit:,.0f}₽{self.RESET}")

    def log_game_enter(self, username, game):
        names = {'slots':'🎰 Слоты','dice':'🎲 Кости','roulette':'🎡 Рулетка','coinflip':'🪙 Монетка','crash':'📈 Краш','blackjack':'🃏 Блэкджек','mines':'💣 Мины','hilo':'🎱 Хай-Лоу','races':'🏇 Скачки','wheel':'🎯 Колесо','tower':'🗼 Башня','limbo':'🎯 Лимбо','penalty':'⚽ Пенальти','keno':'🎱 Кено'}
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.BLUE}🚪 ENTER     {self.RESET} {self.BOLD}{self.WHITE}{username}{self.RESET} → {self.YELLOW}{names.get(game, game)}{self.RESET}")

    def log_page(self, username, page):
        pages = {'dashboard':'🏠 Главная','profile':'👤 Профиль','leaderboard':'🏆 Лидерборд'}
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.GRAY}📄 PAGE      {self.RESET} {self.WHITE}{username}{self.RESET} → {pages.get(page, page)}")

    def log_request(self, method, path, status, ip, ms):
        if '/api/balance' in path or '/api/leaderboard' in path or '/api/chat/messages' in path: return
        c = self.GREEN if status < 400 else self.YELLOW if status < 500 else self.RED
        self._print(f"  {self.GRAY}[{self._time()}]{self.RESET} {self.GRAY}📡 HTTP      {self.RESET} {c}{method} {status}{self.RESET} {self.GRAY}{path} ({ms:.0f}ms) {ip}{self.RESET}")

    def _print_online(self):
        n = len(self.online_users)
        users = ', '.join(u['username'] for u in self.online_users.values())
        s = f"{self.GREEN}{n}{self.RESET} | {self.WHITE}{users}{self.RESET}" if n else f"{self.GRAY}пусто{self.RESET}"
        self._print(f"  {self.GRAY}{'':>11}{self.RESET} 👥 Онлайн: {s}")

    def print_stats(self):
        up = self._format_duration(datetime.now() - self.start_time)
        self._print(f"\n{self.GRAY}{'─'*56}{self.RESET}\n  {self.CYAN}📊 СТАТИСТИКА{self.RESET}\n  Аптайм: {self.WHITE}{up}{self.RESET} | Подключений: {self.WHITE}{self.total_connections}{self.RESET} | Онлайн: {self.GREEN}{len(self.online_users)}{self.RESET}\n  Игр: {self.WHITE}{self.total_games_played}{self.RESET} | Поставлено: {self.YELLOW}{self.total_money_wagered:,.0f}₽{self.RESET} | Депозитов: {self.CYAN}{self.total_deposits:,.0f}₽{self.RESET}\n{self.GRAY}{'─'*56}{self.RESET}\n")


console = CasinoConsole()


# ─── Middleware ───

@app.before_request
def before_request():
    request._start_time = time.time()
    if get_setting('maintenance_mode'):
        username = session.get('username', '')
        ip = request.remote_addr
        level = get_admin_level(username, ip) if username else 'user'
        if level == 'user' and request.endpoint not in ('login', 'static', 'favicon_svg', 'favicon_ico', 'avatar_svg', None):
            flash('🔧 Сервер на обслуживании. Попробуйте позже.', 'error')
            return redirect(url_for('login'))
    if not session.get('_logged_connect') and request.endpoint and 'api' not in str(request.endpoint):
        console.log_connect(request.remote_addr, request.headers.get('User-Agent', ''))
        session['_logged_connect'] = True


@app.after_request
def after_request(response):
    ms = (time.time() - getattr(request, '_start_time', time.time())) * 1000
    console.log_request(request.method, request.path, response.status_code, request.remote_addr, ms)
    return response


# ─── Helpers ───

def current_user():
    uid = session.get('user_id')
    return get_user_by_id(uid) if uid else None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_username():
    return session.get('username', 'Unknown')


# ─── Auth ───

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        ip = request.remote_addr
        if len(username) < 2 or len(username) > 20:
            flash('Ник от 2 до 20 символов', 'error')
            return render_template('register.html', dev=DEVELOPER)
        if len(password) < 3:
            flash('Пароль минимум 3 символа', 'error')
            return render_template('register.html', dev=DEVELOPER)
        ok, msg = create_user(username, password)
        if ok:
            console.log_register(username, ip)
            # AUTO-LOGIN после регистрации
            user, auth_msg = authenticate_user(username, password)
            if user:
                session.permanent = True
                session['user_id'] = user['id']
                session['username'] = user['username']
                set_user_online(user['id'], True)
                console.log_login(user['username'], user['id'], ip, user['balance'])
                flash('🎉 Добро пожаловать в botyaracasino!', 'success')
                return redirect(url_for('dashboard'))
            flash(msg, 'success')
            return redirect(url_for('login'))
        flash(msg, 'error')
    return render_template('register.html', dev=DEVELOPER)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        ip = request.remote_addr
        user, msg = authenticate_user(username, password)
        if user is None:
            flash(msg, 'error'); console.log_login_failed(username, ip, msg)
            return render_template('login.html', dev=DEVELOPER)
        if user['is_online']:
            flash('Аккаунт уже используется!', 'error'); console.log_login_failed(username, ip, 'Двойная сессия')
            return render_template('login.html', dev=DEVELOPER)
        session.permanent = True
        session['user_id'] = user['id']; session['username'] = user['username']
        set_user_online(user['id'], True)
        console.log_login(user['username'], user['id'], ip, user['balance'])
        return redirect(url_for('dashboard'))
    return render_template('login.html', dev=DEVELOPER)

@app.route('/logout')
def logout():
    uid = session.get('user_id'); username = session.get('username', 'Unknown')
    if uid: set_user_online(uid, False); console.log_disconnect(username, uid)
    session.clear()
    return redirect(url_for('login'))


# ─── Pages ───

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user()
    broadcast = get_active_broadcast()
    admin_level = get_admin_level(session.get('username', ''), request.remote_addr)
    console.log_page(get_username(), 'dashboard')
    return render_template('dashboard.html', user=user, dev=DEVELOPER,
                           broadcast=broadcast, admin_level=admin_level)

@app.route('/profile')
@login_required
def profile():
    stats = get_user_stats(session['user_id'])
    history = get_user_history(session['user_id'], 30)
    achievements = get_user_achievements(session['user_id'])
    console.log_page(get_username(), 'profile')
    return render_template('profile.html', user=stats, history=history,
                           achievements=achievements, dev=DEVELOPER)

@app.route('/leaderboard')
@login_required
def leaderboard():
    leaders = get_leaderboard(); user = current_user()
    console.log_page(get_username(), 'leaderboard')
    return render_template('leaderboard.html', leaders=leaders, user=user, dev=DEVELOPER)


# ─── API ───

@app.route('/api/balance')
@login_required
def api_balance():
    user = current_user()
    uid = session.get('user_id')
    if uid in console.online_users:
        console.online_users[uid]['last_action'] = datetime.now()
    broadcast = get_active_broadcast()
    return jsonify({
        'balance': user['balance'],
        'username': user['username'],
        'broadcast': broadcast['message'] if broadcast else None
    })

@app.route('/api/deposit', methods=['POST'])
@login_required
def api_deposit():
    data = request.get_json()
    amount = float(data.get('amount', 0))
    ok, msg = deposit(session['user_id'], amount)
    user = get_user_by_id(session['user_id'])
    if ok: console.log_deposit(get_username(), amount, user['balance'])
    return jsonify({'success': ok, 'message': msg, 'balance': user['balance']})

@app.route('/api/leaderboard')
@login_required
def api_leaderboard():
    return jsonify(get_leaderboard())


# ─── Game Helpers ───

def validate_bet(user, data):
    bet = float(data.get('bet', 0))
    if bet <= 0:
        return None, jsonify({'success': False, 'message': 'Ставка > 0'})
    if bet > user['balance']:
        return None, jsonify({'success': False, 'message': 'Недостаточно средств!'})
    max_bet = get_setting('max_bet')
    if max_bet and max_bet > 0 and bet > max_bet:
        return None, jsonify({'success': False, 'message': f'Макс. ставка: {max_bet:,.0f}₽'})
    min_bet = get_setting('min_bet') or 1
    if bet < min_bet:
        return None, jsonify({'success': False, 'message': f'Мин. ставка: {min_bet:,.0f}₽'})
    return bet, None

def check_game_disabled(game_name):
    disabled = get_setting('disabled_games') or []
    if game_name in disabled:
        return jsonify({'success': False, 'message': f'{game_name} временно отключена'})
    return None

def log_game_result(username, game_type, bet, is_win, profit, payout, balance, details=''):
    console.log_game(username, game_type, bet, is_win, profit, payout, balance, details)


# ═══════════════════════════════════════
#          GAMES (ЩЕДРЫЕ ШАНСЫ)
# ═══════════════════════════════════════

# 1. SLOTS — больше шансов на комбо + повышенные множители
@app.route('/game/slots')
@login_required
def game_slots():
    console.log_game_enter(get_username(), 'slots')
    return render_template('game_slots.html', user=current_user(), dev=DEVELOPER)

@app.route('/api/game/slots', methods=['POST'])
@login_required
def api_game_slots():
    err = check_game_disabled('Слоты')
    if err: return err
    user = current_user(); bet, err = validate_bet(user, request.get_json())
    if err: return err
    symbols = ['🍒','🍋','🍊','🍇','💎','7️⃣','🍀']
    # ЩЕДРЕЕ: больше веса у дорогих символов
    weights  = [22, 20, 18, 16, 13, 8, 5]
    reels = [random.choices(symbols, weights=weights, k=3) for _ in range(3)]
    mid = [reels[0][1], reels[1][1], reels[2][1]]
    mult = 0
    mults = {'🍒':5,'🍋':7,'🍊':10,'🍇':15,'💎':30,'7️⃣':50,'🍀':100}
    if mid[0]==mid[1]==mid[2]:
        mult = mults.get(mid[0], 5)
    elif mid[0]==mid[1] or mid[1]==mid[2] or mid[0]==mid[2]:
        mult = 2.5
    payout = bet*mult; is_win = mult > 0
    details = f"{'|'.join(mid)} →x{mult}"
    new_bal, profit, _ = record_game(session['user_id'], 'Слоты', bet, is_win, payout, details)
    log_game_result(get_username(), 'Слоты', bet, is_win, profit, payout, new_bal)
    return jsonify({'success':True,'reels':reels,'middle_row':mid,'multiplier':mult,'payout':payout,'profit':profit,'is_win':is_win,'balance':new_bal})

# 2. DICE — расширил диапазоны high/low
@app.route('/game/dice')
@login_required
def game_dice():
    console.log_game_enter(get_username(), 'dice')
    return render_template('game_dice.html', user=current_user(), dev=DEVELOPER)

@app.route('/api/game/dice', methods=['POST'])
@login_required
def api_game_dice():
    err = check_game_disabled('Кости')
    if err: return err
    user = current_user(); data = request.get_json(); bet, err = validate_bet(user, data)
    if err: return err
    guess = data.get('guess','high'); target = int(data.get('target',7))
    d1, d2 = random.randint(1,6), random.randint(1,6); total = d1+d2
    is_win, mult = False, 0
    # ЩЕДРЕЕ: high = 7+, low = 7-, seven = ровно 7 -> оба выигрывают на 7
    if guess=='high' and total>=7: is_win, mult = True, 2.1
    elif guess=='low' and total<=7: is_win, mult = True, 2.1
    elif guess=='seven' and total==7: is_win, mult = True, 5.0
    elif guess=='exact' and total==target: is_win, mult = True, 8.0
    elif guess=='doubles' and d1==d2: is_win, mult = True, 6.0
    payout = bet*mult; details = f"🎲{d1}+{d2}={total} [{guess}] →x{mult}"
    new_bal, profit, _ = record_game(session['user_id'], 'Кости', bet, is_win, payout, details)
    log_game_result(get_username(), 'Кости', bet, is_win, profit, payout, new_bal)
    return jsonify({'success':True,'die1':d1,'die2':d2,'total':total,'guess':guess,'is_win':is_win,'multiplier':mult,'payout':payout,'profit':profit,'balance':new_bal})

# 3. ROULETTE — повышенные множители
@app.route('/game/roulette')
@login_required
def game_roulette():
    console.log_game_enter(get_username(), 'roulette')
    return render_template('game_roulette.html', user=current_user(), dev=DEVELOPER)

@app.route('/api/game/roulette', methods=['POST'])
@login_required
def api_game_roulette():
    err = check_game_disabled('Рулетка')
    if err: return err
    user = current_user(); data = request.get_json(); bet, err = validate_bet(user, data)
    if err: return err
    bet_type = data.get('bet_type','red'); bet_number = int(data.get('number',0))
    result_num = random.randint(0,36)
    reds = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    color = 'green' if result_num==0 else ('red' if result_num in reds else 'black')
    is_win, mult = False, 0
    if bet_type=='red' and color=='red': is_win, mult = True, 2.1
    elif bet_type=='black' and color=='black': is_win, mult = True, 2.1
    elif bet_type=='green' and color=='green': is_win, mult = True, 40.0
    elif bet_type=='even' and result_num!=0 and result_num%2==0: is_win, mult = True, 2.1
    elif bet_type=='odd' and result_num%2==1: is_win, mult = True, 2.1
    elif bet_type=='number' and result_num==bet_number: is_win, mult = True, 40.0
    payout = bet*mult; details = f"{result_num}({color}) [{bet_type}] →x{mult}"
    new_bal, profit, _ = record_game(session['user_id'], 'Рулетка', bet, is_win, payout, details)
    log_game_result(get_username(), 'Рулетка', bet, is_win, profit, payout, new_bal)
    return jsonify({'success':True,'number':result_num,'color':color,'bet_type':bet_type,'is_win':is_win,'multiplier':mult,'payout':payout,'profit':profit,'balance':new_bal})

# 4. COINFLIP
@app.route('/game/coinflip')
@login_required
def game_coinflip():
    console.log_game_enter(get_username(), 'coinflip')
    return render_template('game_coinflip.html', user=current_user(), dev=DEVELOPER)

@app.route('/api/game/coinflip', methods=['POST'])
@login_required
def api_game_coinflip():
    err = check_game_disabled('Монетка')
    if err: return err
    user = current_user(); data = request.get_json(); bet, err = validate_bet(user, data)
    if err: return err
    choice = data.get('choice','heads'); result = random.choice(['heads','tails'])
    is_win = choice==result
    mult = 2.0 if is_win else 0  # x2 (0% edge!)
    payout = bet*mult
    ru = {'heads':'Орёл','tails':'Решка'}; details = f"{ru[choice]}→{ru[result]} x{mult}"
    new_bal, profit, _ = record_game(session['user_id'], 'Монетка', bet, is_win, payout, details)
    log_game_result(get_username(), 'Монетка', bet, is_win, profit, payout, new_bal)
    return jsonify({'success':True,'choice':choice,'result':result,'is_win':is_win,'multiplier':mult,'payout':payout,'profit':profit,'balance':new_bal})

# 6. BLACKJACK
@app.route('/game/blackjack')
@login_required
def game_blackjack():
    console.log_game_enter(get_username(), 'blackjack')
    return render_template('game_blackjack.html', user=current_user(), dev=DEVELOPER)

def bj_card_value(card):
    r = card['rank']
    if r in ['J','Q','K']: return 10
    if r == 'A': return 11
    return int(r)

def bj_hand_value(hand):
    total = sum(bj_card_value(c) for c in hand)
    aces = sum(1 for c in hand if c['rank'] == 'A')
    while total > 21 and aces > 0: total -= 10; aces -= 1
    return total

def bj_new_deck():
    ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
    suits = ['♠','♥','♦','♣']
    deck = [{'rank':r,'suit':s} for r in ranks for s in suits]
    random.shuffle(deck); return deck

@app.route('/api/game/blackjack/deal', methods=['POST'])
@login_required
def api_bj_deal():
    err = check_game_disabled('Блэкджек')
    if err: return err
    user = current_user(); data = request.get_json(); bet, e = validate_bet(user, data)
    if e: return e
    deck = bj_new_deck(); player = [deck.pop(), deck.pop()]; dealer = [deck.pop(), deck.pop()]
    session['bj_deck']=deck; session['bj_player']=player; session['bj_dealer']=dealer; session['bj_bet']=bet; session['bj_done']=False
    pv, dv = bj_hand_value(player), bj_hand_value(dealer)
    if pv==21 and dv==21:
        session['bj_done']=True; new_bal, profit, _ = record_game(session['user_id'], 'Блэкджек', bet, False, bet, 'Push')
        return jsonify({'player':player,'dealer':dealer,'player_value':pv,'dealer_value':dv,'status':'push','message':'Ничья!','payout':bet,'profit':0,'balance':new_bal,'done':True})
    elif pv==21:
        session['bj_done']=True; payout=bet*3.0  # ЩЕДРЕЕ: BJ = x3 (было x2.5)
        new_bal, profit, _ = record_game(session['user_id'], 'Блэкджек', bet, True, payout, 'BJ x3')
        log_game_result(get_username(), 'Блэкджек', bet, True, profit, payout, new_bal)
        return jsonify({'player':player,'dealer':dealer,'player_value':pv,'dealer_value':dv,'status':'blackjack','message':'🎉 БЛЭКДЖЕК!','payout':payout,'profit':profit,'balance':new_bal,'done':True})
    return jsonify({'player':player,'dealer':[dealer[0],{'rank':'?','suit':'?'}],'player_value':pv,'dealer_value':bj_card_value(dealer[0]),'status':'playing','done':False})

@app.route('/api/game/blackjack/hit', methods=['POST'])
@login_required
def api_bj_hit():
    if session.get('bj_done'): return jsonify({'success':False,'message':'Игра завершена'})
    deck=session['bj_deck']; player=session['bj_player']; bet=session['bj_bet']
    player.append(deck.pop()); pv=bj_hand_value(player)
    session['bj_player']=player; session['bj_deck']=deck
    if pv>21:
        session['bj_done']=True; dealer=session['bj_dealer']
        new_bal, profit, _ = record_game(session['user_id'], 'Блэкджек', bet, False, 0, f'Bust {pv}')
        log_game_result(get_username(), 'Блэкджек', bet, False, profit, 0, new_bal)
        return jsonify({'player':player,'dealer':dealer,'player_value':pv,'dealer_value':bj_hand_value(dealer),'status':'bust','message':f'💥 Перебор! ({pv})','payout':0,'profit':profit,'balance':new_bal,'done':True})
    if pv==21: return api_bj_stand()
    return jsonify({'player':player,'player_value':pv,'status':'playing','done':False})

@app.route('/api/game/blackjack/stand', methods=['POST'])
@login_required
def api_bj_stand():
    if session.get('bj_done'): return jsonify({'success':False,'message':'Завершена'})
    session['bj_done']=True
    deck,player,dealer,bet = session['bj_deck'],session['bj_player'],session['bj_dealer'],session['bj_bet']
    pv = bj_hand_value(player)
    while bj_hand_value(dealer)<17: dealer.append(deck.pop())
    dv = bj_hand_value(dealer)
    if dv>21: payout=bet*2.2; new_bal,profit,_=record_game(session['user_id'],'Блэкджек',bet,True,payout,f'Дилер bust {dv}'); status,msg='win',f'🎉 Дилер перебрал!'
    elif pv>dv: payout=bet*2.2; new_bal,profit,_=record_game(session['user_id'],'Блэкджек',bet,True,payout,f'{pv}vs{dv}'); status,msg='win',f'🎉 {pv} vs {dv}'
    elif pv==dv: payout=bet; new_bal,profit,_=record_game(session['user_id'],'Блэкджек',bet,False,bet,f'Push {pv}'); status,msg='push',f'Ничья {pv}'
    else: payout=0; new_bal,profit,_=record_game(session['user_id'],'Блэкджек',bet,False,0,f'{pv}vs{dv}'); status,msg='loss',f'😢 {pv} vs {dv}'
    log_game_result(get_username(),'Блэкджек',bet,status=='win',profit,payout,new_bal)
    return jsonify({'player':player,'dealer':dealer,'player_value':pv,'dealer_value':dv,'status':status,'message':msg,'payout':payout,'profit':profit,'balance':new_bal,'done':True})

# 7. MINES — фикс + честная формула + минимальный edge
@app.route('/game/mines')
@login_required
def game_mines():
    console.log_game_enter(get_username(), 'mines')
    return render_template('game_mines.html', user=current_user(), dev=DEVELOPER)

def mines_multiplier(safe_total, opened):
    """Честный множитель для мин с минимальным edge (~1%)"""
    mult = 1.0
    for i in range(opened):
        remaining_safe = safe_total - i
        remaining_total = 25 - i
        if remaining_safe <= 0: return mult
        mult *= remaining_total / remaining_safe
    return max(round(mult * 0.99, 2), 1.0)

@app.route('/api/game/mines/start', methods=['POST'])
@login_required
def api_mines_start():
    err = check_game_disabled('Мины')
    if err: return err
    user = current_user(); data = request.get_json(); bet, e = validate_bet(user, data)
    if e: return e
    mc = max(1, min(24, int(data.get('mines', 3))))
    session['mines_field'] = list(random.sample(range(25), mc))
    session['mines_bet'] = bet
    session['mines_count'] = mc
    session['mines_opened'] = []
    session['mines_active'] = True
    return jsonify({'success': True, 'mines': mc, 'bet': bet})

@app.route('/api/game/mines/open', methods=['POST'])
@login_required
def api_mines_open():
    if not session.get('mines_active'):
        return jsonify({'success': False, 'message': 'Начните новую игру'})
    cell = int(request.get_json().get('cell', -1))
    mines = set(session['mines_field'])
    opened = session['mines_opened']
    bet = session['mines_bet']
    mc = session['mines_count']
    safe = 25 - mc

    if cell < 0 or cell > 24:
        return jsonify({'success': False, 'message': 'Неверная клетка'})
    if cell in opened:
        return jsonify({'success': False, 'message': 'Уже открыта'})

    if cell in mines:
        session['mines_active'] = False
        new_bal, profit, _ = record_game(
            session['user_id'], 'Мины', bet, False, 0,
            f'Boom {len(opened)} cells'
        )
        log_game_result(get_username(), 'Мины', bet, False, profit, 0, new_bal)
        return jsonify({
            'success': True, 'mine': True, 'cell': cell,
            'mines': list(mines), 'balance': new_bal,
            'profit': profit, 'multiplier': 0
        })

    opened.append(cell)
    session['mines_opened'] = opened
    mult = mines_multiplier(safe, len(opened))
    return jsonify({
        'success': True, 'mine': False, 'cell': cell,
        'opened': opened, 'multiplier': mult,
        'current_payout': round(bet * mult, 2),
        'remaining_safe': safe - len(opened)
    })

@app.route('/api/game/mines/cashout', methods=['POST'])
@login_required
def api_mines_cashout():
    if not session.get('mines_active'):
        return jsonify({'success': False, 'message': 'Нет игры'})
    opened = session['mines_opened']
    if not opened:
        return jsonify({'success': False, 'message': 'Откройте клетку'})
    bet = session['mines_bet']
    mc = session['mines_count']
    safe = 25 - mc
    mult = mines_multiplier(safe, len(opened))
    payout = round(bet * mult, 2)
    session['mines_active'] = False
    new_bal, profit, _ = record_game(
        session['user_id'], 'Мины', bet, True, payout, f'x{mult}'
    )
    log_game_result(get_username(), 'Мины', bet, True, profit, payout, new_bal)
    return jsonify({
        'success': True, 'multiplier': mult, 'payout': payout,
        'profit': profit, 'balance': new_bal,
        'mines': session['mines_field']
    })

# 8. HI-LO
@app.route('/game/hilo')
@login_required
def game_hilo():
    console.log_game_enter(get_username(), 'hilo')
    return render_template('game_hilo.html', user=current_user(), dev=DEVELOPER)

HILO_RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']

@app.route('/api/game/hilo/start', methods=['POST'])
@login_required
def api_hilo_start():
    err = check_game_disabled('Хай-Лоу')
    if err: return err
    user = current_user(); data = request.get_json(); bet, e = validate_bet(user, data)
    if e: return e
    card = {'rank':random.choice(HILO_RANKS),'suit':random.choice(['♠','♥','♦','♣'])}
    session['hilo_card']=card; session['hilo_bet']=bet; session['hilo_streak']=0; session['hilo_mult']=1.0; session['hilo_active']=True
    return jsonify({'success':True,'card':card,'bet':bet,'multiplier':1.0})

@app.route('/api/game/hilo/guess', methods=['POST'])
@login_required
def api_hilo_guess():
    if not session.get('hilo_active'): return jsonify({'success':False,'message':'Начните новую'})
    guess=request.get_json().get('guess','high'); cur=session['hilo_card']; bet=session['hilo_bet']
    nc={'rank':random.choice(HILO_RANKS),'suit':random.choice(['♠','♥','♦','♣'])}
    cv,nv=HILO_RANKS.index(cur['rank']),HILO_RANKS.index(nc['rank'])
    # ЩЕДРЕЕ: high/low принимают равные тоже как выигрыш
    ok = (guess=='high' and nv>=cv) or (guess=='low' and nv<=cv) or (guess=='same' and nv==cv)
    if ok:
        session['hilo_streak']+=1
        # ЩЕДРЕЕ: множители 2.0 / 15.0
        session['hilo_mult']=round(session['hilo_mult']*(15.0 if guess=='same' else 2.0),2)
        session['hilo_card']=nc
        return jsonify({'success':True,'correct':True,'new_card':nc,'streak':session['hilo_streak'],'multiplier':session['hilo_mult'],'current_payout':round(bet*session['hilo_mult'],2)})
    session['hilo_active']=False
    new_bal,profit,_=record_game(session['user_id'],'Хай-Лоу',bet,False,0,f'Streak {session["hilo_streak"]}')
    log_game_result(get_username(),'Хай-Лоу',bet,False,profit,0,new_bal)
    return jsonify({'success':True,'correct':False,'new_card':nc,'balance':new_bal,'profit':profit})

@app.route('/api/game/hilo/cashout', methods=['POST'])
@login_required
def api_hilo_cashout():
    if not session.get('hilo_active') or session['hilo_streak']==0: return jsonify({'success':False,'message':'Нечего забирать'})
    bet=session['hilo_bet']; mult=session['hilo_mult']; payout=round(bet*mult,2); session['hilo_active']=False
    new_bal,profit,_=record_game(session['user_id'],'Хай-Лоу',bet,True,payout,f'x{mult} streak {session["hilo_streak"]}')
    log_game_result(get_username(),'Хай-Лоу',bet,True,profit,payout,new_bal)
    return jsonify({'success':True,'multiplier':mult,'payout':payout,'profit':profit,'balance':new_bal})

# 9. RACES — фаворит побеждает чаще
@app.route('/game/races')
@login_required
def game_races():
    console.log_game_enter(get_username(), 'races')
    return render_template('game_races.html', user=current_user(), dev=DEVELOPER)

@app.route('/api/game/races', methods=['POST'])
@login_required
def api_game_races():
    err = check_game_disabled('Скачки')
    if err: return err
    user = current_user(); data = request.get_json(); bet, e = validate_bet(user, data)
    if e: return e
    chosen=max(1,min(6,int(data.get('horse',1))))
    horses=['Молния','Буран','Стрела','Гром','Ветер','Комета']
    odds=[2.2, 2.8, 3.5, 4.5, 6.0, 9.0]  # ЩЕДРЕЕ: чуть выше коэффициенты
    # Веса: обратно пропорциональны odds (фаворит чаще побеждает)
    weights = [1/o for o in odds]
    winner = random.choices(range(1,7), weights=weights, k=1)[0]
    positions=[]
    for step in range(20):
        sp=[]
        for h in range(6):
            if h+1==winner: prog=min(100,(step+1)*5+random.randint(0,3))
            else: prog=min(95 if step<19 else random.randint(60,92),(step+1)*random.randint(2,5)+random.randint(0,5))
            sp.append(min(prog,100))
        if step==19: sp[winner-1]=100
        positions.append(sp)
    is_win=chosen==winner; mult=odds[chosen-1] if is_win else 0; payout=bet*mult
    details=f"{horses[chosen-1]}→{horses[winner-1]}"
    new_bal,profit,_=record_game(session['user_id'],'Скачки',bet,is_win,payout,details)
    log_game_result(get_username(),'Скачки',bet,is_win,profit,payout,new_bal)
    return jsonify({'success':True,'winner':winner,'chosen':chosen,'horses':[f'🏇 {h}' for h in horses],'odds':odds,'positions':positions,'is_win':is_win,'multiplier':mult,'payout':payout,'profit':profit,'balance':new_bal})

# 10. WHEEL — исправлена синхронизация угла + щедрее веса
@app.route('/game/wheel')
@login_required
def game_wheel():
    console.log_game_enter(get_username(), 'wheel')
    return render_template('game_wheel.html', user=current_user(), dev=DEVELOPER)

@app.route('/api/game/wheel', methods=['POST'])
@login_required
def api_game_wheel():
    err = check_game_disabled('Колесо')
    if err: return err
    user = current_user(); data = request.get_json(); bet, e = validate_bet(user, data)
    if e: return e
    # ЩЕДРЕЕ: убрал x0, повысил веса выигрышных
    segments = [
        {'label':'x0.5','mult':0.5,'color':'#4a1942','weight':22},
        {'label':'x1',  'mult':1,  'color':'#6b21a8','weight':25},
        {'label':'x1.5','mult':1.5,'color':'#7c3aed','weight':20},
        {'label':'x2',  'mult':2,  'color':'#2563eb','weight':15},
        {'label':'x3',  'mult':3,  'color':'#059669','weight':10},
        {'label':'x5',  'mult':5,  'color':'#d97706','weight':5},
        {'label':'x10', 'mult':10, 'color':'#dc2626','weight':2},
        {'label':'x25', 'mult':25, 'color':'#f59e0b','weight':0.7},
        {'label':'x50', 'mult':50, 'color':'#10b981','weight':0.3},
    ]
    idx = random.choices(range(len(segments)), weights=[s['weight'] for s in segments], k=1)[0]
    result = segments[idx]
    mult = result['mult']
    payout = bet * mult
    is_win = mult > 1  # x0.5 не считаем выигрышем

    new_bal, profit, _ = record_game(
        session['user_id'], 'Колесо', bet, is_win,
        payout, f'Колесо: {result["label"]}'
    )
    log_game_result(get_username(), 'Колесо', bet, is_win, profit, payout, new_bal)
    return jsonify({
        'success': True,
        'segment_index': idx,
        'segments': segments,
        'multiplier': mult,
        'label': result['label'],
        'payout': payout,
        'profit': profit,
        'is_win': is_win,
        'balance': new_bal
    })


# ─── stats/inactive threads ───

def stats_printer():
    while True: time.sleep(300); console.print_stats()

def inactive_checker():
    while True:
        time.sleep(60)
        now = datetime.now()
        for uid, data in list(console.online_users.items()):
            if (now - data['last_action']).total_seconds() > 300:
                set_user_online(uid, False)
                console.log_disconnect(data['username'], uid)


# ═══════════════════════════════════════
#       NEW GAMES (Tower, Limbo, Penalty, Keno) + CHAT
# ═══════════════════════════════════════

# ── 11. TOWER ── (щедрее)

@app.route('/game/tower')
@login_required
def game_tower():
    console.log_game_enter(get_username(), 'tower')
    return render_template('game_tower.html', user=current_user(), dev=DEVELOPER)


@app.route('/api/game/tower/start', methods=['POST'])
@login_required
def api_tower_start():
    err = check_game_disabled('Башня')
    if err: return err
    user = current_user()
    data = request.get_json()
    bet, e = validate_bet(user, data)
    if e: return e

    difficulty = data.get('difficulty', 'medium')
    doors_map = {'easy': 4, 'medium': 3, 'hard': 2}
    num_doors = doors_map.get(difficulty, 3)

    floors = [random.randint(0, num_doors - 1) for _ in range(10)]

    session['tower_floors'] = floors
    session['tower_bet'] = bet
    session['tower_level'] = 0
    session['tower_doors'] = num_doors
    session['tower_difficulty'] = difficulty
    session['tower_active'] = True

    # ЩЕДРЕЕ: edge всего 1%
    base = num_doors / (num_doors - 1)
    multipliers = [round(base ** (i + 1) * 0.99, 2) for i in range(10)]
    session['tower_multipliers'] = multipliers

    return jsonify({
        'success': True, 'bet': bet, 'doors': num_doors,
        'difficulty': difficulty, 'multipliers': multipliers
    })


@app.route('/api/game/tower/choose', methods=['POST'])
@login_required
def api_tower_choose():
    if not session.get('tower_active'):
        return jsonify({'success': False, 'message': 'Начните новую игру'})

    data = request.get_json()
    door = int(data.get('door', 0))
    level = session['tower_level']
    floors = session['tower_floors']
    bet = session['tower_bet']
    multipliers = session['tower_multipliers']
    num_doors = session['tower_doors']

    if door < 0 or door >= num_doors:
        return jsonify({'success': False, 'message': 'Неверная дверь'})

    trap = floors[level]
    is_safe = (door != trap)

    if is_safe:
        session['tower_level'] = level + 1
        current_mult = multipliers[level]
        current_payout = round(bet * current_mult, 2)

        if level + 1 >= 10:
            session['tower_active'] = False
            new_bal, profit, _ = record_game(
                session['user_id'], 'Башня', bet, True, current_payout,
                f'🗼 Все 10 этажей! x{current_mult}'
            )
            log_game_result(get_username(), 'Башня', bet, True, profit, current_payout, new_bal)
            send_system_message(f'🗼 {get_username()} прошёл ВСЮ БАШНЮ и выиграл {current_payout:,.0f}₽!')
            return jsonify({
                'success': True, 'safe': True, 'level': level + 1,
                'multiplier': current_mult, 'payout': current_payout,
                'completed': True, 'trap': trap,
                'profit': profit, 'balance': new_bal, 'all_traps': floors
            })

        return jsonify({
            'success': True, 'safe': True, 'level': level + 1,
            'multiplier': current_mult, 'payout': current_payout,
            'trap': trap, 'completed': False
        })
    else:
        session['tower_active'] = False
        new_bal, profit, _ = record_game(
            session['user_id'], 'Башня', bet, False, 0,
            f'💀 Этаж {level + 1}, дверь {door + 1}'
        )
        log_game_result(get_username(), 'Башня', bet, False, profit, 0, new_bal)
        return jsonify({
            'success': True, 'safe': False, 'level': level,
            'trap': trap, 'balance': new_bal, 'profit': profit,
            'all_traps': floors
        })


@app.route('/api/game/tower/cashout', methods=['POST'])
@login_required
def api_tower_cashout():
    if not session.get('tower_active'):
        return jsonify({'success': False, 'message': 'Нет активной игры'})

    level = session['tower_level']
    if level == 0:
        return jsonify({'success': False, 'message': 'Пройдите хотя бы 1 этаж'})

    bet = session['tower_bet']
    mult = session['tower_multipliers'][level - 1]
    payout = round(bet * mult, 2)

    session['tower_active'] = False
    new_bal, profit, _ = record_game(
        session['user_id'], 'Башня', bet, True, payout,
        f'🗼 Кэшаут этаж {level} x{mult}'
    )
    log_game_result(get_username(), 'Башня', bet, True, profit, payout, new_bal)

    return jsonify({
        'success': True, 'multiplier': mult, 'payout': payout,
        'profit': profit, 'balance': new_bal,
        'all_traps': session['tower_floors']
    })


# ── 12. LIMBO — минимальный edge

@app.route('/game/limbo')
@login_required
def game_limbo():
    console.log_game_enter(get_username(), 'limbo')
    return render_template('game_limbo.html', user=current_user(), dev=DEVELOPER)


@app.route('/api/game/limbo', methods=['POST'])
@login_required
def api_game_limbo():
    err = check_game_disabled('Лимбо')
    if err: return err
    user = current_user()
    data = request.get_json()
    bet, e = validate_bet(user, data)
    if e: return e

    target = float(data.get('target', 2.0))
    if target < 1.01: target = 1.01
    if target > 1000: target = 1000

    r = random.random()
    # ЩЕДРЕЕ: edge 0.5% (было 2%)
    result = round(0.995 / r, 2) if r > 0 else 1000.0
    result = min(result, 1000.0)

    is_win = result >= target
    payout = round(bet * target, 2) if is_win else 0

    details = f'Цель: {target}x | Результат: {result}x'
    new_bal, profit, _ = record_game(session['user_id'], 'Лимбо', bet, is_win, payout, details)
    log_game_result(get_username(), 'Лимбо', bet, is_win, profit, payout, new_bal)

    if is_win and profit >= 10000:
        send_system_message(f'🎯 {get_username()} выиграл {profit:,.0f}₽ в Лимбо (x{target})!')

    return jsonify({
        'success': True, 'target': target, 'result': result,
        'is_win': is_win, 'payout': payout, 'profit': profit,
        'balance': new_bal
    })


# ── 13. PENALTY — вратарь реже дотягивается

@app.route('/game/penalty')
@login_required
def game_penalty():
    console.log_game_enter(get_username(), 'penalty')
    return render_template('game_penalty.html', user=current_user(), dev=DEVELOPER)


@app.route('/api/game/penalty', methods=['POST'])
@login_required
def api_game_penalty():
    err = check_game_disabled('Пенальти')
    if err: return err
    user = current_user()
    data = request.get_json()
    bet, e = validate_bet(user, data)
    if e: return e

    kick_pos = int(data.get('kick', 4))
    if kick_pos < 0 or kick_pos > 8: kick_pos = 4

    keeper_main = random.randint(0, 8)
    adjacent = {
        0: [1, 3], 1: [0, 2, 4], 2: [1, 5],
        3: [0, 4, 6], 4: [1, 3, 5, 7], 5: [2, 4, 8],
        6: [3, 7], 7: [4, 6, 8], 8: [5, 7]
    }

    keeper_positions = {keeper_main}
    # ЩЕДРЕЕ: 15% вместо 30% что дотянется
    if random.random() < 0.15 and adjacent.get(keeper_main):
        extra = random.choice(adjacent[keeper_main])
        keeper_positions.add(extra)

    is_goal = kick_pos not in keeper_positions

    corners = {0, 2, 6, 8}
    edges = {1, 3, 5, 7}

    if kick_pos in corners: mult = 3.5    # ЩЕДРЕЕ
    elif kick_pos in edges: mult = 2.8
    else: mult = 2.2

    payout = round(bet * mult, 2) if is_goal else 0

    positions = ['↖️','⬆️','↗️','⬅️','⏺️','➡️','↙️','⬇️','↘️']
    details = f'⚽ {positions[kick_pos]} vs 🧤 {positions[keeper_main]} → {"ГОЛ" if is_goal else "МИМО"}'

    new_bal, profit, _ = record_game(session['user_id'], 'Пенальти', bet, is_goal, payout, details)
    log_game_result(get_username(), 'Пенальти', bet, is_goal, profit, payout, new_bal)

    return jsonify({
        'success': True, 'kick': kick_pos, 'keeper': keeper_main,
        'keeper_positions': list(keeper_positions),
        'is_goal': is_goal, 'multiplier': mult if is_goal else 0,
        'payout': payout, 'profit': profit, 'balance': new_bal
    })


# ── 14. KENO — щедрее выплаты

@app.route('/game/keno')
@login_required
def game_keno():
    console.log_game_enter(get_username(), 'keno')
    return render_template('game_keno.html', user=current_user(), dev=DEVELOPER)


@app.route('/api/game/keno', methods=['POST'])
@login_required
def api_game_keno():
    err = check_game_disabled('Кено')
    if err: return err
    user = current_user()
    data = request.get_json()
    bet, e = validate_bet(user, data)
    if e: return e

    chosen = data.get('numbers', [])
    if not chosen or len(chosen) < 1 or len(chosen) > 10:
        return jsonify({'success': False, 'message': 'Выберите от 1 до 10 чисел'})

    chosen = [int(n) for n in chosen if 1 <= int(n) <= 40]
    chosen = list(set(chosen))[:10]

    drawn = sorted(random.sample(range(1, 41), 10))
    hits = sorted(set(chosen) & set(drawn))
    num_hits = len(hits)
    num_chosen = len(chosen)

    # ЩЕДРЕЕ: множители подняты + добавлены выплаты за меньшее число попаданий
    payout_table = {
        1:  {0: 0.5, 1: 4},
        2:  {1: 2,   2: 8},
        3:  {1: 1.2, 2: 4,   3: 15},
        4:  {2: 3,   3: 8,   4: 40},
        5:  {2: 2,   3: 5,   4: 15,  5: 80},
        6:  {3: 3,   4: 8,   5: 30,  6: 150},
        7:  {3: 2,   4: 5,   5: 15,  6: 80,   7: 300},
        8:  {4: 3,   5: 8,   6: 30,  7: 150,  8: 750},
        9:  {4: 2,   5: 5,   6: 15,  7: 80,   8: 400,  9: 1500},
        10: {5: 3,   6: 8,   7: 30,  8: 150,  9: 750, 10: 5000},
    }

    mult = payout_table.get(num_chosen, {}).get(num_hits, 0)
    payout = round(bet * mult, 2)
    is_win = mult > 1  # >x1 считаем реальным выигрышем

    details = f'Выбрано {num_chosen}, попаданий {num_hits}, x{mult}'
    new_bal, profit, _ = record_game(session['user_id'], 'Кено', bet, is_win, payout, details)
    log_game_result(get_username(), 'Кено', bet, is_win, profit, payout, new_bal)

    if is_win and profit >= 10000:
        send_system_message(f'🎱 {get_username()} выиграл {profit:,.0f}₽ в Кено ({num_hits}/{num_chosen})!')

    return jsonify({
        'success': True, 'chosen': chosen, 'drawn': drawn,
        'hits': hits, 'num_hits': num_hits,
        'multiplier': mult, 'payout': payout,
        'profit': profit, 'is_win': is_win, 'balance': new_bal,
        'payout_table': payout_table.get(num_chosen, {})
    })


# ── CHAT ──

@app.route('/api/chat/send', methods=['POST'])
@login_required
def api_chat_send():
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message: return jsonify({'success': False})
    if len(message) > 500: message = message[:500]
    user = current_user()
    if user.get('is_banned'):
        return jsonify({'success': False, 'message': 'Вы заблокированы'})
    send_chat_message(session['user_id'], get_username(), message)
    return jsonify({'success': True})


@app.route('/api/chat/messages')
@login_required
def api_chat_messages():
    after_id = int(request.args.get('after', 0))
    messages = get_chat_messages(50, after_id)
    return jsonify(messages)


# 5. CRASH — реалтайм график
@app.route('/game/crash')
@login_required
def game_crash():
    console.log_game_enter(get_username(), 'crash')
    return render_template('game_crash.html', user=current_user(), dev=DEVELOPER)

@app.route('/api/game/crash/start', methods=['POST'])
@login_required
def api_game_crash_start():
    err = check_game_disabled('Краш')
    if err: return err
    user = current_user()
    data = request.get_json()
    bet, err = validate_bet(user, data)
    if err: return err
    
    # Генерируем краш-поинт (щедрый: instant-crash всего 1.5%)
    r = random.random()
    crash_point = 1.0 if r < 0.015 else round(min(1/(1-r*0.99), 200.0), 2)
    
    # Сохраняем в сессии для проверки при кэшауте
    session['crash_bet'] = bet
    session['crash_point'] = crash_point
    session['crash_active'] = True
    
    return jsonify({
        'success': True,
        'crash_point': crash_point
    })

@app.route('/api/game/crash/cashout', methods=['POST'])
@login_required
def api_game_crash_cashout():
    if not session.get('crash_active'):
        return jsonify({'success': False, 'message': 'Нет активной игры'})
    
    data = request.get_json()
    bet = session['crash_bet']
    multiplier = float(data.get('multiplier', 1.0))
    crash_point = session['crash_point']
    
    # Проверка: не мошенничает ли клиент
    if multiplier > crash_point:
        # Игрок пытался забрать после краша — это loss
        session['crash_active'] = False
        new_bal, profit, _ = record_game(
            session['user_id'], 'Краш', bet, False, 0,
            f'Краш {crash_point}x (пытался забрать {multiplier}x)'
        )
        log_game_result(get_username(), 'Краш', bet, False, profit, 0, new_bal)
        return jsonify({
            'success': False,
            'message': 'Слишком поздно! Уже разбилось.',
            'balance': new_bal
        })
    
    # Успешный кэшаут
    payout = round(bet * multiplier, 2)
    session['crash_active'] = False
    
    new_bal, profit, _ = record_game(
        session['user_id'], 'Краш', bet, True, payout,
        f'Кэшаут {multiplier}x (краш {crash_point}x)'
    )
    log_game_result(get_username(), 'Краш', bet, True, profit, payout, new_bal)
    
    return jsonify({
        'success': True,
        'payout': payout,
        'profit': profit,
        'balance': new_bal
    })


if __name__ == '__main__':
    HOST, PORT = '0.0.0.0', 14651
    conn = get_db(); conn.execute('UPDATE users SET is_online=0'); conn.commit(); conn.close()
    console.print_banner(HOST, PORT)
    threading.Thread(target=stats_printer, daemon=True).start()
    threading.Thread(target=inactive_checker, daemon=True).start()
    import logging; logging.getLogger('werkzeug').setLevel(logging.WARNING)
    app.run(host=HOST, port=PORT, debug=False)
