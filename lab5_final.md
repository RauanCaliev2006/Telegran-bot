- Жоба: Telegram-бот — кіріс/шығыс транзакцияларын жазу (тип, санат, сома, күн). Мәліметтер SQLite (`transactions.db`)–да сақталады.
- Тіл: Python 3.13 (aiogram). Тест скрипттер — Python + requests.
- Пайдаланылған API:
  - Telegram Bot API — getMe, getUpdates
  - exchangerate.host — GET `/latest` (мысал)
  - httpbin.org — POST мысалы

Қалай көрсету (қысқа):
1) PowerShell‑де іске қосыңыз:
python scripts\test_external_api.py > scripts\external_api_output.txt
python scripts\test_telegram_api.py > scripts\telegram_api_output.txt
python scripts\test_post_example.py > scripts\post_output.txt
```
2) `scripts/*_output.txt` файлдарын ашып көрсетіңіз немесе скриншот жасаңыз.

Ескерту: токенді (`config.py`) жарияламаңыз — токенді орнатуды көрсетіңіз:
```powershell
$env:ACCOUNTING_BOT_TOKEN = "мұнда"
