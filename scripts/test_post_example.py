"""
Пример POST-запроса к публичному эхо-сервису httpbin.org для демонстрации POST.
Скрипт отправляет JSON и печатает ответ.
"""
import requests
import json

def main():
    url = "https://httpbin.org/post"
    payload = {"test": "post_example", "value": 123}
    print(f"POST {url} payload={payload}")
    r = requests.post(url, json=payload)
    print(r.status_code)
    try:
        print(json.dumps(r.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print("Failed to decode JSON:", e)

if __name__ == '__main__':
    main()
