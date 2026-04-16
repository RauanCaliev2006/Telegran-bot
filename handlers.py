from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states import TransactionStates
from database import DB_NAME
import aiosqlite
import datetime

router = Router()

# Кнопки выбора типа
type_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Доход"), KeyboardButton(text="Расход")]],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Главное меню с кнопками
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="\U0001f4c8 Доход"), KeyboardButton(text="\U0001f4c9 Расход")],
        [KeyboardButton(text="\U0001f4cb История"), KeyboardButton(text="\U0001f4b0 Баланс")],
        [KeyboardButton(text="\u274c Отменить транзакцию"), KeyboardButton(text="\U0001f5d1 Удалить всё")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# /start
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я твой бот для учёта доходов и расходов.\n"
        "Выбери действие:",
        reply_markup=main_keyboard
    )

router.message.register(start_handler, Command(commands=["start"]))

# Ввод категории
async def process_category(message: Message, state: FSMContext):
    # ...existing code...
    await state.update_data(category=message.text)
    await message.answer("Теперь укажи сумму транзакции (только цифры):")
    await state.set_state(TransactionStates.amount)

router.message.register(process_category, TransactionStates.category)

# Ввод суммы
async def process_amount(message: Message, state: FSMContext):
    # ...existing code...
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введи корректную сумму (только цифры).")
        return

    await state.update_data(amount=amount)
    await message.answer("Отлично! Теперь введи дату транзакции в формате ДД.ММ.ГГГГ (например 08.04.2026):")
    await state.set_state(TransactionStates.date)

router.message.register(process_amount, TransactionStates.amount)

# Ввод даты
async def process_date(message: Message, state: FSMContext):
    # ...existing code...
    try:
        date = datetime.datetime.strptime(message.text, "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат! Введи дату в формате ДД.MM.YYYY (например 08.04.2026).")
        return

    await state.update_data(date=str(date))

    # Сохраняем в SQLite
    data = await state.get_data()
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO transactions (type, category, amount, date) VALUES (?, ?, ?, ?)",
                (data['type'], data['category'], data['amount'], data['date'])
            )
            await db.commit()
        # saved to db
    except Exception as e:
        await message.answer("Ошибка при сохранении транзакции. Попробуйте позже.")
        return

    # Сбрасываем данные для следующей транзакции и переводим FSM в состояние выбора типа
    # В aiogram v3 нет reset_data(); используем set_data({}) чтобы очистить сохранённые данные.
    await state.set_data({})

    # Отправляем единое сообщение: информация о сохранении + клавиатура для выбора типа.
    # Это гарантирует, что клавиатура будет видна пользователю вместе с уведомлением о сохранении.
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

# /history — список транзакций
async def cmd_history(message: Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, type, category, amount, date FROM transactions ORDER BY id DESC LIMIT 20")
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

# /balance — итоговый баланс
async def cmd_balance(message: Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT type, SUM(amount) FROM transactions GROUP BY type"
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
        f"Итого: {balance}"
    )

router.message.register(cmd_balance, Command(commands=["balance"]))

# /delete — удалить все транзакции
async def cmd_delete_all(message: Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM transactions")
        await db.commit()
    await message.answer("Все транзакции удалены.")

router.message.register(cmd_delete_all, Command(commands=["delete"]))

# /cancel — отмена конкретной транзакции по ID
async def cmd_cancel(message: Message, state: FSMContext):
    # Показываем последние транзакции чтобы пользователь выбрал ID
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, type, category, amount, date FROM transactions ORDER BY id DESC LIMIT 10")
        rows = await cursor.fetchall()

    if not rows:
        await message.answer("Транзакций нет, нечего отменять.")
        return

    lines = ["Какую транзакцию отменить? Введи номер (ID):\n"]
    for row in rows:
        tid, ttype, cat, amount, date = row
        emoji = "\U0001f4c8" if ttype == "Доход" else "\U0001f4c9"
        lines.append(f"{emoji} #{tid} | {ttype} | {cat} | {amount} | {date}")

    await message.answer("\n".join(lines))
    await state.set_state(TransactionStates.cancel_id)

router.message.register(cmd_cancel, Command(commands=["cancel"]))

# Ввод ID для отмены транзакции
async def process_cancel_id(message: Message, state: FSMContext):
    try:
        tid = int(message.text.strip().replace("#", ""))
    except ValueError:
        await message.answer("Введи корректный номер транзакции (только цифры).")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, type, category, amount, date FROM transactions WHERE id = ?", (tid,))
        row = await cursor.fetchone()

        if not row:
            await message.answer(f"Транзакция #{tid} не найдена. Попробуй ещё раз или /start для нового ввода.")
            return

        await db.execute("DELETE FROM transactions WHERE id = ?", (tid,))
        await db.commit()

    _, ttype, cat, amount, date = row
    await state.clear()
    await message.answer(
        f"Транзакция отменена:\n"
        f"#{tid} | {ttype} | {cat} | {amount} | {date}\n\n"
        f"Выбери действие:",
        reply_markup=main_keyboard
    )
    await state.set_state(TransactionStates.type)

router.message.register(process_cancel_id, TransactionStates.cancel_id)

# Обработка нажатий кнопок главного меню (регистрируется последним — ловит всё что не поймали FSM-хэндлеры)
async def menu_handler(message: Message, state: FSMContext):
    text = message.text
    if text in ["\U0001f4c8 Доход", "\U0001f4c9 Расход", "Доход", "Расход"]:
        ttype = "Доход" if "Доход" in text else "Расход"
        await state.update_data(type=ttype)
        await message.answer("Отлично! Теперь укажи категорию транзакции:")
        await state.set_state(TransactionStates.category)
    elif text == "\U0001f4cb История":
        await cmd_history(message, state)
    elif text == "\U0001f4b0 Баланс":
        await cmd_balance(message, state)
    elif text == "\u274c Отменить транзакцию":
        await cmd_cancel(message, state)
    elif text == "\U0001f5d1 Удалить всё":
        await cmd_delete_all(message, state)
    else:
        await message.answer("Выбери действие из меню:", reply_markup=main_keyboard)

router.message.register(menu_handler)