from flask import Flask, request, redirect, render_template, url_for, jsonify, flash
import requests
from datetime import datetime

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

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Поиск через TOR
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

# Перенаправление через TOR
@app.route('/redirect/<target>')
def redirect_vpn(target):
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
