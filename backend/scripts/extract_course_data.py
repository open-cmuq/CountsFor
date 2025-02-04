import os
import json
import pandas as pd

# Path to the folder containing course JSON files
COURSE_JSON_FOLDER = r"data/course"
# Output Excel file for verification
OUTPUT_EXCEL_FILE = r"data/extracted_courses.xlsx"

def extract_courses_from_json(folder_path):
    """
    Reads all course JSON files in a folder and extracts relevant data.
    Saves the extracted data into an Excel file for verification.
    """
    courses_data = []  # To store extracted course details

    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r") as file:
                data = json.load(file)

            # Skip invalid course files
            if not data.get("success", True):
                print(f"[Warning] Skipping invalid course file: {filename}")
                continue

            try:
                # Extract course details
                course_info = {
                    "code": data.get("code"),
                    "name": data.get("name"),
                    "units": int(data.get("units", 0)),
                    "min_units": int(data.get("min_units")) if data.get("min_units") else None,
                    "max_units": int(data.get("max_units")) if data.get("max_units") else None,
                    "is_topic": data.get("is_topic", False),
                    "topic": data.get("topic"),
                    "offered_qatar": 1 in data.get("offered_in_campuses", []),
                    "offered_pitts": 2 in data.get("offered_in_campuses", []),
                    "short_name": data.get("short_name"),
                    "description": data.get("long_desc", ""),
                    "undergraduate": 1 if any(s.get("name") == "undergraduate" for s in data.get("student_sets", [])) else 0,
                    "dep_code": (data["code"].split("-")[0]) if data.get("code") else None  # Extract department code from course code
                }

                courses_data.append(course_info)

            except KeyError as e:
                print(f"[Error] Missing key {e} in file: {filename}")
            except Exception as e:
                print(f"[Error] Failed to process file {filename}: {e}")

    return courses_data


def save_to_excel(data, output_file):
    """
    Saves extracted course data to an Excel file.
    """
    if data:
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        print(f"✅ Data successfully saved to {output_file}")
    else:
        print("⚠️ No valid data found to save.")


def main():
    # Extract data from JSON files
    extracted_courses = extract_courses_from_json(COURSE_JSON_FOLDER)

    # Save extracted data to Excel for verification
    save_to_excel(extracted_courses, OUTPUT_EXCEL_FILE)


if __name__ == "__main__":
    main()
