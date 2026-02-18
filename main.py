import sys
import subprocess
import importlib.util
from src.create_pptx import create_presentation

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <sprint_number>")
        sys.exit(1)

    sprint_number = sys.argv[1]  # Keep as string for file names

    # Run read_pdf.py to update data_{sprint_number}.py
    subprocess.run([sys.executable, "src/read_pdf.py", sprint_number], check=True)

    # Import updated data from data_{sprint_number}.py
    data_file = f"data/data_{sprint_number}.py"
    spec = importlib.util.spec_from_file_location("data_module", data_file)
    data_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_module)
    data = data_module.data

    # Create presentation
    create_presentation(int(sprint_number), data)

    print(f"Presentation created: ./result/sprint_{sprint_number}.pptx")

if __name__ == "__main__":
    main()
