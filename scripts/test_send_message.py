"""
Пример POST-запроса к Telegram Bot API: отправка сообщения через sendMessage.
Сначала получает chat_id из getUpdates, затем отправляет тестовое сообщение.
"""
import os
import sys
import json
import requests

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def get_token():
    token = os.environ.get("ACCOUNTING_BOT_TOKEN")
    if token:
        return token
    try:
        import config
        return getattr(config, "TOKEN")
    except Exception:
        return None


def main():
    token = get_token()
    if not token:
        print("ERROR: bot token not found.")
        sys.exit(1)

    base = f"https://api.telegram.org/bot{token}"

    # 1) Получаем chat_id из последних обновлений
    print("=== GET getUpdates (для получения chat_id) ===")
    r = requests.get(base + "/getUpdates")
    print("Status:", r.status_code)
    updates = r.json()

    chat_id = None
    if updates.get("result"):
        chat_id = updates["result"][-1]["message"]["chat"]["id"]
        print(f"Найден chat_id: {chat_id}")
    else:
        print("Нет обновлений! Сначала напиши боту /start в Telegram, затем запусти скрипт снова.")
        sys.exit(1)

    # 2) POST sendMessage
    print("\n=== POST sendMessage ===")
    url = base + "/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "Привет! Это тестовое сообщение, отправленное через Telegram Bot API (POST sendMessage)."
    }
    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, ensure_ascii=True, indent=2)}")

    r = requests.post(url, json=payload)
    print(f"\nStatus: {r.status_code}")
    print(json.dumps(r.json(), indent=2, ensure_ascii=True))


if __name__ == '__main__':
    main()
