import sys
import subprocess
from src.create_pptx import create_presentation
from src.gigachat_client import analyze_sprint_data, get_analyzed_data
from src.lmstudio_client import analyze_sprint_data_lmstudio
from src.ollama_client import analyze_sprint_data_ollama

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <sprint_number> <use_ai>")
        print("use_ai options: 'none' (no AI, use existing data), 'giga' (GigaChat), 'lmstudio' (LMStudio), 'ollama' (Ollama), 'get_data_jira' (get data from Jira)")
        sys.exit(1)

    sprint_number = sys.argv[1]  # Keep as string for file names
    use_ai = sys.argv[2].lower()

    if use_ai == 'get_data_jira':
        # Get data from Jira
        subprocess.run([sys.executable, "src/get_jira_data.py", sprint_number], check=True)
        print(f"Data from Jira saved for sprint {sprint_number}")
        return  # Exit without creating presentation

    if use_ai not in ['none', 'giga', 'lmstudio', 'ollama']:
        print("Invalid use_ai option. Use 'none', 'giga', 'lmstudio', 'ollama', or 'get_data_jira'")
        sys.exit(1)

    if use_ai != 'none':
        # Run read_pdf.py to update data_raw_{sprint_number}.py
        subprocess.run([sys.executable, "src/read_pdf.py", sprint_number], check=True)

        if use_ai == 'giga':
            # Analyze data with GigaChat
            analyzed_data = analyze_sprint_data(sprint_number)
        elif use_ai == 'lmstudio':
            # Analyze data with LMStudio
            analyzed_data = analyze_sprint_data_lmstudio(sprint_number)
        elif use_ai == 'ollama':
            # Analyze data with Ollama
            analyzed_data = analyze_sprint_data_ollama(sprint_number)
    else:
        # Load existing analyzed data
        analyzed_data = get_analyzed_data(sprint_number)

    # Create presentation
    create_presentation(int(sprint_number), analyzed_data)

    print(f"Presentation created: ./result/sprint_{sprint_number}.pptx")

if __name__ == "__main__":
    main()
