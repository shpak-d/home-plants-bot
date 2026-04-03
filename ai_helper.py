import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.5-flash')

async def get_advice(plant) -> str:
    prompt = f"""
Ти — досвідчений ботанік і помічник по догляду за кімнатними рослинами.
Рослина: {plant[2]}
Інтервал поливу: кожні {plant[3]} днів
Тип поливу: {'нижній (ставити в таз з водою)' if plant[4] else 'звичайний'}
Останній полив: {plant[6] if plant[6] else 'невідомо'}
Останнє миття листя: {plant[7] if plant[7] else 'невідомо'}

Дай коротку та корисну пораду українською мовою на найближчі 5–7 днів.
Напиши:
- чи треба зараз поливати
- чи є якісь ризики
- рекомендації по догляду

Відповідай природно, дружньо і без зайвої води.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Вибач, не вдалося отримати пораду зараз. Спробуй пізніше.\n\nПомилка: {str(e)}"