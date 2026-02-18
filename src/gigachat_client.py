import os
import base64
import importlib.util
import json
from dotenv import load_dotenv
from gigachat import GigaChat
from promt.promt import prompt

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
    data_file = f"data/data_raw_{sprint_number}.py"
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to load data: {str(e)}"}

def clean_gigachat_response(response):
    # Убрать ```json и ``` из ответа
    response = response.strip()
    if response.startswith('```json'):
        response = response[7:]
    if response.startswith('```'):
        response = response[3:]
    if response.endswith('```'):
        response = response[:-3]
    response = response.strip()
    # Убрать все оставшиеся ```
    response = response.replace('```', '')
    # Убрать комментарии после JSON
    for marker in ['\n\n###', '\n\n', '###']:
        pos = response.find(marker)
        if pos != -1:
            response = response[:pos]
            break
    response = response.strip()
    return response

def analyze_sprint_data_giga(sprint_number):
    client = get_gigachat_client()

    # Получить данные
    data = get_sprint_data(sprint_number)

    # Подготовить промпт
    system_prompt = prompt

    user_content = f"Данные спринта: {data}"

    message = f"{system_prompt}\n\n{user_content}"

    response = client.chat(message)

    gigachat_response = clean_gigachat_response(response.choices[0].message.content)

    # print("GigaChat response:", gigachat_response)
    # Предполагаем, что ответ в JSON формате
    try:
        result = json.loads(gigachat_response)
        # Сохранить чистый JSON в data файл
        data_file = f"data/data_{sprint_number}.py"
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        return result
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}")
        # Не сохранять файл, если JSON не валидный
        # Вернуть пустой список, чтобы избежать KeyError в create_pptx
        return []
