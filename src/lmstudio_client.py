import os
import json
import re
from openai import OpenAI
from promt.promt import prompt

def get_lmstudio_client():
    # LMStudio обычно работает на localhost:1234 без дополнительных credentials
    client = OpenAI(
        base_url="http://localhost:1234/v1",
        api_key="not-needed"  # LMStudio не требует API key
    )
    return client

def get_sprint_data(sprint_number):
    data_file = f"data/data_raw_{sprint_number}.py"
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to load data: {str(e)}"}

def get_analyzed_data(sprint_number):
    data_file = f"data/data_{sprint_number}.py"
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise FileNotFoundError(f"Analyzed data file not found: {data_file}. Run with use_ai='lmstudio' or 'giga' first or ensure the file exists.")

def clean_lmstudio_response(response):
    # print("LM Studio response:", response)
    # Аналогичная очистка как в gigachat_client
    response = response.strip()
    # Убрать секцию <think>...</think>
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
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

def analyze_sprint_data_lmstudio(sprint_number):
    client = get_lmstudio_client()

    # Получить данные
    data = get_sprint_data(sprint_number)

    # Подготовить промпт
    system_prompt = prompt

    user_content = f"Данные спринта: {data}"

    message = f"{system_prompt}\n\n{user_content}"

    response = client.chat.completions.create(
        model="lmstudio-community/DeepSeek-R1-0528-Qwen3-8B-GGUF",
        messages=[
            {"role": "user", "content": message}
        ],
        temperature=0.7
    )

    lmstudio_response = clean_lmstudio_response(response.choices[0].message.content)

    # Предполагаем, что ответ в JSON формате
    try:
        result = json.loads(lmstudio_response)
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