import sys
import subprocess
from src.create_pptx import create_presentation
from src.gigachat_client import analyze_sprint_data, get_analyzed_data
from src.lmstudio_client import analyze_sprint_data_lmstudio

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <sprint_number> <use_ai>")
        print("use_ai options: 'none' (no AI, use existing data), 'giga' (GigaChat), 'lmstudio' (LMStudio)")
        sys.exit(1)

    sprint_number = sys.argv[1]  # Keep as string for file names
    use_ai = sys.argv[2].lower()

    if use_ai not in ['none', 'giga', 'lmstudio']:
        print("Invalid use_ai option. Use 'none', 'giga', or 'lmstudio'")
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
    else:
        # Load existing analyzed data
        analyzed_data = get_analyzed_data(sprint_number)

    # Create presentation
    create_presentation(int(sprint_number), analyzed_data)

    print(f"Presentation created: ./result/sprint_{sprint_number}.pptx")

if __name__ == "__main__":
    main()
