# Presentation-Py

Инструмент для автоматической генерации презентаций PowerPoint на основе данных о спринтах разработки. Создает структурированные слайды с информацией об эпиках, задачах и достижениях команды.

## Установка

Убедитесь, что у вас установлен [uv](https://github.com/astral-sh/uv) для управления зависимостями.

```bash
uv init
uv add python-pptx
uv sync
```

## Использование

### Запуск проекта

```bash
uv run main.py <sprint_number> <data_source> <ai_processing>
```

Где:
- `<sprint_number>` - номер спринта (например, 24)
- `<data_source>` - источник данных:
  - `jira` - получить данные из Jira
  - `pdf` - получить данные из PDF-файла спринта
  - `json` - использовать готовые обработанные данные из файла `data/data_<sprint_number>.py`
- `<ai_processing>` - обработка данных через ИИ:
  - `none` - без ИИ, использует сырые данные
  - `giga` - анализ через GigaChat (требует API ключа)
  - `lmstudio` - анализ через локальную модель LMStudio
  - `ollama` - анализ через локальную модель Ollama (deepseek-r1:8b)

### Примеры использования

```bash
# Использовать готовый JSON из файла data_24.py
uv run main.py 24 json none

# Получить данные из Jira и обработать через GigaChat
uv run main.py 24 jira giga

# Получить данные из PDF и обработать через GigaChat
uv run main.py 24 pdf giga

# Получить данные из PDF и обработать через LMStudio
uv run main.py 24 pjiraf lmstudio
```

Результат сохраняется в папку `result/` как `sprint_<sprint_number>.pptx`.

## Структура проекта

- `main.py` - основной скрипт генерации презентации
- `template/base.pptx` - базовый шаблон презентации
- `data/` - данные для слайдов (эпики, задачи)
- `result/` - папка для готовых презентаций
- `images/logo.png` - логотип (опционально)

## Зависимости

- Python >= 3.12
- python-pptx >= 1.0.2
