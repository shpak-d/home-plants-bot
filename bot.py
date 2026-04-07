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
# Стан для додавання рослини
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


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


# ====================== ДОДАВАННЯ РОСЛИНИ З ФОТО ======================

class AddPlant(StatesGroup):
    waiting_for_name = State()
    waiting_for_photo = State()


@dp.message(F.text == "➕ Додати рослину")
async def add_plant_start(message: types.Message, state: FSMContext):
    if not is_allowed(message.from_user.id):
        return
    await message.answer(
        "Напиши дані рослини:\n"
        "<b>Назва полив нижній_полив</b>\n\n"
        "Приклад: Фікус 7 14"
    )
    await state.set_state(AddPlant.waiting_for_name)


@dp.message(AddPlant.waiting_for_name)
async def process_plant_name(message: types.Message, state: FSMContext):
    if not is_allowed(message.from_user.id):
        return
    try:
        parts = message.text.strip().split()
        name = " ".join(parts[:-2])
        watering = int(parts[-2])
        bottom = int(parts[-1])

        await state.update_data(name=name, watering=watering, bottom=bottom)

        await message.answer("Добре! Тепер надішли фото рослини (обов'язково).")
        await state.set_state(AddPlant.waiting_for_photo)
    except:
        await message.answer("❌ Неправильний формат.\nПриклад: Фікус 7 14\nСпробуй ще раз.")
        await state.clear()


@dp.message(AddPlant.waiting_for_photo, F.photo)
async def process_plant_photo(message: types.Message, state: FSMContext):
    if not is_allowed(message.from_user.id):
        return

    data = await state.get_data()
    name = data.get("name")
    watering = data.get("watering")
    bottom = data.get("bottom")

    if not name:
        await message.answer("Помилка стану. Почни додавання заново.")
        await state.clear()
        return

    photo_file_id = message.photo[-1].file_id

    add_plant(name, watering, bottom, photo_file_id)

    await message.answer(
        f"✅ Рослина «{name}» успішно додана з фото!",
        reply_markup=main_menu()
    )
    await state.clear()


# Якщо користувач надіслав щось інше замість фото
@dp.message(AddPlant.waiting_for_photo)
async def wrong_photo(message: types.Message):
    await message.answer("Будь ласка, надішли саме **фото** рослини.")

# ====================== СПІЛЬНІ РОСЛИНИ (з фото) ======================
@dp.message(F.text == "🌱 Мої рослини")
async def my_plants(message: types.Message):
    if not is_allowed(message.from_user.id): return

    plants = get_all_plants()
    if not plants:
        await message.answer("Поки немає рослин.")
        return

    for plant in plants:
        caption = f"🌿 <b>{plant[1]}</b>\nПолив: кожні {plant[2]} днів | Нижній: кожні {plant[3]} днів"
        if plant[4]:  # photo_file_id
            await message.answer_photo(photo=plant[4], caption=caption, parse_mode="HTML")
        else:
            await message.answer(caption, parse_mode="HTML")


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
    if not plant:
        await callback.answer("Рослину не знайдено", show_alert=True)
        return

    name = plant[1]
    photo_file_id = plant[4]

    await callback.message.edit_text(f"🤖 Генерую пораду для «{name}»...")

    advice_text = await get_advice(plant)

    # Обмежуємо довжину підпису до 900 символів (з запасом)
    if len(advice_text) > 900:
        advice_text = advice_text[:897] + "..."

    if photo_file_id:
        try:
            await callback.message.answer_photo(
                photo=photo_file_id,
                caption=f"🌱 <b>{name}</b>\n\n{advice_text}",
                parse_mode="HTML"
            )
        except:
            # Якщо навіть скорочений caption занадто довгий — надсилаємо без фото
            await callback.message.answer(
                f"🌱 <b>{name}</b>\n\n{advice_text}",
                parse_mode="HTML"
            )
    else:
        await callback.message.edit_text(
            f"🌱 <b>{name}</b>\n\n{advice_text}",
            parse_mode="HTML"
        )

    await callback.answer("Порада готова ✅")


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

# ====================== НАГАДУВАННЯ (поки ручне) ======================
@dp.message(Command("remind"))
async def manual_remind(message: types.Message):
    if not is_allowed(message.from_user.id): return
    plants = get_all_plants()
    if not plants:
        await message.answer("Немає рослин.")
        return

    await message.answer("🔄 Перевіряю, кому треба поливати...")

    for plant in plants:
        if not plant[5]: continue  # немає дати останнього поливу
        last_watered = datetime.fromisoformat(plant[5])
        days_passed = (datetime.now() - last_watered).days

        if days_passed >= plant[2] - 1:   # нагадуємо за 1 день до "терміну"
            for uid in ALLOWED_USERS:
                try:
                    text = f"⚠️ Нагадування!\nРослина <b>{plant[1]}</b> не поливалась {days_passed} днів.\nРекомендується полити."
                    await bot.send_message(uid, text, parse_mode="HTML")
                except:
                    pass

    await message.answer("✅ Нагадування надіслано.")

# ====================== ЗАПУСК ======================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🌱 Бот запущений...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())