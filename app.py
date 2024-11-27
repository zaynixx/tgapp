import subprocess
import sqlite3
from flask import Flask, request, redirect, render_template, url_for, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import subprocess
import time



app = Flask(__name__)
app.secret_key = 'super_secret_key_12345'  # Уникальный ключ для сессий

# Конфигурация для работы с TOR через SOCKS5
TOR_PROXY = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

# Внешние сервисы
VPN_TARGETS = {
    "tiktok": "https://www.tiktok.com",
    "instagram": "https://www.instagram.com",
    "2ip": "https://2ip.ru"
}

# Заголовки для HTTP-запросов
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Конфигурация базы данных
DB_NAME = 'users.db'

# Настройка Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Функция для запуска OpenVPN
def start_vpn():
    vpn_command = ["sudo", "openvpn", "--config", "cfg.ovpn"]
    subprocess.Popen(vpn_command)
    time.sleep(10)  # Даем время на установку соединения VPN
# Создание базы данных и таблицы пользователей
def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Обновление таблицы user для добавления нового поля
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        can_use_tiktok INTEGER DEFAULT 0,
        can_use_instagram INTEGER DEFAULT 0,
        can_use_2ip INTEGER DEFAULT 0  -- Новое поле для 2ip
    )
    ''')

    conn.commit()
    conn.close()

# Создаем таблицу при старте приложения
with app.app_context():
    create_db()

# Модели базы данных и логика пользователя
class User(UserMixin):
    def __init__(self, id, username, password, is_admin=False, can_use_tiktok=False, can_use_instagram=False, can_use_2ip=False):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin
        self.can_use_tiktok = can_use_tiktok
        self.can_use_instagram = can_use_instagram
        self.can_use_2ip = can_use_2ip 

    @staticmethod
    def get_by_id(user_id):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM user WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            return User(*user_data)  
        return None 

    @staticmethod
    def get_by_username(username):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM user WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()

        if user_data:
            return User(*user_data)
        return None

    @staticmethod
    def create(username, password):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        hashed_password = generate_password_hash(password)
        cursor.execute('''
        INSERT INTO user (username, password)
        VALUES (?, ?)
        ''', (username, hashed_password))

        conn.commit()
        conn.close()

    @staticmethod
    def get_all_users():
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM user')
        users_data = cursor.fetchall()
        conn.close()

        users = [User(*user_data) for user_data in users_data]
        return users

# Загрузка пользователя в Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

# Функция для запуска OpenVPN
def start_vpn():
    vpn_command = ["sudo", "openvpn", "--config", "cfg.ovpn"]
    subprocess.Popen(vpn_command)

@app.route('/')
def index():
    username = "логин"  # Пример: передаем имя пользователя в шаблон
    return render_template('index.html', username=username)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/buy_access/<target>', methods=['GET'])
@login_required
def buy_access(target):
    price = 666  # Цена для доступа
    return render_template('buy_access.html', target=target, price=price)



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.get_by_username(username):
            flash('Пользователь с таким именем уже существует!', 'error')
        else:
            User.create(username, password)
            flash('Регистрация успешна!', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.get_by_username(username)

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Добро пожаловать!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!', 'error')
    return render_template('login.html')

# Выход пользователя
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Выход выполнен!', 'success')
    return redirect(url_for('login'))

# Поиск через TOR
@app.route('/search')
@login_required
def search_tor():
    query = request.args.get('query', '')
    if not query:
        return "Введите запрос для поиска!", 400

    search_url = f"https://duckduckgo.com/?t=h_&q={query}&ia=web"
    try:
        response = requests.get(search_url, proxies=TOR_PROXY, headers=headers)
        return response.text
    except Exception as e:
        return f"Ошибка при подключении через TOR: {e}", 500


@app.route('/redirect/<target>')
@login_required
def redirect_vpn(target):
    # Проверка прав на доступ к сервису
    if target == 'instagram' and not current_user.can_use_instagram:
        return redirect(url_for('buy_access', target='instagram'))
    elif target == 'tiktok' and not current_user.can_use_tiktok:
        return redirect(url_for('buy_access', target='tiktok'))
    elif target == '2ip' and not current_user.can_use_2ip:
        return redirect(url_for('buy_access', target='2ip'))

    url = VPN_TARGETS.get(target)
    if not url:
        return "Цель не найдена!", 404

    try:
        # Запуск OpenVPN для трафика через него
        start_vpn()

        # После подключения через VPN, делаем запрос к целевому сервису
        if target == '2ip':
            response = requests.get(url, proxies=TOR_PROXY, headers=headers)
            return response.text
        else:
            # Для Instagram и TikTok перенаправляем через VPN
            return redirect(url)
    except Exception as e:
        return f"Ошибка при подключении через TOR или VPN: {e}", 500

@app.route('/open_2ip_vpn')
@login_required
def open_2ip_vpn():
    if not current_user.can_use_2ip:
        return redirect(url_for('buy_access', target='2ip'))

    try:
        # Запускаем OpenVPN перед тем как сделать запрос
        start_vpn()

        # URL для 2ip через VPN
        url = "https://2ip.ru"
        response = requests.get(url, headers=headers)  # Отправляем запрос через VPN

        return response.text
    except Exception as e:
        return f"Ошибка при подключении через VPN: {e}", 500

# Панель администратора
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('У вас нет прав администратора!', 'error')
        return redirect(url_for('index'))

    users = User.get_all_users()  # Получаем список пользователей в виде объектов

    return render_template('admin.html', users=users)

# Настройки прав пользователей
@app.route('/set_permissions/<int:user_id>', methods=['POST'])
@login_required
def set_permissions(user_id):
    if not current_user.is_admin:
        flash('У вас нет прав администратора!', 'error')
        return redirect(url_for('index'))

    user = User.get_by_id(user_id)  # Загружаем объект пользователя
    if user:
        can_use_instagram = 'instagram' in request.form
        can_use_tiktok = 'tiktok' in request.form
        can_use_2ip = '2ip' in request.form  # Получаем новое поле для 2ip

        # Обновляем права пользователя
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE user SET can_use_instagram = ?, can_use_tiktok = ?, can_use_2ip = ? WHERE id = ?
        ''', (can_use_instagram, can_use_tiktok, can_use_2ip, user_id))
        conn.commit()
        conn.close()

        flash(f'Права для {user.username} обновлены!', 'success')

    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
