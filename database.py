import sqlite3
from datetime import datetime

conn = sqlite3.connect('plants.db', check_same_thread=False)
cur = conn.cursor()


def init_db():
    # Створюємо таблицю plants
    cur.execute('''CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        watering_interval INTEGER DEFAULT 7,
        bottom_watering_interval INTEGER DEFAULT 14,
        photo_file_id TEXT,
        last_watered TEXT,
        last_washed TEXT,
        last_photo_update TEXT
    )''')

    # Таблиця користувачів
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT
    )''')

    # Таблиця логів дій
    cur.execute('''CREATE TABLE IF NOT EXISTS action_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_id INTEGER,
        action TEXT,
        user_id INTEGER,
        username TEXT,
        timestamp TEXT
    )''')

    conn.commit()
    print("✅ База даних ініціалізована успішно")


def add_plant(user_id: int, name: str, watering_days: int, bottom_days: int, photo_file_id=None):
    cur.execute('''INSERT INTO plants 
        (user_id, name, watering_interval, bottom_watering_interval, photo_file_id, 
         last_watered, last_washed, last_photo_update)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, name, watering_days, bottom_days,
         photo_file_id,
         datetime.now().isoformat(),
         datetime.now().isoformat(),
         datetime.now().isoformat()))
    conn.commit()
    return cur.lastrowid


def get_plant_by_id(plant_id: int):
    cur.execute("SELECT * FROM plants WHERE id = ?", (plant_id,))
    return cur.fetchone()


def delete_plant(plant_id: int):
    cur.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
    conn.commit()


def get_user_plants(user_id: int):
    cur.execute("SELECT * FROM plants WHERE user_id = ?", (user_id,))
    return cur.fetchall()


def log_action(plant_id: int, action: str, user_id: int, username: str):
    cur.execute('''INSERT INTO action_logs 
        (plant_id, action, user_id, username, timestamp)
        VALUES (?, ?, ?, ?, ?)''',
                (plant_id, action, user_id, username, datetime.now().isoformat()))
    conn.commit()


def update_last_watered(plant_id: int):
    cur.execute("UPDATE plants SET last_watered = ? WHERE id = ?",
                (datetime.now().isoformat(), plant_id))
    conn.commit()


def update_last_washed(plant_id: int):
    cur.execute("UPDATE plants SET last_washed = ? WHERE id = ?",
                (datetime.now().isoformat(), plant_id))
    conn.commit()


init_db()