from flask import Flask, request, redirect, render_template, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests

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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Используем SQLite для простоты
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Настройка Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модели базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    can_use_tiktok = db.Column(db.Boolean, default=False)
    can_use_instagram = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Создание базы данных
with app.app_context():
    db.create_all()

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Регистрация пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешна!', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Ошибка регистрации!', 'error')
    return render_template('register.html')

# Вход пользователя
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

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

# Перенаправление через TOR
@app.route('/redirect/<target>')
@login_required
def redirect_vpn(target):
    if current_user.is_admin or (target == '2ip' and current_user.is_authenticated):
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
    else:
        return "У вас нет прав для выполнения этого действия!", 403

# Панель администратора
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('У вас нет прав администратора!', 'error')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin.html', users=users)

# Настройки прав пользователей
@app.route('/set_permissions/<int:user_id>', methods=['POST'])
@login_required
def set_permissions(user_id):
    if not current_user.is_admin:
        flash('У вас нет прав администратора!', 'error')
        return redirect(url_for('index'))

    user = User.query.get(user_id)
    if user:
        user.can_use_instagram = 'instagram' in request.form
        user.can_use_tiktok = 'tiktok' in request.form
        db.session.commit()
        flash(f'Права для {user.username} обновлены!', 'success')
    return redirect(url_for('admin'))

# Загрузка пользователя в Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
