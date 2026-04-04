from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def get_advice(plant):
    # plant — це кортеж з БД:
    # (id, name, watering_interval, bottom_watering_interval, photo_file_id, last_watered, last_washed, last_photo_update)

    name = plant[1]
    watering_interval = plant[2]
    bottom_interval = plant[3]
    last_watered = plant[5][:10] if plant[5] else "невідомо"
    last_washed = plant[6][:10] if plant[6] else "невідомо"

    prompt = f"""
Ти — досвідчений ботанік по кімнатних рослинах.

Рослина: {name}
Звичайний полив: кожні {watering_interval} днів
Нижній полив (в таз): кожні {bottom_interval} днів
Останній полив: {last_watered}
Останнє миття листя: {last_washed}

Дай коротку, корисну пораду українською мовою на найближчі 5–7 днів.
Напиши:
- чи треба поливати найближчим часом
- чи є ризики переливу або пересушування
- рекомендації по догляду (листя, світло тощо)

Відповідай природно, дружньо і без зайвої води.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt]
        )
        return response.text.strip()
    except Exception as e:
        return f"Вибач, не вдалося отримати пораду.\nПомилка: {str(e)}"