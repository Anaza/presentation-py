import requests
import json
import os
import base64
from dotenv import load_dotenv

def get_epic_names(epic_ids, sprint_number):
    # Загружаем переменные из .env
    load_dotenv()

    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_HOST = os.getenv('JIRA_HOST')
    JIRA_USER_NAME = os.getenv('JIRA_USER_NAME')
    JIRA_USER_PASS = os.getenv('JIRA_USER_PASS')

    # Аутентификация
    auth_string = base64.b64encode(f"{JIRA_USER_NAME}:{JIRA_USER_PASS}".encode()).decode()
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8',
        'host': JIRA_HOST,
        'Authorization': f'Basic {auth_string}',
    }

    epic_names = {}
    for epic_id in epic_ids:
        if not epic_id:
            continue
        url = f"{JIRA_URL}/issue/{epic_id}?fields=summary"
        response = requests.get(url, headers=headers, verify=False)
        if response.status_code == 200:
            data = response.json()
            summary = data['fields'].get('summary', '')
            epic_names[epic_id] = summary
        else:
            print(f"Ошибка получения эпика {epic_id}: {response.status_code} {response.text}")
            epic_names[epic_id] = f"Ошибка: {response.status_code}"

    return epic_names

def get_jira_data(sprint_number):
    # Загружаем переменные из .env
    load_dotenv()

    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_HOST = os.getenv('JIRA_HOST')
    JIRA_USER_NAME = os.getenv('JIRA_USER_NAME')
    JIRA_USER_PASS = os.getenv('JIRA_USER_PASS')

    SPRINT_NAME = f"Tools.{sprint_number}"

    # 1. Формируем JQL-запрос (получаем задачи спринта в проекте ADSTOOLS со статусами Сделано, Готово, Выполнено)
    jql = f'project = ADSTOOLS AND sprint = {SPRINT_NAME} AND (status = "Done"  OR status = "Ready" OR status = "Closed")'

    # 2. Параметры запроса
    url = f"{JIRA_URL}/search"
    params = {
        'jql': jql,
        'fields': 'summary,description,customfield_10006'  # customfield_10001 - предполагаемый ID для Epic Link
    }

    # 3. Аутентификация
    auth_string = base64.b64encode(f"{JIRA_USER_NAME}:{JIRA_USER_PASS}".encode()).decode()
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8',
        'host': JIRA_HOST,
        'Authorization': f'Basic {auth_string}',
    }

    # 4. Выполняем GET-запрос
    response = requests.get(url, headers=headers, params=params, verify=False)

    # 5. Обрабатываем ответ
    if response.status_code == 200:
        data = response.json()
        issues = data['issues']
        print(f"Найдено задач в спринте {SPRINT_NAME}: {len(issues)}\n")

        extracted_data = []
        for issue in issues:
            summary = issue['fields'].get('summary', '')
            description = issue['fields'].get('description', '')
            epic = issue['fields'].get('customfield_10006', '')  # Epic Link

            extracted_data.append({
                "epic": epic,
                "title": summary,
                "description": description
            })

        # Собираем уникальные epic IDs и получаем их названия
        epic_ids = set(item['epic'] for item in extracted_data if item['epic'])
        if epic_ids:
            epic_names = get_epic_names(list(epic_ids), sprint_number)
            epic_file = f"data/epic_names_{sprint_number}.json"
            with open(epic_file, "w", encoding="utf-8") as f:
                json.dump(epic_names, f, ensure_ascii=False, indent=4)
            print(f"Названия эпиков сохранены в {epic_file}")

            # Заменяем epic ID на название в extracted_data
            for item in extracted_data:
                item['epic'] = epic_names.get(item['epic'], item['epic'])

        # Сохраняем в файл (после замены epic на название)
        data_file = f"data/data_raw_{sprint_number}.py"
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print(f"Данные сохранены в {data_file}")

        return extracted_data
    else:
        print(f"Ошибка {response.status_code}: {response.text}")
        return []

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python get_jira_data.py <sprint_number>")
        sys.exit(1)

    sprint_number = sys.argv[1]
    get_jira_data(sprint_number)
