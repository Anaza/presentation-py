import sys
import subprocess
import json
from src.create_pptx import create_presentation
from src.gigachat_client import analyze_sprint_data_giga
from src.lmstudio_client import analyze_sprint_data_lmstudio
from src.ollama_client import analyze_sprint_data_ollama
from src.get_jira_data import get_jira_data

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
        raise FileNotFoundError(f"Analyzed data file not found: {data_file}. Run with use_ai=true first or ensure the file exists.")

def main():
    if len(sys.argv) < 4:
        print("Usage: python main.py <sprint_number> <data_source> <ai_processing>")
        print("data_source: jira, pdf, json")
        print("ai_processing: none, giga, lmstudio, ollama")
        sys.exit(1)

    sprint_number = sys.argv[1]
    data_source = sys.argv[2].lower()
    ai_processing = sys.argv[3].lower()

    if data_source == 'jira':
        analyzed_data = get_jira_data(sprint_number)
    elif data_source == 'pdf':
        subprocess.run([sys.executable, "src/read_pdf.py", sprint_number], check=True)
    elif data_source == 'json':
        analyzed_data = get_analyzed_data(sprint_number)
    else:
        print("Invalid data_source. Use 'jira', 'pdf', or 'json'")
        sys.exit(1)

    if ai_processing != 'none':
        if ai_processing == 'giga':
            analyzed_data = analyze_sprint_data_giga(sprint_number)
        elif ai_processing == 'lmstudio':
            analyzed_data = analyze_sprint_data_lmstudio(sprint_number)
        elif ai_processing == 'ollama':
            analyzed_data = analyze_sprint_data_ollama(sprint_number)
        else:
            print("Invalid ai_processing. Use 'none', 'giga', 'lmstudio', or 'ollama'")
            sys.exit(1)
    else:
        if data_source == 'json':
            pass  # already loaded
        else:
            analyzed_data = get_analyzed_data(sprint_number)

    # Create presentation
    create_presentation(int(sprint_number), analyzed_data)

    print(f"Presentation created: ./result/sprint_{sprint_number}.pptx")

if __name__ == "__main__":
    main()
