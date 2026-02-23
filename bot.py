import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8017987877:AAHAAg2baXiSqoSPLv2qOb5-uzZp8X1hkrU"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ---------------- БАЗА ----------------

conn = sqlite3.connect("ads.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    photo TEXT,
    name TEXT,
    price TEXT,
    description TEXT,
    city TEXT,
    contact TEXT
)
""")
conn.commit()

# ---------------- СТАНИ ----------------

class SellState(StatesGroup):
    photo = State()
    name = State()
    price = State()
    description = State()
    city = State()
    contact = State()

class BuyState(StatesGroup):
    search = State()

# ---------------- КНОПКИ ----------------

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Купити")],
        [KeyboardButton(text="💰 Продати")],
        [KeyboardButton(text="❌ Скасувати")]
    ],
    resize_keyboard=True
)

# ---------------- СКАСУВАННЯ ----------------

@dp.message(F.text == "❌ Скасувати")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Дію скасовано.", reply_markup=main_keyboard)

# ---------------- START ----------------

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привіт 👋 Це вело-барахолка.\nОбери дію:",
        reply_markup=main_keyboard
    )

# ---------------- ПРОДАЖ ----------------

@dp.message(F.text == "💰 Продати")
async def sell_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(SellState.photo)
    await message.answer("📸 Надішли фото товару:")

@dp.message(SellState.photo, F.photo)
async def get_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(SellState.name)
    await message.answer("Введи назву товару:")

@dp.message(SellState.photo)
async def no_photo(message: Message):
    await message.answer("❗ Надішли саме фото.")

@dp.message(SellState.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(SellState.price)
    await message.answer("Введи ціну:")

@dp.message(SellState.price)
async def get_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(SellState.description)
    await message.answer("Введи опис товару:")

@dp.message(SellState.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(SellState.city)
    await message.answer("Вкажи місто:")

@dp.message(SellState.city)
async def get_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(SellState.contact)
    await message.answer("Вкажи контакт (телефон або @username):")

@dp.message(SellState.contact)
async def get_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()

    cursor.execute("""
        INSERT INTO ads (photo, name, price, description, city, contact)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["photo"],
        data["name"],
        data["price"],
        data["description"],
        data["city"],
        data["contact"]
    ))
    conn.commit()

    await message.answer_photo(
        photo=data["photo"],
        caption=(
            f"📦 Оголошення створено:\n\n"
            f"Назва: {data['name']}\n"
            f"Ціна: {data['price']}\n"
            f"Опис: {data['description']}\n"
            f"Місто: {data['city']}\n"
            f"Контакт: {data['contact']}"
        ),
        reply_markup=main_keyboard
    )

    await state.clear()

# ---------------- ПОШУК ----------------

@dp.message(F.text == "🛒 Купити")
async def buy_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BuyState.search)
    await message.answer("🔎 Напиши що шукаєш:")

@dp.message(BuyState.search)
async def process_search(message: Message, state: FSMContext):
    query = message.text.lower()

    cursor.execute("""
        SELECT photo, name, price, description, city, contact 
        FROM ads 
        WHERE LOWER(name) LIKE ?
    """, (f"%{query}%",))
    results = cursor.fetchall()

    if not results:
        await message.answer("❌ Нічого не знайдено.", reply_markup=main_keyboard)
    else:
        for ad in results:
            await message.answer_photo(
                photo=ad[0],
                caption=(
                    f"📦 Знайдено:\n\n"
                    f"Назва: {ad[1]}\n"
                    f"Ціна: {ad[2]}\n"
                    f"Опис: {ad[3]}\n"
                    f"Місто: {ad[4]}\n"
                    f"Контакт: {ad[5]}"
                )
            )

    await state.clear()

# ---------------- ЗАПУСК ----------------

@dp.message()
async def debug(message: Message):
    print(message.chat.id)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())