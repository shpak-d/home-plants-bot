import sqlite3
from datetime import datetime

conn = sqlite3.connect('plants.db', check_same_thread=False)
cur = conn.cursor()


def init_db():
    # Спільна таблиця рослин
    cur.execute('''CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        watering_interval INTEGER DEFAULT 7,
        bottom_watering_interval INTEGER DEFAULT 14,
        photo_file_id TEXT,
        last_watered TEXT,
        last_washed TEXT,
        last_photo_update TEXT
    )''')

    # Таблиця користувачів для розсилки
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT
    )''')

    # Логи дій
    cur.execute('''CREATE TABLE IF NOT EXISTS action_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_id INTEGER,
        action TEXT,
        user_id INTEGER,
        username TEXT,
        timestamp TEXT
    )''')

    conn.commit()
    print("✅ База даних ініціалізована (спільна для 2 користувачів)")


def add_plant(name: str, watering_days: int, bottom_days: int, photo_file_id=None):
    cur.execute('''INSERT INTO plants 
        (name, watering_interval, bottom_watering_interval, photo_file_id, 
         last_watered, last_washed, last_photo_update)
        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (name, watering_days, bottom_days, photo_file_id,
                 datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    return cur.lastrowid


def get_all_plants():
    cur.execute("SELECT * FROM plants ORDER BY name")
    return cur.fetchall()


def get_plant_by_id(plant_id: int):
    cur.execute("SELECT * FROM plants WHERE id = ?", (plant_id,))
    return cur.fetchone()


def update_last_watered(plant_id: int):
    cur.execute("UPDATE plants SET last_watered = ? WHERE id = ?",
                (datetime.now().isoformat(), plant_id))
    conn.commit()


def update_last_washed(plant_id: int):
    cur.execute("UPDATE plants SET last_washed = ? WHERE id = ?",
                (datetime.now().isoformat(), plant_id))
    conn.commit()


def delete_plant(plant_id: int):
    cur.execute("DELETE FROM plants WHERE id = ?", (plant_id,))
    conn.commit()


def add_user(user_id: int, username: str = None, first_name: str = None):
    cur.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)",
                (user_id, username, first_name))
    conn.commit()


def get_all_users():
    cur.execute("SELECT user_id FROM users")
    return [row[0] for row in cur.fetchall()]


init_db()