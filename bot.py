import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import os

from database import (
    add_plant, get_all_plants, get_plant_by_id,
    update_last_watered, update_last_washed, delete_plant,
    add_user
)
from ai_helper import get_advice
from keyboards import main_menu

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ====================== НАЛАШТУВАННЯ ======================
ALLOWED_USERS_STR = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS = [int(x.strip()) for x in ALLOWED_USERS_STR.split(",") if x.strip().isdigit()]


def is_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS


# ====================== СТАРТ ======================
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_allowed(message.from_user.id):
        await message.answer("❌ Ви не маєте доступу до цього бота.")
        return

    add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    await message.answer(
        "🌿 Бот готовий!\nРослини спільні для двох користувачів.",
        reply_markup=main_menu()
    )


# ====================== ДОДАВАННЯ РОСЛИНИ ======================
@dp.message(F.text == "➕ Додати рослину")
async def add_plant_start(message: types.Message):
    if not is_allowed(message.from_user.id): return
    await message.answer(
        "Напиши:\n<b>Назва інтервал_поливу інтервал_нижнього</b>\n\n"
        "Приклад: Фікус 7 14",
        parse_mode="HTML"
    )


@dp.message(F.text.regexp(r'^(.+?)\s+(\d+)\s+(\d+)$'))
async def process_add_plant(message: types.Message):
    if not is_allowed(message.from_user.id): return
    try:
        parts = message.text.strip().split()
        name = " ".join(parts[:-2])
        watering = int(parts[-2])
        bottom = int(parts[-1])

        add_plant(name, watering, bottom)
        await message.answer(f"✅ Рослина «{name}» додана!", reply_markup=main_menu())
    except:
        await message.answer("❌ Неправильний формат. Приклад: Фікус 7 14")


# ====================== СПІЛЬНІ РОСЛИНИ ======================
@dp.message(F.text == "🌱 Мої рослини")
async def my_plants(message: types.Message):
    if not is_allowed(message.from_user.id): return

    plants = get_all_plants()
    if not plants:
        await message.answer("Поки немає рослин.")
        return

    text = "🌿 <b>Спільні рослини:</b>\n\n"
    for p in plants:
        last = p[5][:10] if p[5] else "—"
        text += f"• <b>{p[1]}</b> — полив кожні {p[2]} днів (останній: {last})\n"
    await message.answer(text, parse_mode="HTML")


# ====================== КНОПКИ ДІЙ ======================
@dp.message(F.text == "💧 Полив")
async def water_start(message: types.Message):
    if not is_allowed(message.from_user.id): return
    plants = get_all_plants()
    if not plants:
        await message.answer("Немає рослин.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💧 {p[1]}", callback_data=f"water_{p[0]}")] for p in plants
    ])
    await message.answer("Яку рослину поливаємо?", reply_markup=kb)


@dp.message(F.text == "🧼 Помити листя")
async def wash_start(message: types.Message):
    if not is_allowed(message.from_user.id): return
    plants = get_all_plants()
    if not plants:
        await message.answer("Немає рослин.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🧼 {p[1]}", callback_data=f"wash_{p[0]}")] for p in plants
    ])
    await message.answer("Яке листя миємо?", reply_markup=kb)


@dp.message(F.text == "🤖 Порада від AI")
async def advice_start(message: types.Message):
    if not is_allowed(message.from_user.id): return
    plants = get_all_plants()
    if not plants:
        await message.answer("Немає рослин.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🤖 {p[1]}", callback_data=f"advice_{p[0]}")] for p in plants
    ])
    await message.answer("По якій рослині дати пораду?", reply_markup=kb)


@dp.message(F.text == "🗑 Видалити рослину")
async def delete_start(message: types.Message):
    if not is_allowed(message.from_user.id): return
    plants = get_all_plants()
    if not plants:
        await message.answer("Немає рослин.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🗑 {p[1]}", callback_data=f"delete_{p[0]}")] for p in plants
    ])
    await message.answer("Яку рослину видалити? (незворотньо)", reply_markup=kb)


# ====================== CALLBACK ОБРОБНИКИ ======================
@dp.callback_query(F.data.startswith("water_"))
async def callback_water(callback: types.CallbackQuery):
    if not is_allowed(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    plant_id = int(callback.data.split("_")[1])
    plant = get_plant_by_id(plant_id)
    if not plant: return

    update_last_watered(plant_id)
    username = callback.from_user.username or callback.from_user.first_name

    await callback.message.edit_text(f"✅ Полито!\n💧 <b>{plant[1]}</b>")

    # Сповіщення іншому користувачу
    for uid in ALLOWED_USERS:
        if uid != callback.from_user.id:
            try:
                await bot.send_message(uid, f"💧 @{username} полив(ла) **{plant[1]}**")
            except:
                pass
    await callback.answer("Записано")


@dp.callback_query(F.data.startswith("wash_"))
async def callback_wash(callback: types.CallbackQuery):
    if not is_allowed(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    plant_id = int(callback.data.split("_")[1])
    plant = get_plant_by_id(plant_id)
    if not plant: return

    update_last_washed(plant_id)
    username = callback.from_user.username or callback.from_user.first_name

    await callback.message.edit_text(f"✅ Листя помито!\n🧼 <b>{plant[1]}</b>")

    for uid in ALLOWED_USERS:
        if uid != callback.from_user.id:
            try:
                await bot.send_message(uid, f"🧼 @{username} помив(ла) листя у **{plant[1]}**")
            except:
                pass
    await callback.answer("Записано")


@dp.callback_query(F.data.startswith("advice_"))
async def callback_advice(callback: types.CallbackQuery):
    if not is_allowed(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    plant_id = int(callback.data.split("_")[1])
    plant = get_plant_by_id(plant_id)
    if not plant: return

    await callback.message.edit_text(f"🤖 Генерую пораду для «{plant[1]}»...")

    advice_text = await get_advice(plant)

    await callback.message.edit_text(
        f"🌱 <b>{plant[1]}</b>\n\n{advice_text}",
        parse_mode="HTML"
    )
    await callback.answer("Готово")


@dp.callback_query(F.data.startswith("delete_"))
async def callback_delete(callback: types.CallbackQuery):
    if not is_allowed(callback.from_user.id):
        await callback.answer("Доступ заборонено", show_alert=True)
        return
    plant_id = int(callback.data.split("_")[1])
    plant = get_plant_by_id(plant_id)
    if not plant: return

    name = plant[1]
    delete_plant(plant_id)

    await callback.message.edit_text(f"🗑 Рослину «{name}» видалено.")
    await callback.answer("Видалено", show_alert=True)


# ====================== ЗАПУСК ======================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🌱 Бот запущений...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())