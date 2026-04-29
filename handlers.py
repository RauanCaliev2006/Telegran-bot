from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states import TransactionStates
from database import DB_NAME
import aiosqlite
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

router = Router()

type_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Доход"), KeyboardButton(text="Расход")]],
    resize_keyboard=True,
    one_time_keyboard=False
)

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="\U0001f4c8 Доход"), KeyboardButton(text="\U0001f4c9 Расход")],
        [KeyboardButton(text="\U0001f4cb История"), KeyboardButton(text="\U0001f4b0 Баланс")],
        [KeyboardButton(text="\U0001f4c5 Отчёт по датам"), KeyboardButton(text="\u274c Отменить")],
        [KeyboardButton(text="\U0001f5d1 Удалить запись"), KeyboardButton(text="\U0001f6ab Удалить всё")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я твой бот для учёта доходов и расходов.\n"
        "Выбери действие:",
        reply_markup=main_keyboard
    )

router.message.register(start_handler, Command(commands=["start"]))

CANCEL_TEXT = "\u274c Отменить"
OTHER_TEXT = "\u270f\ufe0f Другое"

# Кнопки категорий для дохода
income_category_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="\U0001f4b5 Зарплата"), KeyboardButton(text="\U0001f3c6 Премия")],
        [KeyboardButton(text="\U0001f4c8 Инвестиции"), KeyboardButton(text="\U0001f381 Подарок")],
        [KeyboardButton(text="\U0001f4b0 Подработка"), KeyboardButton(text=OTHER_TEXT)],
        [KeyboardButton(text=CANCEL_TEXT)]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Кнопки категорий для расхода
expense_category_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="\U0001f6d2 Продукты"), KeyboardButton(text="\U0001f3e0 Жильё")],
        [KeyboardButton(text="\U0001f697 Транспорт"), KeyboardButton(text="\U0001f3ae Развлечения")],
        [KeyboardButton(text="\U0001f48a Здоровье"), KeyboardButton(text="\U0001f393 Образование")],
        [KeyboardButton(text="\U0001f455 Одежда"), KeyboardButton(text=OTHER_TEXT)],
        [KeyboardButton(text=CANCEL_TEXT)]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

async def do_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Операция отменена. Выбери действие:", reply_markup=main_keyboard)

async def process_category(message: Message, state: FSMContext):
    if message.text == CANCEL_TEXT:
        return await do_cancel(message, state)
    if message.text == OTHER_TEXT:
        await message.answer("Введи название категории:")
        await state.set_state(TransactionStates.custom_category)
        return
    # Убираем эмодзи из названия кнопки, оставляем только текст
    category = message.text.split(" ", 1)[-1] if " " in message.text else message.text
    await state.update_data(category=category)
    await message.answer("Теперь укажи сумму транзакции (только цифры):")
    await state.set_state(TransactionStates.amount)

router.message.register(process_category, TransactionStates.category)

# Ручной ввод категории (когда выбрали "Другое")
async def process_custom_category(message: Message, state: FSMContext):
    if message.text == CANCEL_TEXT:
        return await do_cancel(message, state)
    await state.update_data(category=message.text)
    await message.answer("Теперь укажи сумму транзакции (только цифры):")
    await state.set_state(TransactionStates.amount)

router.message.register(process_custom_category, TransactionStates.custom_category)

async def process_amount(message: Message, state: FSMContext):
    if message.text == CANCEL_TEXT:
        return await do_cancel(message, state)
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введи корректную сумму (только цифры).")
        return

    await state.update_data(amount=amount)
    await message.answer("Отлично! Теперь введи дату транзакции в формате ДД.ММ.ГГГГ (например 08.04.2026):")
    await state.set_state(TransactionStates.date)

router.message.register(process_amount, TransactionStates.amount)

async def process_date(message: Message, state: FSMContext):
    if message.text == CANCEL_TEXT:
        return await do_cancel(message, state)
    # ...existing code...
    try:
        date = datetime.datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат! Введи дату в формате ДД.MM.YYYY (например 08.04.2026).")
        return

    await state.update_data(date=str(date))

    data = await state.get_data()
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)",
                (message.from_user.id, data['type'], data['category'], data['amount'], data['date'])
            )
            await db.commit()
    except Exception as e:
        await message.answer("Ошибка при сохранении транзакции. Попробуйте позже.")
        return

    await state.set_data({})
    await state.set_state(TransactionStates.type)

    await message.answer(
        f"Транзакция сохранена!\n"
        f"Тип: {data['type']}\n"
        f"Категория: {data['category']}\n"
        f"Сумма: {data['amount']}\n"
        f"Дата: {data['date']}\n\n"
        f"Хочешь добавить ещё одну транзакцию? Выбери действие:",
        reply_markup=main_keyboard
    )

