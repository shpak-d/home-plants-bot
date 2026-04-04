import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton   # ← додав тут

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
        # Розбиваємо текст правильно
        parts = message.text.strip().split()
        if len(parts) < 3:
            raise ValueError("Недостатньо даних")

        # Назва може складатися з кількох слів, останні два — числа
        watering = int(parts[-2])
        bottom = int(parts[-1])
        name = " ".join(parts[:-2])   # все, що перед двома числами — назва рослини

        if watering <= 0 or bottom <= 0:
            await message.answer("Інтервали повинні бути більшими за 0.")
            return

        plant_id = add_plant(message.from_user.id, name, watering, bottom)

        await message.answer(
            f"✅ Рослина <b>«{name}»</b> успішно додана!\n\n"
            f"Звичайний полив: кожні {watering} днів\n"
            f"Нижній полив: кожні {bottom} днів",
            parse_mode="HTML",
            reply_markup=main_menu()
        )
    except Exception:
        await message.answer(
            "❌ Неправильний формат!\n\n"
            "Правильний приклад:\n"
            "<b>Фікус 7 14</b>\n"
            "<b>Монстера 10 21</b>\n"
            "<b>Сансевієрія 14 30</b>\n\n"
            "Назва + два числа через пробіл",
            parse_mode="HTML"
        )


@dp.message(F.text == "🌱 Мої рослини")
async def my_plants(message: types.Message):
    plants = get_user_plants(message.from_user.id)

    if not plants:
        await message.answer("У тебе поки немає доданих рослин.")
        return

    text = "🌿 <b>Твої рослини:</b>\n\n"
    for p in plants:
        bottom_text = f", нижній полив кожні {p[4]} днів" if p[4] else ""
        text += f"• <b>{p[2]}</b> — полив кожні {p[3]} днів{bottom_text}\n"

    await message.answer(text, parse_mode="HTML")


# =================== ВИДАЛЕННЯ (залишаємо текстове, бо небезпечно) ===================
@dp.message(F.text == "🗑 Видалити рослину")
async def delete_plant_start(message: types.Message):
    plants = get_user_plants(message.from_user.id)
    if not plants:
        await message.answer("У тебе немає рослин.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for plant in plants:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🗑 {plant[2]}",
                callback_data=f"delete_{plant[0]}"
            )
        ])

    await message.answer("Яку рослину видалити? (ця дія незворотна)", reply_markup=kb)

# =================== ПОРАДА ВІД AI ===================
@dp.message(F.text == "🤖 Порада від AI")
async def advice_start(message: types.Message):
    plants = get_user_plants(message.from_user.id)
    if not plants:
        await message.answer("Спочатку додай рослину.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for plant in plants:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🤖 {plant[2]}",
                callback_data=f"advice_{plant[0]}"
            )
        ])

    await message.answer("По якій рослині дати пораду?", reply_markup=kb)

# =================== ПОМИТИ ЛИСТЯ ===================
@dp.message(F.text == "🧼 Помити листя")
async def wash_start(message: types.Message):
    plants = get_user_plants(message.from_user.id)
    if not plants:
        await message.answer("У тебе немає рослин.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for plant in plants:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🧼 {plant[2]}",
                callback_data=f"wash_{plant[0]}"
            )
        ])

    await message.answer("Яке листя миємо?", reply_markup=kb)

# =================== ПОЛИВ ===================
@dp.message(F.text == "💧 Полив")
async def water_start(message: types.Message):
    plants = get_user_plants(message.from_user.id)
    if not plants:
        await message.answer("У тебе немає рослин.")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for plant in plants:
        kb.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"💧 {plant[2]}",
                callback_data=f"water_{plant[0]}"
            )
        ])

    await message.answer("Яку рослину поливаємо?", reply_markup=kb)


# =================== CALLBACK ОБРОБНИКИ ===================
@dp.callback_query(F.data.startswith("water_"))
async def callback_water(callback: types.CallbackQuery):
    plant_id = int(callback.data.split("_")[1])
    plant = get_plant_by_id(plant_id)

    if not plant or plant[1] != callback.from_user.id:
        await callback.answer("Це не твоя рослина!", show_alert=True)
        return

    update_last_watered(plant_id)
    log_action(plant_id, "полив", callback.from_user.id, callback.from_user.username or "unknown")

    await callback.message.edit_text(
        f"✅ Полито!\n\n💧 Рослина <b>{plant[2]}</b> успішно полита.",
        parse_mode="HTML"
    )
    await callback.answer("Записано ✓")


@dp.callback_query(F.data.startswith("wash_"))
async def callback_wash(callback: types.CallbackQuery):
    plant_id = int(callback.data.split("_")[1])
    plant = get_plant_by_id(plant_id)

    if not plant or plant[1] != callback.from_user.id:
        await callback.answer("Це не твоя рослина!", show_alert=True)
        return

    update_last_washed(plant_id)
    log_action(plant_id, "миття листя", callback.from_user.id, callback.from_user.username or "unknown")

    await callback.message.edit_text(
        f"✅ Листя помито!\n\n🧼 Рослина <b>{plant[2]}</b>",
        parse_mode="HTML"
    )
    await callback.answer("Записано ✓")


@dp.callback_query(F.data.startswith("advice_"))
async def callback_advice(callback: types.CallbackQuery):
    plant_id = int(callback.data.split("_")[1])
    plant = get_plant_by_id(plant_id)

    if not plant or plant[1] != callback.from_user.id:
        await callback.answer("Це не твоя рослина!", show_alert=True)
        return

    await callback.message.edit_text(f"🤖 Думаю пораду для «{plant[2]}»...")

    advice_text = await get_advice(plant)

    await callback.message.edit_text(
        f"🌱 <b>{plant[2]}</b>\n\n{advice_text}",
        parse_mode="HTML"
    )
    await callback.answer("Готово")


@dp.callback_query(F.data.startswith("delete_"))
async def callback_delete(callback: types.CallbackQuery):
    plant_id = int(callback.data.split("_")[1])
    plant = get_plant_by_id(plant_id)

    if not plant or plant[1] != callback.from_user.id:
        await callback.answer("Це не твоя рослина!", show_alert=True)
        return

    name = plant[2]
    delete_plant(plant_id)

    await callback.message.edit_text(f"🗑 Рослину «{name}» видалено.")
    await callback.answer("Видалено", show_alert=True)

# =================== ЗАПУСК ===================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🌱 Бот запущений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())