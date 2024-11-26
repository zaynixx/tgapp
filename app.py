from flask import Flask, request, redirect
import requests

app = Flask(__name__)

# Конфигурация для работы с TOR через SOCKS5
TOR_PROXY = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

# Внешние сервисы, на которые нужно перенаправить трафик
VPN_TARGETS = {
    "tiktok": "https://www.tiktok.com",
    "instagram": "https://www.instagram.com"
}

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
                    window.location.href = '/redirect/tiktok';
                });

                document.getElementById('open-instagram').addEventListener('click', () => {
                    window.location.href = '/redirect/instagram';
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
        response = requests.get(search_url, proxies=TOR_PROXY)
        return response.text
    except Exception as e:
        return f"Ошибка при подключении через TOR: {e}", 500

@app.route('/redirect/<target>')
def redirect_vpn(target):
    url = VPN_TARGETS.get(target)
    if not url:
        return "Цель не найдена!", 404

    return redirect(url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
