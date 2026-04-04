from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    kb = [
        [KeyboardButton(text="➕ Додати рослину")],
        [KeyboardButton(text="🌱 Мої рослини"), KeyboardButton(text="🗑 Видалити рослину")],
        [KeyboardButton(text="💧 Полив"), KeyboardButton(text="🧼 Помити листя")],
        [KeyboardButton(text="🤖 Порада від AI")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)