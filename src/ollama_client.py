import os
import json
from openai import OpenAI
from promt.promt import prompt

def get_ollama_client():
    # Ollama работает на localhost:11434 с OpenAI-compatible API
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="not-needed"  # Ollama не требует API key
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
        raise FileNotFoundError(f"Analyzed data file not found: {data_file}. Run with use_ai='ollama' first or ensure the file exists.")

def clean_ollama_response(response):
    # Аналогичная очистка как в других клиентах
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
    # Убрать <think> блоки (для DeepSeek-R1)
    import re
    response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    # Убрать комментарии после JSON
    for marker in ['\n\n###', '\n\n', '###']:
        pos = response.find(marker)
        if pos != -1:
            response = response[:pos]
            break
    response = response.strip()
    return response

def parse_text_to_json(text):
    # Парсинг текста вида "### Резюме задач:" с нумерованным списком
    import re
    result = []
    # Убрать заголовок "### Резюме задач:" если есть
    text = re.sub(r'^###\s*Резюме\s*задач:\s*\n?', '', text, flags=re.MULTILINE | re.IGNORECASE)
    # Найти все эпики: 1. **Epic Name**: \n - item1\n - item2
    pattern = r'\d+\.\s*\*\*(.*?)\*\*:\s*\n((?:[^\d]*?(?=\d+\.\s*\*\*|$)))'
    matches = re.findall(pattern, text, re.DOTALL)
    for epic, items_text in matches:
        epic = epic.strip()
        # Разделить items по - , учитывать многострочные
        items = re.findall(r'-\s*(.*?)(?=\n\s*-\s*|\n\s*\d+\.\s*\*\*|$)', items_text, re.DOTALL)
        items = [item.strip().replace('\n', ' ') for item in items if item.strip()]
        if items:
            result.append({
                "epic": epic,
                "title": epic,
                "items": items
            })
    return result

def analyze_sprint_data_ollama(sprint_number):
    client = get_ollama_client()

    # Получить данные
    data = get_sprint_data(sprint_number)

    # Подготовить промпт
    system_prompt = prompt

    user_content = f"Данные спринта: {data}"

    response = client.chat.completions.create(
        model="deepseek-r1:8b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.7
    )

    raw_response = response.choices[0].message.content
    ollama_response = clean_ollama_response(raw_response)

    print(f"Ollama raw response: {ollama_response}")

    # Сохранить сырой ответ для отладки всегда
    raw_data_file = f"data/data_{sprint_number}_raw.txt"
    with open(raw_data_file, "w", encoding="utf-8") as f:
        f.write(raw_response)
    print(f"Saved raw response to {raw_data_file}")

    # Сначала попробовать парсить как JSON
    try:
        result = json.loads(ollama_response)
        print("Successfully parsed as JSON")
    except json.JSONDecodeError:
        # Если не JSON, попробовать парсить как текст
        print("Response is not JSON, trying to parse as text...")
        result = parse_text_to_json(ollama_response)
        if not result:
            print("Failed to parse as text")
            return []

    # Сохранить результат в data файл
    data_file = f"data/data_{sprint_number}.py"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    return result
