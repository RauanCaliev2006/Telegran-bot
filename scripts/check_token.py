"""
Небольшой скрипт для проверки текущего токена бота (getMe).
Он читает `TOKEN` из `config.py` и делает запрос к Telegram Bot API.
Выводит краткий результат и имя пользователя бота (если токен рабочий).
"""
import sys
import os
import json
import requests

# Гарантируем, что корень проекта в sys.path, чтобы импортировать config.py
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import config
except Exception as e:
    print("Не удалось импортировать config.py:", e)
    sys.exit(2)

TOKEN = getattr(config, "TOKEN", None)

if not TOKEN:
    print("Токен не найден. Задайте переменную окружения ACCOUNTING_BOT_TOKEN или создайте config_secret.py с TOKEN = \"...\"")
    sys.exit(1)

base = f"https://api.telegram.org/bot{TOKEN}"

try:
    r = requests.get(base + "/getMe", timeout=10)
except Exception as e:
    print("Ошибка запроса:", e)
    sys.exit(2)

print("HTTP:", r.status_code)
try:
    data = r.json()
    ok = data.get("ok")
    if ok:
        result = data.get("result", {})
        print("ok: true")
        print("username:", result.get("username"))
        print("first_name:", result.get("first_name"))
    else:
        print("ok: false")
        print(json.dumps(data, ensure_ascii=False, indent=2))
except Exception as e:
    print("Не удалось распарсить JSON:", e)
    print(r.text)
    sys.exit(2)
