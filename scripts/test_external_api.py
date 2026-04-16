"""
Тестовый скрипт для публичного API обменных курсов (open.er-api.com).
Демонстрирует простой GET-запрос и вывод результата.
"""
import requests
import json

def main():
    url = "https://open.er-api.com/v6/latest/USD"
    print(f"GET {url}")
    r = requests.get(url)
    print("Status:", r.status_code)
    try:
        data = r.json()
        print(json.dumps({
            "result": data.get("result"),
            "base_code": data.get("base_code"),
            "time_last_update_utc": data.get("time_last_update_utc"),
            "rates_sample": {k: data.get("rates", {}).get(k) for k in ["RUB", "EUR", "KZT"]}
        }, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Failed to decode JSON:", e)

if __name__ == '__main__':
    main()