router.message.register(process_date, TransactionStates.date)

async def cmd_history(message: Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, type, category, amount, date FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT 10", (message.from_user.id,))
        rows = await cursor.fetchall()

    if not rows:
        await message.answer("Транзакций пока нет.")
        return

    lines = ["Последние транзакции:\n"]
    for row in rows:
        tid, ttype, cat, amount, date = row
        emoji = "\U0001f4c8" if ttype == "Доход" else "\U0001f4c9"
        lines.append(f"{emoji} #{tid} | {ttype} | {cat} | {amount} | {date}")

    await message.answer("\n".join(lines))

router.message.register(cmd_history, Command(commands=["history"]))

# Клавиатура после баланса
balance_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="\U0001f4ca Показать график")],
        [KeyboardButton(text=CANCEL_TEXT)]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

async def cmd_balance(message: Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT type, SUM(amount) FROM transactions WHERE user_id = ? GROUP BY type", (message.from_user.id,)
        )
        rows = await cursor.fetchall()

    income = 0.0
    expense = 0.0
    for ttype, total in rows:
        if ttype == "Доход":
            income = total or 0.0
        else:
            expense = total or 0.0

    balance = income - expense
    await message.answer(
        f"\U0001f4b0 Баланс:\n"
        f"\U0001f4c8 Доходы: {income}\n"
        f"\U0001f4c9 Расходы: {expense}\n"
        f"\U00002014\U00002014\U00002014\U00002014\U00002014\n"
        f"Итого: {balance}\n\n"
        f"Хочешь увидеть график?",
        reply_markup=balance_keyboard
    )

router.message.register(cmd_balance, Command(commands=["balance"]))

# Генерация круговой диаграммы
async def cmd_chart(message: Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        # Данные по типам
        cursor = await db.execute(
            "SELECT type, SUM(amount) FROM transactions WHERE user_id = ? GROUP BY type", (message.from_user.id,)
        )
        type_rows = await cursor.fetchall()

        # Данные по категориям расходов
        cursor2 = await db.execute(
            "SELECT category, SUM(amount) FROM transactions WHERE type='Расход' AND user_id = ? GROUP BY category", (message.from_user.id,)
        )
        expense_rows = await cursor2.fetchall()

        # Данные по категориям доходов
        cursor3 = await db.execute(
            "SELECT category, SUM(amount) FROM transactions WHERE type='Доход' AND user_id = ? GROUP BY category", (message.from_user.id,)
        )
        income_rows = await cursor3.fetchall()

    if not type_rows:
        await message.answer("Транзакций нет, график невозможен.", reply_markup=main_keyboard)
        return

    # Собираем все категории в одну диаграмму
    labels = []
    values = []
    colors = []
    color_income = ['#00d2ff', '#00b4d8', '#0096c7', '#0077b6', '#023e8a']
    color_expense = ['#ff6b6b', '#ee5a24', '#f0932b', '#e056fd', '#be2edd', '#6c5ce7', '#fd79a8']

    for i, row in enumerate(income_rows):
        labels.append(f"{row[0]} (доход)")
        values.append(row[1])
        colors.append(color_income[i % len(color_income)])

    for i, row in enumerate(expense_rows):
        labels.append(f"{row[0]} (расход)")
        values.append(row[1])
        colors.append(color_expense[i % len(color_expense)])

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')

    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct='%1.1f%%', colors=colors,
        textprops={'color': 'white', 'fontsize': 11},
        pctdistance=0.8, labeldistance=1.15
    )
    for t in autotexts:
        t.set_fontsize(10)

    ax.set_title('Доходы и расходы по категориям', color='white', fontsize=16, fontweight='bold', pad=20)

    plt.tight_layout()
    chart_path = 'chart.png'
    plt.savefig(chart_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)

    photo = FSInputFile(chart_path)
    await message.answer_photo(photo, caption="\U0001f4ca График доходов и расходов по категориям", reply_markup=main_keyboard)

    os.remove(chart_path)

router.message.register(cmd_chart, Command(commands=["chart"]))

async def cmd_report(message: Message, state: FSMContext):
    await message.answer("Введи начальную дату (ДД.ММ.ГГГГ):")
    await state.set_state(TransactionStates.report_from)

router.message.register(cmd_report, Command(commands=["report"]))

async def process_report_from(message: Message, state: FSMContext):
    if message.text == CANCEL_TEXT:
        return await do_cancel(message, state)
    try:
        date_from = datetime.datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат! Введи дату в формате ДД.ММ.ГГГГ (например 01.01.2026):")
        return
    await state.update_data(report_from=str(date_from))
    await message.answer("Теперь введи конечную дату (ДД.ММ.ГГГГ):")
    await state.set_state(TransactionStates.report_to)

