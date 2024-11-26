from flask import Flask, request, redirect, render_template, url_for, jsonify, flash
import requests
import sqlite3
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = b'\xf6Sy"\x0f\x8dc\xc3\x98t6\xafJ\xdd\x8aFV(M\xc7#0\x0cM'  # Уникальный ключ

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

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

# Заголовки
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Создание базы данных и таблиц
def init_db():
    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    # Создание таблиц пользователей и сессий
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            target TEXT,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Функция для добавления нового пользователя с хешированным паролем
def add_user(username, password):
    hashed_password = generate_password_hash(password)  # Хеширование пароля
    print(f"Хеш пароля для {username}: {hashed_password}")  # Логируем хеш
    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (username, password)
        VALUES (?, ?)
    ''', (username, hashed_password))
    conn.commit()
    conn.close()

# Проверка пароля при логине
def check_password(user, password):
    print(f"Проверяем пароль для пользователя {user[1]}")  # Логируем имя пользователя
    print(f"Пароль: {password} | Хеш: {user[2]}")  # Логируем введенный пароль и хеш в базе
    return check_password_hash(user[2], password)  # Проверка пароля с хешем

# Получение пользователя по имени
def get_user_by_username(username):
    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    print(f"Полученные данные для пользователя {username}: {user}")  # Логируем данные пользователя
    return user

# Логирование действий (посещение сайтов и другие действия)
def add_log(user_id, site, action=None):
    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO logs (user_id, action, target, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, action, site, timestamp))
    conn.commit()
    conn.close()

# Пользователь для Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# Загрузка пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(id=user[0], username=user[1], password=user[2])
    return None

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_confirmation = request.form['password_confirmation']
        
        # Проверка, что пароли совпадают
        if password != password_confirmation:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('register'))
        
        # Проверка, что пользователь не существует
        if get_user_by_username(username):
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('register'))
        
        # Добавление нового пользователя в базу данных
        add_user(username, password)
        
        # Перенаправление на страницу логина после успешной регистрации
        flash('Регистрация прошла успешно. Пожалуйста, войдите.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# Страница логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user:
            print(f"Найден пользователь: {user[1]}")
            if check_password(user, password):  # Используем функцию для проверки пароля
                login_user(User(id=user[0], username=user[1], password=user[2]))
                return redirect(url_for('index'))
            else:
                flash('Неверный логин или пароль', 'error')
        else:
            flash('Неверный логин или пароль', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

# Страница выхода
@app.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    add_log(user_id, 'Logout')  # Логирование выхода
    logout_user()
    return redirect(url_for('login'))

# Главная страница с доступом для авторизованных пользователей
@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

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
        add_log(current_user.id, 'Search', query)  # Логирование поиска
        return response.text
    except Exception as e:
        return f"Ошибка при подключении через TOR: {e}", 500

# Перенаправление через TOR на внешние сервисы
@app.route('/redirect/<target>')
@login_required
def redirect_vpn(target):
    user_id = current_user.id
    url = VPN_TARGETS.get(target)
    if not url:
        return "Цель не найдена!", 404

    add_log(user_id, 'Visit', target)  # Логирование посещения сайта

    try:
        if target == '2ip':
            response = requests.get(url, proxies=TOR_PROXY, headers=headers)
            return response.text
        else:
            return redirect(url)
    except Exception as e:
        return f"Ошибка при подключении через TOR: {e}", 500

# Страница для просмотра логов (только для администраторов)
@app.route('/logs')
@login_required
def view_logs():
    if current_user.username != "admin":  # Убедитесь, что это администратор
        return "Доступ запрещен", 403

    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    c.execute('SELECT * FROM logs')
    logs = c.fetchall()
    conn.close()

    return render_template('logs.html', logs=logs)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
