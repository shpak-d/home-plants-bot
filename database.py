import sqlite3
from datetime import datetime

conn = sqlite3.connect('plants.db', check_same_thread=False)
cur = conn.cursor()


def init_db():
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS plants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        watering_interval INTEGER DEFAULT 7,
        is_bottom_watering INTEGER DEFAULT 0,   -- 1 = нижній полив
        leaf_wash_interval INTEGER DEFAULT 14,
        last_watered TEXT,
        last_washed TEXT
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS action_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plant_id INTEGER,
        action TEXT,
        user_id INTEGER,
        username TEXT,
        timestamp TEXT
    )''')
    conn.commit()


def add_plant(user_id: int, name: str, watering_days: int, is_bottom: bool):
    cur.execute('''INSERT INTO plants 
        (user_id, name, watering_interval, is_bottom_watering, last_watered, last_washed)
        VALUES (?, ?, ?, ?, ?, ?)''',
                (user_id, name, watering_days, int(is_bottom),
                 datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    return cur.lastrowid


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