router.message.register(process_report_from, TransactionStates.report_from)

async def process_report_to(message: Message, state: FSMContext):
    if message.text == CANCEL_TEXT:
        return await do_cancel(message, state)
    try:
        date_to = datetime.datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат! Введи дату в формате ДД.ММ.ГГГГ (например 30.04.2026):")
        return

    data = await state.get_data()
    date_from = data["report_from"]
    date_to_str = str(date_to)
    uid = message.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, type, category, amount, date FROM transactions WHERE user_id = ? AND date >= ? AND date <= ? ORDER BY date",
            (uid, date_from, date_to_str)
        )
        rows = await cursor.fetchall()

        cursor2 = await db.execute(
            "SELECT type, SUM(amount) FROM transactions WHERE user_id = ? AND date >= ? AND date <= ? GROUP BY type",
            (uid, date_from, date_to_str)
        )
        totals = await cursor2.fetchall()

    await state.clear()

    if not rows:
        await message.answer(
            f"За период {date_from} — {date_to_str} транзакций нет.",
            reply_markup=main_keyboard
        )
        return

    income = 0.0
    expense = 0.0
    for ttype, total in totals:
        if ttype == "Доход":
            income = total or 0.0
        else:
            expense = total or 0.0

    lines = [f"\U0001f4c5 Отчёт: {date_from} — {date_to_str}\n"]
    for row in rows:
        tid, ttype, cat, amount, date = row
        emoji = "\U0001f4c8" if ttype == "Доход" else "\U0001f4c9"
        lines.append(f"{emoji} #{tid} | {ttype} | {cat} | {amount} | {date}")

    lines.append(f"\n\U0001f4c8 Доходы: {income}")
    lines.append(f"\U0001f4c9 Расходы: {expense}")
    lines.append(f"\U0001f4b0 Итого: {income - expense}")

    await message.answer("\n".join(lines), reply_markup=main_keyboard)

router.message.register(process_report_to, TransactionStates.report_to)

async def cmd_delete_all(message: Message, state: FSMContext):
    uid = message.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM transactions WHERE user_id = ?", (uid,))
        await db.commit()
    await state.clear()
    await message.answer("Все транзакции удалены!", reply_markup=main_keyboard)

router.message.register(cmd_delete_all, Command(commands=["deleteall"]))

async def cmd_cancel(message: Message, state: FSMContext):
    await message.answer("Введи ID транзакции для удаления (можно посмотреть в истории):")
    await state.set_state(TransactionStates.cancel_id)

router.message.register(cmd_cancel, Command(commands=["cancel"]))

async def process_cancel_id(message: Message, state: FSMContext):
    if message.text == CANCEL_TEXT:
        return await do_cancel(message, state)
    try:
        tid = int(message.text)
    except ValueError:
        await message.answer("Введи корректный ID (число).")
        return

    uid = message.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id, type, category, amount, date FROM transactions WHERE id = ? AND user_id = ?", (tid, uid)
        )
        row = await cursor.fetchone()
        if not row:
            await message.answer("Транзакция не найдена или не принадлежит тебе.")
            await state.clear()
            return
        await db.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tid, uid))
        await db.commit()

    await state.clear()
    await message.answer(
        f"Транзакция #{row[0]} удалена!\n"
        f"({row[1]} | {row[2]} | {row[3]} | {row[4]})",
        reply_markup=main_keyboard
    )

router.message.register(process_cancel_id, TransactionStates.cancel_id)

async def menu_handler(message: Message, state: FSMContext):
    text = message.text
    if text in ["\U0001f4c8 Доход", "\U0001f4c9 Расход", "Доход", "Расход"]:
        ttype = "Доход" if "Доход" in text else "Расход"
        await state.update_data(type=ttype)
        kb = income_category_keyboard if ttype == "Доход" else expense_category_keyboard
        await message.answer("Выбери категорию:", reply_markup=kb)
        await state.set_state(TransactionStates.category)
    elif text == "\U0001f4cb История":
        await cmd_history(message, state)
    elif text == "\U0001f4b0 Баланс":
        await cmd_balance(message, state)
    elif text == "\U0001f4ca Показать график":
        await cmd_chart(message, state)
    elif text == "\U0001f4c5 Отчёт по датам":
        await cmd_report(message, state)
    elif text == CANCEL_TEXT:
        await do_cancel(message, state)
    elif text == "\U0001f5d1 Удалить запись":
        await cmd_cancel(message, state)
    elif text == "\U0001f6ab Удалить всё":
        await cmd_delete_all(message, state)
    else:
        await message.answer("Выбери действие из меню:", reply_markup=main_keyboard)

router.message.register(menu_handler)