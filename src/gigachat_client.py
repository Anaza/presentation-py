import os
import base64
import importlib.util
from dotenv import load_dotenv
from gigachat import GigaChat

load_dotenv()

def get_gigachat_client():
    # Получаем учетные данные из переменных окружения
    client_id = os.getenv("GIGAGW_CLIENT_ID", "")
    client_secret = os.getenv("GIGAGW_CLIENT_SECRET", "")
    user_pass = f"{client_id}:{client_secret}"
    credentials_b64 = base64.b64encode(user_pass.encode("utf-8")).decode("utf-8")

    base_url = os.getenv("GIGAGW_BASE_URL")
    auth_url = os.getenv("GIGAGW_AUTH_URL")

    if not all([client_id, client_secret, base_url, auth_url]):
        raise ValueError("Missing GigaChat credentials in .env")

    return GigaChat(
      credentials=credentials_b64,
      base_url=base_url,
      auth_url=auth_url,
      verify_ssl_certs=False,
    )

def get_sprint_data(sprint_number):
    data_file = f"data/data_{sprint_number}.py"
    try:
        spec = importlib.util.spec_from_file_location("data_module", data_file)
        data_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(data_module)
        return data_module.data
    except Exception as e:
        return {"error": f"Failed to load data: {str(e)}"}

def analyze_sprint_data(sprint_number):
    client = get_gigachat_client()

    # Получить данные
    data = get_sprint_data(sprint_number)

    # Подготовить промпт
    system_prompt = """
    Ты помощник для анализа данных спринта. Проанализируй предоставленные данные, сгруппируй их логически и подготовь 5-7 текстовых блоков для слайдов презентации.
    Каждый блок должен быть кратким (не более 500 символов) и содержать ключевую информацию по группе задач.
    Формат вывода: JSON массив объектов с полями "title" и "content".
    """

    user_content = f"Данные спринта: {data}"

    message = f"{system_prompt}\n\n{user_content}"

    response = client.chat(message)

    # Предполагаем, что ответ в JSON формате
    import json
    try:
        result = json.loads(response.choices[0].message.content)
        return result
    except:
        # Если не JSON, вернуть как есть
        return [{"title": "Анализ", "content": response.choices[0].message.content}]
