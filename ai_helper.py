from google import genai
from google.genai.types import Part
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def get_advice(plant):
    """Проста текстова порада (поки без фото)"""
    prompt = f"""
Ти — досвідчений ботанік по кімнатних рослинах.

Рослина: {plant[2]}
Звичайний полив: кожні {plant[3]} днів
Нижній полив: кожні {plant[4]} днів
Останній полив: {plant[6] if plant[6] else 'невідомо'}
Останнє миття листя: {plant[7] if plant[7] else 'невідомо'}

Дай коротку, корисну пораду українською мовою на найближчі 7 днів.
Напиши дружньо:
- чи треба поливати найближчим часом
- можливі проблеми
- що рекомендуєш зробити

Відповідай природно і без зайвої води.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt]
        )
        return response.text.strip()
    except Exception as e:
        return f"Вибач, зараз не можу отримати пораду.\nПомилка: {str(e)}"