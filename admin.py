from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, jsonify, flash, send_file
)
import json

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

DEVELOPER = "dimasbotyara"


def admin_required(min_level='admin'):
    levels = {'user': 0, 'admin': 1, 'super_admin': 2, 'owner': 3}

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))

            from models import get_admin_level
            username = session.get('username', '')
            ip = request.remote_addr
            level = get_admin_level(username, ip)

            if levels.get(level, 0) < levels.get(min_level, 0):
                flash('Недостаточно прав', 'error')
                return redirect(url_for('dashboard'))

            kwargs['admin_level'] = level
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_level_info(level):
    info = {
        'owner': {'name': 'OWNER', 'color': 'amber', 'desc': 'Полный доступ'},
        'super_admin': {'name': 'SUPER ADMIN', 'color': 'violet', 'desc': 'Расширенный доступ'},
        'admin': {'name': 'ADMIN', 'color': 'blue', 'desc': 'Базовый доступ'},
    }
    return info.get(level, {'name': 'USER', 'color': 'gray', 'desc': 'Нет доступа'})


@admin_bp.route('/')
@admin_required('admin')
def admin_dashboard(admin_level):
    from models import (get_server_stats, get_all_users, get_all_settings,
                        get_active_broadcast, get_user_by_id)
    stats = get_server_stats()
    users = get_all_users()
    settings = get_all_settings()
    level_info = get_level_info(admin_level)
    broadcast = get_active_broadcast()
    user = get_user_by_id(session['user_id'])
    return render_template('admin.html',
        user=user, stats=stats, users=users, settings=settings,
        admin_level=admin_level, level_info=level_info,
        broadcast=broadcast, dev=DEVELOPER)


@admin_bp.route('/user/<int:user_id>')
@admin_required('admin')
def admin_user_detail(user_id, admin_level):
    from models import get_user_by_id, get_user_history
    target = get_user_by_id(user_id)
    if not target:
        flash('Пользователь не найден', 'error')
        return redirect(url_for('admin.admin_dashboard'))
    history = get_user_history(user_id, 50)
    level_info = get_level_info(admin_level)
    user = get_user_by_id(session['user_id'])
    return render_template('admin_user.html',
        user=user, target=target, history=history,
        admin_level=admin_level, level_info=level_info, dev=DEVELOPER)


@admin_bp.route('/api/set_balance', methods=['POST'])
@admin_required('admin')
def api_set_balance(admin_level):
    from models import get_user_by_id, set_user_balance, log_admin_action
    data = request.get_json()
    user_id = int(data.get('user_id', 0))
    new_balance = float(data.get('balance', 0))
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'success': False, 'message': 'Не найден'})
    old = target['balance']
    set_user_balance(user_id, new_balance)
    log_admin_action(session.get('username', ''), 'set_balance', target['username'],
        f'{old:.0f} -> {new_balance:.0f}', request.remote_addr)
    return jsonify({'success': True,
        'message': f'Баланс {target["username"]}: {old:.0f} -> {new_balance:.0f}'})


@admin_bp.route('/api/add_balance', methods=['POST'])
@admin_required('admin')
def api_add_balance(admin_level):
    from models import get_user_by_id, set_user_balance, log_admin_action
    data = request.get_json()
    user_id = int(data.get('user_id', 0))
    amount = float(data.get('amount', 0))
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'success': False, 'message': 'Не найден'})
    new_balance = target['balance'] + amount
    set_user_balance(user_id, new_balance)
    log_admin_action(session.get('username', ''), 'add_balance', target['username'],
        f'{amount:+.0f} (было {target["balance"]:.0f}, стало {new_balance:.0f})',
        request.remote_addr)
    return jsonify({'success': True,
        'message': f'{target["username"]}: {amount:+.0f} -> {new_balance:.0f}',
        'balance': new_balance})


@admin_bp.route('/api/ban', methods=['POST'])
@admin_required('super_admin')
def api_ban(admin_level):
    from models import get_user_by_id, ban_user, log_admin_action, OWNER_USERNAME
    data = request.get_json()
    user_id = int(data.get('user_id', 0))
    reason = data.get('reason', 'Нарушение правил')
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'success': False, 'message': 'Не найден'})
    if target['username'] == OWNER_USERNAME:
        return jsonify({'success': False, 'message': 'Нельзя забанить владельца'})
    ban_user(user_id, reason)
    log_admin_action(session.get('username', ''), 'ban', target['username'],
        reason, request.remote_addr)
    return jsonify({'success': True, 'message': f'{target["username"]} забанен'})


@admin_bp.route('/api/unban', methods=['POST'])
@admin_required('super_admin')
def api_unban(admin_level):
    from models import get_user_by_id, unban_user, log_admin_action
    data = request.get_json()
    user_id = int(data.get('user_id', 0))
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'success': False, 'message': 'Не найден'})
    unban_user(user_id)
    log_admin_action(session.get('username', ''), 'unban', target['username'],
        '', request.remote_addr)
    return jsonify({'success': True, 'message': f'{target["username"]} разбанен'})


