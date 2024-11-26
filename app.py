from flask import Flask, request, redirect, render_template, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'super_secret_key_12345'  # Уникальный ключ для сессий
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

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

# Модели базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')  # 'admin' или 'user'

# Загрузка пользователя для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    if user_id is None:
        return None
    return User.query.get(int(user_id))

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Для простоты, в реальном проекте используйте хеширование пароля
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html')

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # В реальном проекте используйте хеширование паролей
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

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

# Перенаправление через TOR с проверкой прав пользователя
@app.route('/redirect/<target>')
@login_required
def redirect_vpn(target):
    if current_user.role == 'user' and target in ['tiktok', 'instagram']:
        return "У вас нет прав для использования этого ресурса.", 403

    url = VPN_TARGETS.get(target)
    if not url:
        return "Цель не найдена!", 404

    try:
        if target == '2ip':
            response = requests.get(url, proxies=TOR_PROXY, headers=headers)
            return response.text
        else:
            return redirect(url)
    except Exception as e:
        return f"Ошибка при подключении через TOR: {e}", 500

# Админка для управления правами
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if current_user.username != 'zaynix':
        return "Доступ запрещен", 403

    if request.method == 'POST':
        target_user = User.query.filter_by(username=request.form['username']).first()
        if target_user:
            target_user.role = request.form['role']
            db.session.commit()
            flash(f"Права пользователя {target_user.username} изменены!")
    
    users = User.query.all()
    return render_template('admin.html', users=users)

# Шаг 6: Запуск приложения
if __name__ == '__main__':
    db.create_all()  # Создает таблицы в базе данных
    app.run(host='0.0.0.0', port=5000, debug=True)
