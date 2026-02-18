import pdfplumber
import json

def extract_data_from_pdf(pdf_path):
    data = []

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
                        # Очистить описание от лишних пробелов и переносов
                        clean_description = description.replace('\n', ' ').strip() if description else ''
                        # Очистить title (theme)
                        clean_title = theme.replace('\n', ' ').strip() if theme else ''
                        data.append({
                            "epic": clean_epic,
                            "title": clean_title,
                            "description": clean_description
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
    # Сохранить в data_raw_{sprint_number}.py как чистый JSON
    data_file = f"data/data_raw_{sprint_number}.py"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=4)
    print(f"Raw data saved to {data_file}")
