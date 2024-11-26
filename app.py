from flask import Flask, request, redirect, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Конфигурация для работы с TOR через SOCKS5
TOR_PROXY = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

# Внешние сервисы, на которые нужно перенаправить трафик
VPN_TARGETS = {
    "tiktok": "https://www.tiktok.com",
    "instagram": "https://www.instagram.com",
    "2ip": "https://2ip.ru"
}

# Заголовки для имитации браузера (чтобы избежать блокировок сайта)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Создание базы данных и таблиц, если они не существуют
def init_db():
    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    # Создаем таблицу пользователей, если не существует
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            allowed_sites TEXT
        )
    ''')
    # Создаем таблицу логов посещений, если не существует
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            site TEXT,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Функция для добавления нового пользователя
def add_user(name, allowed_sites):
    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO users (name, allowed_sites)
        VALUES (?, ?)
    ''', (name, allowed_sites))
    conn.commit()
    conn.close()

# Функция для получения пользователя по ID
def get_user_by_id(user_id):
    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

# Функция для добавления лога о посещении сайта
def add_log(user_id, site):
    conn = sqlite3.connect('user_activity.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO logs (user_id, site, timestamp)
        VALUES (?, ?, ?)
    ''', (user_id, site, timestamp))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Мини-апп через TOR</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin: 20px;
                }
                input[type="text"] {
                    width: 80%;
                    padding: 10px;
                    margin: 20px 0;
                }
                button {
                    display: block;
                    width: 80%;
                    padding: 10px;
                    margin: 10px auto;
                    font-size: 16px;
                }
            </style>
        </head>
        <body>
            <h1>Мини-апп через TOR</h1>
            <input type="text" id="search" placeholder="Введите запрос для поиска">
            <button id="search-tor">Поиск через TOR</button>
            <button id="open-tiktok">Открыть TikTok через TOR</button>
            <button id="open-instagram">Открыть Instagram через TOR</button>
            <button id="open-2ip">Открыть 2ip.ru через TOR</button>

            <script>
                document.getElementById('search-tor').addEventListener('click', () => {
                    const query = document.getElementById('search').value;
                    if (query) {
                        window.location.href = `/search?query=${encodeURIComponent(query)}`;
                    } else {
                        alert("Введите запрос для поиска.");
                    }
                });

                document.getElementById('open-tiktok').addEventListener('click', () => {
                    window.location.href = '/redirect/tiktok?user_id=1';  // Пример передачи ID
                });

                document.getElementById('open-instagram').addEventListener('click', () => {
                    window.location.href = '/redirect/instagram?user_id=1';
                });

                document.getElementById('open-2ip').addEventListener('click', () => {
                    window.location.href = '/redirect/2ip?user_id=1';
                });
            </script>
        </body>
        </html>
    '''

@app.route('/search')
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
def redirect_vpn(target):
    user_id = request.args.get('user_id', type=int)
    user = get_user_by_id(user_id)
    if not user:
        return "Пользователь не найден!", 404

    allowed_sites = user[2].split(',')
    if target not in allowed_sites:
        return "Доступ к этому сайту ограничен!", 403

    url = VPN_TARGETS.get(target)
    if not url:
        return "Цель не найдена!", 404

    # Логируем посещение
    add_log(user_id, target)

    try:
        if target == '2ip':
            response = requests.get(url, proxies=TOR_PROXY, headers=headers)
            return response.text  # Отправить содержимое 2ip.ru через Tor
        else:
            return redirect(url)
    except Exception as e:
        return f"Ошибка при подключении через TOR: {e}", 500

if __name__ == '__main__':
    init_db()  # Инициализация базы данных
    app.run(host='0.0.0.0', port=5000, debug=True)
