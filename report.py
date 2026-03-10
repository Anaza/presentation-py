import requests
import json
import os
import base64
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from gigachat import GigaChat
from promt.weekly_report_promt import weekly_report_prompt

def parse_date(date_str):
    """Парсит дату в формате DD.MM или DD.MM.YYYY, возвращает datetime"""
    load_dotenv()
    current_year = datetime.now().year
    try:
        if len(date_str.split('.')) == 2:
            day, month = map(int, date_str.split('.'))
            return datetime(current_year, month, day)
        elif len(date_str.split('.')) == 3:
            day, month, year = map(int, date_str.split('.'))
            return datetime(year, month, day)
        else:
            raise ValueError("Неверный формат даты")
    except ValueError as e:
        raise ValueError(f"Ошибка парсинга даты: {e}")

def get_jira_issues(start_date, end_date):
    """Получает закрытые задачи из Jira за период"""
    load_dotenv()

    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_HOST = os.getenv('JIRA_HOST')
    JIRA_USER_NAME = os.getenv('JIRA_USER_NAME')
    JIRA_USER_PASS = os.getenv('JIRA_USER_PASS')

    # Формат дат для JQL: YYYY-MM-DD
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    # JQL: закрытые задачи проекта ADSTOOLS за период
    jql = f'project = ADSTOOLS AND status in (Done, Closed) AND updated >= {start_str} AND updated <= {end_str}'

    url = f"{JIRA_URL}/search"
    params = {
        'jql': jql,
        'fields': 'summary,description,customfield_10006',  # customfield_10006 - Epic Link
        'maxResults': 1000  # Ограничение на количество результатов
    }

    # Аутентификация
    auth_string = base64.b64encode(f"{JIRA_USER_NAME}:{JIRA_USER_PASS}".encode()).decode()
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=UTF-8',
        'host': JIRA_HOST,
        'Authorization': f'Basic {auth_string}',
    }

    response = requests.get(url, headers=headers, params=params, verify=False)

    if response.status_code == 200:
        data = response.json()
        issues = data['issues']
        print(f"Найдено задач: {len(issues)}")

        extracted_data = []
        epic_ids = set()

        for issue in issues:
            summary = issue['fields'].get('summary', '')
            description = issue['fields'].get('description', '')
            epic = issue['fields'].get('customfield_10006', '')

            extracted_data.append({
                "epic": epic,
                "title": summary,
                "description": description
            })

            if epic:
                epic_ids.add(epic)

        # Получить названия эпиков
        if epic_ids:
            epic_names = get_epic_names(list(epic_ids))
            for item in extracted_data:
                if item['epic']:
                    item['epic'] = epic_names.get(item['epic'], item['epic'])

        return extracted_data
    else:
        print(f"Ошибка {response.status_code}: {response.text}")
        return []

def get_epic_names(epic_ids):
    """Получает названия эпиков по их ID"""
    load_dotenv()

    JIRA_URL = os.getenv('JIRA_URL')
    JIRA_HOST = os.getenv('JIRA_HOST')
    JIRA_USER_NAME = os.getenv('JIRA_USER_NAME')
    JIRA_USER_PASS = os.getenv('JIRA_USER_PASS')

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
            print(f"Ошибка получения эпика {epic_id}: {response.status_code}")
            epic_names[epic_id] = f"Ошибка: {response.status_code}"

    return epic_names

def get_gigachat_client():
    """Получает клиент GigaChat"""
    load_dotenv()

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

def generate_weekly_report(tasks, start_date, end_date):
    """Генерирует отчет через GigaChat"""
    try:
        client = get_gigachat_client()

        user_content = f"Задачи: {json.dumps(tasks, ensure_ascii=False)}"

        message = f"{weekly_report_prompt}\n\n{user_content}"

        response = client.chat(message)

        report = response.choices[0].message.content.strip()
        return report
    except Exception as e:
        print(f"Ошибка при генерации отчета: {e}")
        # Если GigaChat не отвечает, записать сырые данные от Jira
        return json.dumps(tasks, ensure_ascii=False, indent=2)

def save_report(report, start_date):
    """Сохраняет отчет в папку report"""
    filename = f"report/weekly_report_{start_date.strftime('%Y-%m-%d')}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Отчет сохранен: {filename}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python report.py <date>")
        print("Date format: DD.MM or DD.MM.YYYY")
        sys.exit(1)

    date_str = sys.argv[1]
    try:
        start_date = parse_date(date_str)
        end_date = start_date + timedelta(days=7)

        print(f"Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")

        # Проверить, существует ли отчет
        filename = f"report/weekly_report_{start_date.strftime('%Y-%m-%d')}.md"
        if os.path.exists(filename):
            print("Отчет уже существует")
            return

        # Получить задачи
        tasks = get_jira_issues(start_date, end_date)

        if not tasks:
            print("Нет задач за указанный период")
            return

        # Сгенерировать отчет
        report = generate_weekly_report(tasks, start_date, end_date)

        # Сохранить отчет
        save_report(report, start_date)

    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()