import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove
from dotenv import load_dotenv
import os

from database import add_plant, get_user_plants, log_action, update_last_watered, update_last_washed, delete_plant, get_plant_by_id
from ai_helper import get_advice
from keyboards import main_menu

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# =================== СТАРТ ===================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌿 Привіт! Я твій помічник по кімнатних рослинах.",
        reply_markup=main_menu()
    )

# =================== ДОДАВАННЯ РОСЛИНИ ===================
@dp.message(F.text == "➕ Додати рослину")
async def add_plant_start(message: types.Message):
    await message.answer(
        "Напиши дані про рослину в форматі:\n"
        "<b>Назва інтервал_поливу інтервал_нижнього_поливу</b>\n\n"
        "Приклад:\n"
        "Фікус 7 14\n"
        "Монстера 10 30\n\n"
        "Де:\n"
        "• Перше число — звичайний полив (днів)\n"
        "• Друге число — нижній полив (днів)",
        parse_mode="HTML"
    )

@dp.message(F.text.regexp(r'^(.+?)\s+(\d+)\s+(\d+)$'))
async def process_add_plant(message: types.Message):
    try:
        match = message.text.strip().split()
        name = " ".join(match[:-2])          # назва може бути з пробілами
        watering = int(match[-2])
        bottom = int(match[-1])

        plant_id = add_plant(message.from_user.id, name, watering, bottom)

        await message.answer(
            f"✅ Рослина <b>«{name}»</b> додана!\n\n"
            f"Полив: кожні {watering} днів\n"
            f"Нижній полив: кожні {bottom} днів",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
    except Exception as e:
        await message.answer("❌ Неправильний формат. Спробуй ще раз.")

# =================== ВИДАЛЕННЯ РОСЛИНИ ===================
@dp.message(F.text == "🗑 Видалити рослину")
async def delete_plant_start(message: types.Message):
    plants = get_user_plants(message.from_user.id)
    if not plants:
        await message.answer("У тебе немає рослин для видалення.")
        return

    text = "Яку рослину хочеш видалити?\n\n"
    for p in plants:
        text += f"• {p[2]} (ID: {p[0]})\n"

    await message.answer(text + "\nНапиши ID рослини для видалення:")

@dp.message(F.text.regexp(r'^\d+$'))
async def process_delete_plant(message: types.Message):
    plant_id = int(message.text)
    plant = get_plant_by_id(plant_id)

    if not plant or plant[1] != message.from_user.id:
        await message.answer("❌ Рослину не знайдено або це не твоя рослина.")
        return

    delete_plant(plant_id)
    await message.answer(f"🗑 Рослину «{plant[2]}» успішно видалено.", reply_markup=main_menu())

# =================== ПОРАДА ВІД AI ===================
@dp.message(F.text == "🤖 Порада від AI")
async def advice_start(message: types.Message):
    plants = get_user_plants(message.from_user.id)
    if not plants:
        await message.answer("Спочатку додай хоча б одну рослину.")
        return

    # Поки що просто виводимо список і просимо вибрати
    text = "По якій рослині дати пораду?\n\n"
    for p in plants:
        text += f"• {p[2]} (ID: {p[0]})\n"

    await message.answer(text + "\nНапиши ID рослини:")

# (Поки що проста версія — пізніше зробимо красиві inline-кнопки)

# =================== ЗАПУСК ===================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🌱 Бот запущений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())