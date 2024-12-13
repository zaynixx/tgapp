import subprocess
import sqlite3
from flask import Flask, request, redirect, render_template, url_for, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import requests
import time
from bs4 import BeautifulSoup
import logging
import random
from urllib.parse import urljoin


app = Flask(__name__)
app.secret_key = 'super_secret_key_12345'  # Уникальный ключ для сессий

logging.basicConfig(level=logging.DEBUG)

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



USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

# Заголовки для HTTP-запросов
headers = {
    'User-Agent': get_random_user_agent()
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

def make_request(url, method="GET", data=None, proxies=None):
    headers = {
        'User-Agent': get_random_user_agent()
    }
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, data=data, proxies=proxies, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при запросе к {url}: {e}")
        raise

# Создание базы данных и таблицы пользователей
def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        can_use_tiktok INTEGER DEFAULT 0,
        can_use_instagram INTEGER DEFAULT 0,
        can_use_2ip INTEGER DEFAULT 0,
        balance INTEGER DEFAULT 0  -- Новое поле для баланса
    )
    ''')

    conn.commit()
    conn.close()

# Создаем таблицу при старте приложения
with app.app_context():
    create_db()

# Модели базы данных и логика пользователя
class User(UserMixin):
    def __init__(self, id, username, password, is_admin=False, can_use_tiktok=False, can_use_instagram=False, can_use_2ip=False, balance=None):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin
        self.can_use_tiktok = can_use_tiktok
        self.can_use_instagram = can_use_instagram
        self.can_use_2ip = can_use_2ip
        self.balance = balance

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

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buy_access/<target>', methods=['GET'])
@login_required
def buy_access(target):
    price = 666  # Цена для доступа
    return render_template('buy_access.html', target=target, price=price)

@app.route('/balance')
def balance():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM user WHERE id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    return render_template('template.html', balance=balance)

@app.route('/update_balance', methods=['POST'])
def update_balance():
    print("update_balance вызвана")
    data = request.get_json()
    print("data:", data)
    login = data.get('login')
    amount = data.get('amount')
    print("login:", login)
    print("amount:", amount)

    if not login or not amount:
        print("Недопустимые данные: login или amount отсутствуют")
        return jsonify({"error": "Недопустимые данные: login или amount отсутствуют"}), 400

    # Обновление баланса пользователя в базе данных
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    print("cursor создан")
    cursor.execute("UPDATE user SET balance = balance + ? WHERE username = ?", (amount, login))
    print("запрос выполнен")
    conn.commit()
    print("изменения сохранены")
    conn.close()
    print("соединение закрыто")

    # Отправка ответа на бота
    return jsonify({'message': 'Баланс обновлен успешно!'}), 200


# Регистрация
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
        
        remember = 'remember' in request.form  # Проверка флага "remember me"

        user = User.get_by_username(username)

        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)  # Передаем параметр remember
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

@app.route('/search_duckduckgo', methods=['GET'])
@login_required
def search_duckduckgo():
    query = request.args.get('query', '')
    if not query:
        flash("Введите запрос для поиска!", "error")
        return redirect(url_for('index'))

    duckduckgo_url = "https://html.duckduckgo.com/html/"
    try:
        logging.debug(f"Поиск по запросу: {query}")

        # Запрос через DuckDuckGo HTML
        response = make_request(
            url=duckduckgo_url,
            method="POST",
            data={"q": query},
            proxies=TOR_PROXY
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = []
        for result in soup.select('.result__a'):
            search_results.append({
                'title': result.text,
                'link': result['href']
            })

        logging.debug(f"Найдено результатов: {len(search_results)}")
        if not search_results:
            flash("Не удалось найти результаты поиска.", "warning")
            return redirect(url_for('index'))

        return render_template(
            'search_results_duckduckgo.html',
            results=search_results,
            query=query
        )
    except Exception as e:
        logging.error(f"Ошибка поиска: {e}")
        flash(f"Ошибка поиска: {e}", "error")
        return redirect(url_for('index'))




@app.route('/visit_link', methods=['GET'])
@login_required
def visit_link():
    target_url = request.args.get('url')
    if not target_url:
        return "URL не указан!", 400

    try:
        # Выполняем запрос к целевому сайту через TOR-прокси
        response = requests.get(target_url, proxies=TOR_PROXY, headers=headers)
        response.raise_for_status()

        # Возвращаем содержимое сайта
        return response.text
    except Exception as e:
        return f"Ошибка при подключении через TOR: {e}", 500

@app.route('/redirect/<target>')
@login_required
def redirect_vpn(target):
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
        start_vpn()

        if target == '2ip':
            response = requests.get(url, proxies=TOR_PROXY, headers=headers)
            return response.text
        else:
            return redirect(url)
    except Exception as e:
        return f"Ошибка при подключении через TOR или VPN: {e}", 500

@app.route('/open_2ip_vpn')
@login_required
def open_2ip_vpn():
    if not current_user.can_use_2ip:
        return redirect(url_for('buy_access', target='2ip'))

    try:
        start_vpn()

        url = "https://2ip.ru"
        response = requests.get(url, headers=headers)

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

    users = User.get_all_users()

    return render_template('admin.html', users=users)

# Эндпоинт для проверки авторизации и получения информации о текущем пользователе
@app.route('/me')
@login_required
def me():
    user_info = {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "can_use_tiktok": current_user.can_use_tiktok,
        "can_use_instagram": current_user.can_use_instagram,
        "can_use_2ip": current_user.can_use_2ip
    }
    return jsonify(user_info)


# Настройки прав пользователей
@app.route('/set_permissions/<int:user_id>', methods=['POST'])
@login_required
def set_permissions(user_id):
    if not current_user.is_admin:
        flash('У вас нет прав администратора!', 'error')
        return redirect(url_for('index'))

    user = User.get_by_id(user_id)  
    if user:
        can_use_instagram = 'instagram' in request.form
        can_use_tiktok = 'tiktok' in request.form
        can_use_2ip = '2ip' in request.form

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
    app.run(debug=True)
