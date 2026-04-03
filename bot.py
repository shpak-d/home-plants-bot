import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram import Router
from dotenv import load_dotenv
import os

from database import add_plant, get_user_plants, log_action, update_last_watered, update_last_washed
from ai_helper import get_advice
from keyboards import main_menu

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =================== КОМАНДИ ===================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌿 Привіт! Я бот-помічник для ваших кімнатних рослин.\n\n"
        "Використовуй кнопки або команди:\n"
        "/add_plant — додати нову рослину",
        reply_markup=main_menu()
    )


@dp.message(Command("add_plant"))
async def cmd_add_plant(message: types.Message):
    await message.answer(
        "Напиши дані про рослину в форматі:\n"
        "Назва інтервал_днів нижній_полив\n\n"
        "Приклад:\n"
        "Фікус 7 так\n"
        "Монстера 10 ні"
    )


@dp.message(F.text.regexp(r'^(.+) (\d+) (так|ні)$'))
async def process_add_plant(message: types.Message):
    try:
        parts = message.text.split()
        name = parts[0]
        days = int(parts[1])
        is_bottom = parts[2].lower() == "так"

        plant_id = add_plant(message.from_user.id, name, days, is_bottom)

        await message.answer(
            f"✅ Рослина «{name}» успішно додана!\n"
            f"Полив кожні {days} днів. "
            f"Тип: {'нижній полив' if is_bottom else 'звичайний'}"
        )
    except:
        await message.answer("Неправильний формат. Спробуй ще раз.")


@dp.message(F.text == "🌱 Мої рослини")
async def my_plants(message: types.Message):
    plants = get_user_plants(message.from_user.id)
    if not plants:
        await message.answer("У тебе поки немає рослин.")
        return

    text = "🌿 Твої рослини:\n\n"
    for p in plants:
        bottom = " (нижній полив)" if p[4] else ""
        text += f"• {p[2]} — полив кожні {p[3]} днів{bottom}\n"
    await message.answer(text)


@dp.message(F.text == "🤖 Порада від AI")
async def advice(message: types.Message):
    plants = get_user_plants(message.from_user.id)
    if not plants:
        await message.answer("Спочатку додай хоча б одну рослину.")
        return

    await message.answer("Думаю пораду...")

    for plant in plants:
        advice_text = await get_advice(plant)
        await message.answer(f"🌱 <b>{plant[2]}</b>\n\n{advice_text}", parse_mode="HTML")


@dp.message(F.text.in_({"💧 Полив", "/water"}))
async def water_command(message: types.Message):
    plants = get_user_plants(message.from_user.id)
    if not plants:
        await message.answer("У тебе немає рослин.")
        return

    # Для простоти — просимо назву
    await message.answer("Напиши назву рослини, яку полив:")


@dp.message()
async def handle_watering(message: types.Message):
    # Простий пошук по назві (можна покращити пізніше)
    plants = get_user_plants(message.from_user.id)
    for plant in plants:
        if plant[2].lower() in message.text.lower():
            update_last_watered(plant[0])
            log_action(plant[0], "полив", message.from_user.id, message.from_user.username or "unknown")

            action = "нижнім способом" if plant[4] else "звичайним способом"

            await message.answer(f"✅ Записано: ти полив «{plant[2]}» {action}")


    await message.answer("Не знайшов такої рослини. Спробуй ще раз.")


# =================== ЗАПУСК ===================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущений...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())