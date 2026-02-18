import pdfplumber
import json

def extract_data_from_pdf(pdf_path):
    data = []
    epic_groups = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Пропустить строки с менее чем 5 колонками или пустые
                    if len(row) < 5 or not row[1] or row[1].startswith('Код'):
                        continue
                    # Извлечь: Тип, Код, Тема, Описание, Epic Link
                    typ, code, theme, description, epic_link = row[:5]
                    if epic_link:
                        # Очистить epic от переносов
                        clean_epic = epic_link.replace('\n', ' ').strip()
                        if clean_epic not in epic_groups:
                            epic_groups[clean_epic] = []
                        # Очистить описание от лишних пробелов и переносов
                        clean_description = description.replace('\n', ' ').strip() if description else ''
                        epic_groups[clean_epic].append(clean_description)

    # Сформировать структуру
    for epic, items in epic_groups.items():
        data.append({
            "epic": epic,
            "title": epic,  # Как указано, извлечь из Epic Link
            "items": items
        })

    return data

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python read_pdf.py <sprint_number>")
        sys.exit(1)

    sprint_number = sys.argv[1]
    pdf_path = f"pdf/sprint_{sprint_number}.pdf"
    extracted_data = extract_data_from_pdf(pdf_path)
    # Сохранить в data_{sprint_number}.py
    data_file = f"data/data_{sprint_number}.py"
    with open(data_file, "w", encoding="utf-8") as f:
        f.write("data = ")
        f.write(json.dumps(extracted_data, ensure_ascii=False, indent=4))
    print(f"Data saved to {data_file}")
