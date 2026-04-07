from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def get_advice(plant):
    """Порада від AI з правильними даними"""
    name = plant[1]
    watering = plant[2]
    bottom = plant[3]
    last_watered = plant[5][:10] if plant[5] else "невідомо"
    last_washed = plant[6][:10] if plant[6] else "невідомо"

    prompt = f"""
Ти — досвідчений ботанік по кімнатних рослинах.

Рослина: {name}
Звичайний полив: кожні {watering} днів
Нижній полив (в таз): кожні {bottom} днів
Останній полив: {last_watered}
Останнє миття листя: {last_washed}

Дай дуже коротку, корисну пораду українською мовою.
Зверни увагу на вигляд. Що рекомендуєш зробити?
Відповідай без зайвої води.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # model="gemini-2.5-flash-lite", легша версія, часто стабільніша
    contents=[prompt]
        )
        return response.text.strip()
    except Exception as e:
        return f"Вибач, не вдалося отримати пораду зараз.\nПомилка: {str(e)}"