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


def display_rows(rows, show_link=False):
    if not rows:
        print("\nNo rows found in the CSV file.")
        return

    columns = HEADER if show_link else [col for col in HEADER if col != "link"]
    total_word_count = 0
    print("\nCurrent rows in sources.csv:")
    print("Index | " + " | ".join(columns))
    print("-" * (8 + len(columns) * 15))
    for idx, row in enumerate(rows, start=1):
        values = [row.get(col, "") for col in columns]
        try:
            total_word_count += int(row.get("word_count", "0"))
        except ValueError:
            pass
        print(f"{idx:>5} | " + " | ".join(values))

    print("-" * (8 + len(columns) * 15))
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
    if not rows:
        print("\nNo rows available to modify.")
        return

    while True:
        sel = input("Enter filename or row index to modify (or 'c' to cancel): ").strip()
        if sel.lower() == "c":
            return
        # index selection
        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(rows):
                row_index = idx
                break
            else:
                print("Invalid index. Try again.")
                continue

        # filename selection (exact match first)
        matches = [i for i, r in enumerate(rows) if r.get("filename", "") == sel]
        if not matches:
            # substring matches
            matches = [i for i, r in enumerate(rows) if sel in r.get("filename", "")]
        if not matches:
            print("No matching filename found. Try again.")
            continue
        if len(matches) == 1:
            row_index = matches[0]
        else:
            print("Multiple matches:")
            for m in matches:
                r = rows[m]
                print(f"{m+1}: {r.get('filename','')} | {r.get('category','')} | {r.get('subcategory','')}")
            pick = input("Enter the row number to modify from the list above: ").strip()
            if not pick.isdigit():
                print("Cancelled selection.")
                return
            row_index = int(pick) - 1
            if row_index not in matches:
                print("Selected index not in matches. Canceling.")
                return
        break

    # === FIXED HERE: Renamed 'selected' to 'row' to match downstream references ===
    row = rows[row_index]
    print("\nSelected row:")
    for key in HEADER:
        print(f"  {key}: {row.get(key, '')}")
        
    confirm = input("Modify this row? (y/n): ").strip().lower()
    if confirm != "y":
        print("Modification cancelled.")
        return

    # Let user pick which fields to modify from a menu
    while True:
        print("\nFields:")
        for idx, key in enumerate(HEADER, start=1):
            print(f"  {idx}. {key} (current: {row.get(key, '')})")
        print("  0. Done / Save changes")
        sel = input("Enter field numbers to modify (comma-separated), or 0 to finish: ").strip()
        if sel == "0" or sel.lower() == "done":
            break
        choices = [s.strip() for s in sel.split(",") if s.strip()]
        fields_to_modify = []
        for c in choices:
            if c.isdigit():
                n = int(c)
                if 1 <= n <= len(HEADER):
                    fields_to_modify.append(HEADER[n - 1])
                else:
                    print(f"Invalid field number: {c}")
            else:
                # allow entering field names directly
                if c in HEADER:
                    fields_to_modify.append(c)
                else:
                    print(f"Unknown field: {c}")

        if not fields_to_modify:
            print("No valid fields selected. Try again.")
            continue

        for key in fields_to_modify:
            is_required = key in REQUIRED_FIELDS
            default_value = row.get(key, "")
            new_val = prompt_value(f"{key}", default=default_value, allow_empty=(key not in REQUIRED_FIELDS), required=is_required)
            row[key] = new_val

    write_rows(rows)
    print("Row updated successfully.")


def delete_row():
    rows = read_rows()
    if not rows:
        print("\nNo rows are available to delete.")
        return

    while True:
        sel = input("Enter filename(s) or row index(es) to delete (comma-separated), or 'c' to cancel: ").strip()
        if sel.lower() == "c":
            return
        tokens = [token.strip() for token in sel.split(",") if token.strip()]
        if not tokens:
            continue

        selected_indices = []
        invalid = False
        for token in tokens:
            if token.isdigit():
                idx = int(token) - 1
                if 0 <= idx < len(rows):
                    selected_indices.append(idx)
                else:
                    print(f"Index out of range: {token}")
                    invalid = True
                    break
            else:
                exact = [i for i, r in enumerate(rows) if r.get("filename", "") == token]
                if len(exact) == 1:
                    selected_indices.append(exact[0])
                    continue
                substring = [i for i, r in enumerate(rows) if token in r.get("filename", "")]
                if len(substring) == 1:
                    selected_indices.append(substring[0])
                    continue
                if len(exact) > 1 or len(substring) > 1:
                    matches = exact or substring
                    print(f"Multiple matches for '{token}':")
                    for m in matches:
                        r = rows[m]
                        print(f"  {m+1}: {r.get('filename','')} | {r.get('category','')} | {r.get('subcategory','')}")
                    pick = input("Enter the row number to delete from the list above, or press Enter to skip: ").strip()
                    if pick.isdigit():
                        idx = int(pick) - 1
                        if idx in matches:
                            selected_indices.append(idx)
                        else:
                            print("Selected row not in matches. Skipping.")
                    else:
                        print("Skipping this token.")
                else:
                    print(f"No match found for '{token}'.")
                    invalid = True
                    break
        if invalid:
            continue
        if not selected_indices:
            print("No valid rows selected. Try again.")
            continue

        selected_indices = sorted(set(selected_indices), reverse=True)
        deleted_any = False
        for idx in selected_indices:
            row = rows[idx]
            confirm = input(f"Delete row {idx+1} (filename={row.get('filename','')})? (y/n): ").strip().lower()
            if confirm == "y":
                deleted = rows.pop(idx)
                print(f"Deleted: {deleted.get('filename')}")
                deleted_any = True
            else:
                print(f"Kept: {row.get('filename')}")
        if deleted_any:
            write_rows(rows)
        return


