"""
Простой тест для Telegram Bot API: выполняет getMe и getUpdates.
Читает токен из переменной окружения ACCOUNTING_BOT_TOKEN или из config.py (если переменная не задана).
"""
import os
import sys
import json
import requests

# Ensure project root is on sys.path so importing config.py (in project root) works
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def get_token():
    token = os.environ.get("ACCOUNTING_BOT_TOKEN")
    if token:
        return token
    # fallback to config.py if present
    try:
        import config
        return getattr(config, "TOKEN")
    except Exception:
        return None


def main():
    token = get_token()
    if not token:
        print("ERROR: bot token not found. Set ACCOUNTING_BOT_TOKEN or add TOKEN to config.py")
        sys.exit(1)

    base = f"https://api.telegram.org/bot{token}"

    print("Calling getMe...")
    r = requests.get(base + "/getMe")
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=True))
    except Exception as e:
        print("Failed to decode JSON:", e)

    print("\nCalling getUpdates...")
    r = requests.get(base + "/getUpdates")
    print(r.status_code)
    try:
        resp = r.json()
        print(json.dumps(resp, indent=2, ensure_ascii=True))
    except Exception as e:
        print("Failed to decode JSON:", e)


if __name__ == '__main__':
    main()
