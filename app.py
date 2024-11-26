from flask import Flask, request, redirect
import requests

app = Flask(__name__)

# Конфигурация для работы с TOR
TOR_PROXY = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

# VPN ссылки
VPN_TARGETS = {
    "tiktok": "https://www.tiktok.com",
    "instagram": "https://www.instagram.com"
}


@app.route("/")
def home():
    return "Добро пожаловать в мини-приложение!"


@app.route('/search')
def search_tor():
    query = request.args.get('query', '')
    if not query:
        return "Введите запрос для поиска!", 400

    # Выполняем поиск через TOR
    search_url = f"https://duckduckgo.com/?q={query}"  # Используем DuckDuckGo для анонимности
    try:
        response = requests.get(search_url, proxies=TOR_PROXY)
        return response.text
    except Exception as e:
        return f"Ошибка при подключении через TOR: {e}", 500

@app.route('/redirect/<target>')
def redirect_vpn(target):
    url = VPN_TARGETS.get(target)
    if not url:
        return "Цель не найдена!", 404

    # Просто перенаправляем на URL через VPN (на уровне сервера настраивайте VPN)
    return redirect(url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
