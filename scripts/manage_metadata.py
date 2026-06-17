import csv
import os
from datetime import date

CSV_DIR = "metadata"
CSV_FILE = os.path.join(CSV_DIR, "sources.csv")
HEADER = [
    "filename",
    "source",
    "category",
    "subcategory",
    "date",
    "word_count",
    "link",
]

REQUIRED_FIELDS = {"filename", "category", "word_count"}


def ensure_csv_exists():
    os.makedirs(CSV_DIR, exist_ok=True)
    if not os.path.exists(CSV_FILE) or os.path.getsize(CSV_FILE) == 0:
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=HEADER)
            writer.writeheader()


def read_rows():
    ensure_csv_exists()
    with open(CSV_FILE, "r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def write_rows(rows):
    with open(CSV_FILE, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)


def display_rows(rows):
    if not rows:
        print("\nNo rows found in the CSV file.")
        return

    total_word_count = 0
    print("\nCurrent rows in sources.csv:")
    print("Index | " + " | ".join(HEADER))
    print("-" * (8 + len(HEADER) * 15))
    for idx, row in enumerate(rows, start=1):
        values = [row.get(col, "") for col in HEADER]
        try:
            total_word_count += int(row.get("word_count", "0"))
        except ValueError:
            pass
        print(f"{idx:>5} | " + " | ".join(values))

    print("-" * (8 + len(HEADER) * 15))
    print(f"Total word_count: {total_word_count}")


def prompt_value(prompt, default=None, allow_empty=False, required=False):
    if default is not None:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    while True:
        value = input(prompt).strip()
        if value:
            return value
        if default is not None and not required:
            return default
        if allow_empty:
            return ""
        if not required and default is None:
            return ""
        print("This field cannot be empty.")


def add_row():
    rows = read_rows()
    print("\nAdd a new row to sources.csv")
    row = {
        "filename": prompt_value("Enter filename", required=True),
        "source": prompt_value("Enter source", default="Malayalam Wikipedia"),
        "category": prompt_value("Enter category", required=True),
        "subcategory": prompt_value("Enter subcategory", default="none", allow_empty=True),
        "date": prompt_value("Enter date", default=str(date.today())),
        "word_count": prompt_value("Enter word_count", required=True),
        "link": prompt_value("Enter link"),
    }
    rows.append(row)
    write_rows(rows)
    print("Row added successfully.")


def choose_row(rows, action_name):
    if not rows:
        print(f"\nNo rows are available to {action_name}.")
        return None
    display_rows(rows)
    while True:
        choice = input(f"\nEnter the row index to {action_name} (or 'c' to cancel): ").strip()
        if choice.lower() == "c":
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(rows):
                return idx - 1
        print("Invalid index. Please enter a valid row number or 'c' to cancel.")


def modify_row():
    rows = read_rows()
    row_index = choose_row(rows, "modify")
    if row_index is None:
        return

    print("\nEnter new values or press Enter to keep the existing value.")
    row = rows[row_index]
    for key in HEADER:
        is_required = key in REQUIRED_FIELDS
        default_value = row.get(key, "")
        row[key] = prompt_value(
            f"{key}",
            default=default_value,
            allow_empty=(key not in REQUIRED_FIELDS),
            required=is_required,
        )
    write_rows(rows)
    print("Row updated successfully.")


def delete_row():
    rows = read_rows()
    row_index = choose_row(rows, "delete")
    if row_index is None:
        return

    confirm = input("Are you sure you want to delete this row? (y/n): ").strip().lower()
    if confirm == "y":
        deleted = rows.pop(row_index)
        write_rows(rows)
        print(f"Row deleted: {deleted}")
    else:
        print("Deletion cancelled.")


def main_menu():
    ensure_csv_exists()
    while True:
        print("\nCSV Editor for metadata/sources.csv")
        print("1. View rows")
        print("2. Add row")
        print("3. Modify row")
        print("4. Delete row")
        print("5. Total word count")
        print("6. Exit")

        choice = input("Choose an option: ").strip()
        if choice == "1":
            display_rows(read_rows())
        elif choice == "2":
            add_row()
        elif choice == "3":
            modify_row()
        elif choice == "4":
            delete_row()
        elif choice == "5":
            rows = read_rows()
            display_rows(rows)
        elif choice == "6":
            print("Exiting CSV editor.")
            break
        else:
            print("Invalid option. Please choose a number from 1 to 6.")


if __name__ == "__main__":
    main_menu()
