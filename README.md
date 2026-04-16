Telegram Бот — Кіріс/Шығыс Есебі
Telegram бот арқылы кіріс пен шығысты жазып, қаржыңды бақылайсың.

Мүмкіндіктері
 Кіріс және  Шығыс жазу
 Тарих — соңғы транзакцияларды көру
 Баланс — жалпы қалдықты есептеу
 Транзакцияны болдырмау
 Барлығын жою
Технологиялар
Python 3.13
aiogram v3
SQLite (aiosqlite)
Орнату
git clone https://github.com/RauanCaliev2006/Telegran-bot.git
cd Telegran-bot
pip install aiogram aiosqlite
config.py файлын жасап, токенді қос:

TOKEN = "ТОКЕН"
Іске қосу
python main.py
