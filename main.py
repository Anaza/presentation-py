import sys
import subprocess
from src.create_pptx import create_presentation
from src.gigachat_client import analyze_sprint_data

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <sprint_number>")
        sys.exit(1)

    sprint_number = sys.argv[1]  # Keep as string for file names

    # Run read_pdf.py to update data_{sprint_number}.py
    subprocess.run([sys.executable, "src/read_pdf.py", sprint_number], check=True)

    # Analyze data with GigaChat
    analyzed_data = analyze_sprint_data(sprint_number)

    # Create presentation
    create_presentation(int(sprint_number), analyzed_data)

    print(f"Presentation created: ./result/sprint_{sprint_number}.pptx")

if __name__ == "__main__":
    main()