def find_file_in_workspace(filename, search_root="."):
    """Search workspace for a file with the given filename.

    Returns the first matching absolute path or None if not found.
    """
    for root, dirs, files in os.walk(search_root):
        if filename in files:
            return os.path.join(root, filename)
    return None


def check_csv_file_references():
    """Check each CSV row's `filename` value and allow user to keep or delete rows
    when the referenced file is missing under `data/` or exists elsewhere in the workspace.
    """
    rows = read_rows()
    if not rows:
        print("\nNo rows to check.")
        return

    changed = False
    i = 0
    extra_files_found = False
    while i < len(rows):
        row = rows[i]
        fname = row.get("filename", "").strip()
        if not fname:
            i += 1
            continue

        # Look for file under data/ first
        data_path = find_file_in_workspace(fname, search_root=CSV_DIR.replace('metadata', 'data'))
        if data_path:
            # Found under data — OK
            i += 1
            continue

        # Not found under data; search entire workspace
        found_any = find_file_in_workspace(fname, search_root=".")
        print("\nReference check for:", fname)
        if found_any:
            extra_files_found = True
            print(f"  Found in workspace at: {found_any} (not under data/)")
        else:
            print("  File not found anywhere in the workspace.")

        resp = input("  Keep this CSV row? (y = keep / n = delete) [y]: ").strip().lower()
        if resp == "n" or resp == "no":
            removed = rows.pop(i)
            changed = True
            print(f"  Deleted CSV row for filename: {removed.get('filename')}")
            # do not increment i, since rows shifted
        else:
            print("  Kept CSV row.")
            i += 1

    if changed:
        write_rows(rows)
        print("\nUpdated CSV saved after removals.")
    else:
        print("\nNo changes made to CSV.")

    if not extra_files_found:
        print("\nNo extra files found in workspace.")


def view_rows_selection():
    rows = read_rows()
    if not rows:
        print("\nNo rows available.")
        return

    while True:
        print("\nView options:")
        print("  1. View by index (single or comma-separated)")
        print("  2. View by filename or substring (comma-separated)")
        print("  3. View all rows")
        print("  4. Cancel")
        choice = input("Choose 1-4: ").strip()
        if choice == "1":
            show_link = input("Show link field? (y/n) [n]: ").strip().lower() == "y"
            sel = input("Enter index or comma-separated indices (e.g. 1,3,5): ").strip()
            if not sel:
                print("No input provided.")
                continue
            parts = [p.strip() for p in sel.split(",") if p.strip()]
            for p in parts:
                if not p.isdigit():
                    print(f"Invalid index: {p}")
                    continue
                idx = int(p) - 1
                if 0 <= idx < len(rows):
                    r = rows[idx]
                    print(f"\nRow {idx+1}:")
                    for key in HEADER:
                        if key == "link" and not show_link:
                            continue
                        print(f"  {key}: {r.get(key,'')}")
                else:
                    print(f"Index out of range: {p}")
            return
        if choice == "2":
            show_link = input("Show link field? (y/n) [n]: ").strip().lower() == "y"
            sel = input("Enter filename(s) or substrings, comma-separated: ").strip()
            if not sel:
                print("No input provided.")
                continue
            parts = [p.strip() for p in sel.split(",") if p.strip()]
            matched_any = False
            for name in parts:
                for i, r in enumerate(rows):
                    if r.get('filename','') == name or name in r.get('filename',''):
                        matched_any = True
                        print(f"\nRow {i+1}:")
                        for key in HEADER:
                            if key == "link" and not show_link:
                                continue
                            print(f"  {key}: {r.get(key,'')}")
            if not matched_any:
                print("No matches found.")
            return
        if choice == "3":
            show_link = input("Show link field? (y/n) [n]: ").strip().lower() == "y"
            display_rows(rows, show_link=show_link)
            return
        if choice == "4":
            return
        print("Invalid choice. Enter 1-4.")


def main_menu():
    ensure_csv_exists()
    while True:
        print("\nCSV Editor for metadata/sources.csv")
        print("1. View rows")
        print("2. Add row")
        print("3. Modify row")
        print("4. Delete row")
        print("5. Total word count")
        print("6. Check file references (keep/delete rows)")
        print("7. Exit")

        choice = input("Choose an option (or type 'exit' to quit): ").strip().lower()
        if choice == "1":
            view_rows_selection()
        elif choice == "2":
            add_row()
        elif choice == "3":
            modify_row()
        elif choice == "4":
            delete_row()
        elif choice == "5":
            rows = read_rows()
            total_word_count = 0
            for row in rows:
                try:
                    total_word_count += int(row.get("word_count", "0"))
                except Exception:
                    pass
            print(f"\nTotal word_count: {total_word_count}")
        elif choice == "6":
            check_csv_file_references()
        elif choice == "7" or choice == "exit" or choice == "quit":
            print("Exiting CSV editor.")
            break
        else:
            print("Invalid option. Please choose a number from 1 to 7, or type 'exit'.")


if __name__ == "__main__":
    main_menu()