@admin_bp.route('/api/kick', methods=['POST'])
@admin_required('admin')
def api_kick(admin_level):
    from models import get_user_by_id, set_user_online, log_admin_action
    data = request.get_json()
    user_id = int(data.get('user_id', 0))
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'success': False, 'message': 'Не найден'})
    set_user_online(user_id, False)
    log_admin_action(session.get('username', ''), 'kick', target['username'],
        '', request.remote_addr)
    return jsonify({'success': True, 'message': f'{target["username"]} кикнут'})


@admin_bp.route('/api/delete_user', methods=['POST'])
@admin_required('owner')
def api_delete_user(admin_level):
    from models import get_user_by_id, delete_user, log_admin_action, OWNER_USERNAME
    data = request.get_json()
    user_id = int(data.get('user_id', 0))
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'success': False, 'message': 'Не найден'})
    if target['username'] == OWNER_USERNAME:
        return jsonify({'success': False, 'message': 'Нельзя удалить владельца'})
    username = target['username']
    delete_user(user_id)
    log_admin_action(session.get('username', ''), 'delete_user', username,
        'Удалён', request.remote_addr)
    return jsonify({'success': True, 'message': f'{username} удалён'})


@admin_bp.route('/api/reset_stats', methods=['POST'])
@admin_required('super_admin')
def api_reset_stats(admin_level):
    from models import get_user_by_id, reset_user_stats, log_admin_action
    data = request.get_json()
    user_id = int(data.get('user_id', 0))
    target = get_user_by_id(user_id)
    if not target:
        return jsonify({'success': False, 'message': 'Не найден'})
    reset_user_stats(user_id)
    log_admin_action(session.get('username', ''), 'reset_stats', target['username'],
        '', request.remote_addr)
    return jsonify({'success': True, 'message': f'Стата {target["username"]} сброшена'})


@admin_bp.route('/api/set_admin', methods=['POST'])
@admin_required('owner')
def api_set_admin(admin_level):
    from models import get_user_by_username, set_admin_status, log_admin_action
    data = request.get_json()
    username = data.get('username', '')
    is_admin = data.get('is_admin', False)
    target = get_user_by_username(username)
    if not target:
        return jsonify({'success': False, 'message': 'Не найден'})
    set_admin_status(username, is_admin)
    action = 'grant_admin' if is_admin else 'revoke_admin'
    log_admin_action(session.get('username', ''), action, username, '', request.remote_addr)
    status = 'назначен админом' if is_admin else 'снят с админки'
    return jsonify({'success': True, 'message': f'{username} {status}'})


@admin_bp.route('/api/update_settings', methods=['POST'])
@admin_required('super_admin')
def api_update_settings(admin_level):
    from models import set_setting, log_admin_action
    data = request.get_json()
    for key, value in data.items():
        set_setting(key, value)
    log_admin_action(session.get('username', ''), 'update_settings', '',
        json.dumps(data, ensure_ascii=False), request.remote_addr)
    return jsonify({'success': True, 'message': 'Настройки сохранены'})


@admin_bp.route('/api/broadcast', methods=['POST'])
@admin_required('admin')
def api_broadcast(admin_level):
    from models import create_broadcast, log_admin_action
    data = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'success': False, 'message': 'Пустое сообщение'})
    create_broadcast(message, session.get('username', ''))
    log_admin_action(session.get('username', ''), 'broadcast', '', message, request.remote_addr)
    return jsonify({'success': True, 'message': 'Отправлено'})


@admin_bp.route('/api/clear_broadcast', methods=['POST'])
@admin_required('admin')
def api_clear_broadcast(admin_level):
    from models import clear_broadcast
    clear_broadcast()
    return jsonify({'success': True, 'message': 'Снято'})


@admin_bp.route('/logs')
@admin_required('admin')
def admin_logs(admin_level):
    from models import get_admin_logs, get_user_by_id
    logs = get_admin_logs(200)
    level_info = get_level_info(admin_level)
    user = get_user_by_id(session['user_id'])
    return render_template('admin_logs.html',
        user=user, logs=logs, admin_level=admin_level,
        level_info=level_info, dev=DEVELOPER)


@admin_bp.route('/settings')
@admin_required('super_admin')
def admin_settings(admin_level):
    from models import get_all_settings, get_user_by_id
    settings = get_all_settings()
    level_info = get_level_info(admin_level)
    user = get_user_by_id(session['user_id'])
    return render_template('admin_settings.html',
        user=user, settings=settings, admin_level=admin_level,
        level_info=level_info, dev=DEVELOPER)


@admin_bp.route('/export_db')
@admin_required('owner')
def export_db(admin_level):
    from models import log_admin_action, DB_PATH
    log_admin_action(session.get('username', ''), 'export_db', '', '', request.remote_addr)
    return send_file(DB_PATH, as_attachment=True, download_name='casino_backup.db')


@admin_bp.route('/api/stats')
@admin_required('admin')
def api_stats(admin_level):
    from models import get_server_stats
    return jsonify(get_server_stats())


@admin_bp.route('/api/users')
@admin_required('admin')
def api_users(admin_level):
    from models import get_all_users
    return jsonify(get_all_users())