from flask import Flask, request, redirect
import requests
import urllib.parse

app = Flask(__name__)

TOR_PROXY = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

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
            <title>Мини-апп через TOR и VPN</title>
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

                header {
                    background-color: #333;
                    color: #fff;
                    padding: 20px;
                    text-align: center;
                }

                h1 {
                    margin: 0;
                    font-size: 36px;
                }

                main {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin-top: 20px;
                }

                form {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin-bottom: 20px;
                }

                button:hover {
                    background-color: #555;
                }

                .buttons {
                    display: flex;
                    flex-direction: row;
                    justify-content: center;
                    align-items: center;
                    margin-top: 20px;
                }

                .buttons button {
                    margin-right: 10px;
                }       
            </style>
        </head>
        <body>
            <h1>Мини-апп через TOR и VPN</h1>
            <input type="text" id="search" placeholder="Введите запрос для поиска">
            <button id="search-tor">Поиск через TOR</button>
            <button id="open-tiktok">Открыть TikTok через VPN</button>
            <button id="open-instagram">Открыть Instagram через VPN</button>

            <script>
                // Обработка кнопок
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

import urllib.parse

@app.route('/search')
def search_tor():
    query = request.args.get('query', '')
    if not query:
        return "Введите запрос для поиска!", 400

    # Экранируем запрос для URL
    encoded_query = urllib.parse.quote(query)

    # Формируем правильный URL для поиска на Qwant
    search_url = f"https://www.qwant.com/?q={encoded_query}&t=web"

    # Логируем URL для отладки
    print(f"Запрос на Qwant: {search_url}")
    
    try:
        # Отправляем запрос через TOR
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
