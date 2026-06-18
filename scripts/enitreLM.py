import os
import re
import json
import shutil
import urllib.parse
import requests
from bs4 import BeautifulSoup

# Step 1: Base Inputs
url = input("🔗 Paste the Malayalam Wikipedia URL: ").strip()

data_root = "data"
def ensure_dir(path, record=True):
    existed = os.path.exists(path)
    os.makedirs(path, exist_ok=True)
    created = not existed and os.path.exists(path)
    if created and record:
        push_action({"type": "create_dir", "path": path})
    return created

ensure_dir(data_root, record=False)

# Actions stack for undo support
metadata_dir = "metadata"
ensure_dir(metadata_dir, record=False)
actions_file = os.path.join(metadata_dir, "actions_stack.json")


def load_actions():
    if os.path.exists(actions_file):
        try:
            with open(actions_file, "r", encoding="utf-8") as af:
                return json.load(af)
        except Exception:
            return []
    return []


def save_actions(actions):
    with open(actions_file, "w", encoding="utf-8") as af:
        json.dump(actions, af, ensure_ascii=False, indent=2)



def push_action(action):
    actions = load_actions()
    actions.append(action)
    save_actions(actions)


def pop_action():
    actions = load_actions()
    if not actions:
        return None
    action = actions.pop()
    save_actions(actions)
    return action


def undo_action(action):
    t = action.get("type")
    if t == "create_dir":
        p = action.get("path")
        if os.path.isdir(p):
            try:
                # remove only if empty
                if not os.listdir(p):
                    os.rmdir(p)
                    print(f"Undo: removed empty directory {p}")
                else:
                    ans = input(f"Directory {p} is not empty. Remove recursively? (y/N): ").strip().lower()
                    if ans == "y":
                        shutil.rmtree(p)
                        print(f"Undo: recursively removed {p}")
                    else:
                        print(f"Skipped removing non-empty directory {p}")
            except Exception as e:
                print(f"Failed to remove directory {p}: {e}")
        else:
            print(f"Directory {p} already absent")
    elif t == "create_file":
        p = action.get("path")
        if os.path.isfile(p):
            try:
                os.remove(p)
                print(f"Undo: removed file {p}")
            except Exception as e:
                print(f"Failed to remove file {p}: {e}")
        else:
            print(f"File {p} already absent")
    elif t == "append_csv":
        p = action.get("path")
        row = action.get("row")
        csv_created = action.get("csv_created", False)
        if os.path.isfile(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                # remove last matching row
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].strip() == row.strip():
                        lines.pop(i)
                        break
                # if CSV was created by this action and now only header or empty, remove file
                if csv_created:
                    try:
                        os.remove(p)
                        print(f"Undo: removed CSV file {p}")
                    except Exception as e:
                        print(f"Failed to remove CSV file {p}: {e}")
                else:
                    with open(p, "w", encoding="utf-8") as f:
                        f.writelines(lines)
                    print(f"Undo: removed CSV row from {p}")
            except Exception as e:
                print(f"Failed to undo CSV append in {p}: {e}")
        else:
            print(f"CSV file {p} absent")
    else:
        print(f"Unknown action type: {t}")


def do_undo(n=1):
    for _ in range(n):
        action = pop_action()
        if not action:
            print("No more actions to undo.")
            return
        undo_action(action)


def load_csv_rows(csv_path):
    if not os.path.isfile(csv_path):
        return []
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    if not lines:
        return []
    header = lines[0].lstrip("\ufeff").split(",")
    rows = [dict(zip(header, line.split(","))) for line in lines[1:]]
    return rows


def write_csv_rows(csv_path, rows):
    if not rows:
        return
    header = ["filename", "source", "category", "subcategory", "date", "word_count", "link"]
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("\ufeff" + ",".join(header) + "\n")
        for row in rows:
            f.write(",".join(str(row.get(col, "")) for col in header) + "\n")


def undo_last_csv(csv_path):
    actions = load_actions()
    for i in range(len(actions) - 1, -1, -1):
        if actions[i].get("type") == "append_csv":
            action = actions.pop(i)
            save_actions(actions)
            undo_action(action)
            return
    print("No CSV append action found to undo.")


def prompt_csv_value(prompt_text, default=""):
    if default:
        value = input(f"{prompt_text} [{default}]: ").strip()
        return value if value else default
    return input(f"{prompt_text}: ").strip()


def add_csv_entry(csv_path):
    ensure_dir(os.path.dirname(csv_path), record=False)
    csv_exists = os.path.isfile(csv_path)
    if not csv_exists:
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("\ufefffilename,source,category,subcategory,date,word_count,link\n")

    row = {
        "filename": prompt_csv_value("Enter filename", ""),
        "source": prompt_csv_value("Enter source", "Malayalam Wikipedia"),
        "category": prompt_csv_value("Enter category", ""),
        "subcategory": prompt_csv_value("Enter subcategory", "none"),
        "date": prompt_csv_value("Enter date", "2026-06-17"),
        "word_count": prompt_csv_value("Enter word count", "0"),
        "link": prompt_csv_value("Enter link", ""),
    }
    with open(csv_path, "a", encoding="utf-8") as f:
        f.write(",".join(str(row[col]) for col in ["filename", "source", "category", "subcategory", "date", "word_count", "link"]) + "\n")
    push_action({"type": "append_csv", "path": csv_path, "row": ",".join(str(row[col]) for col in ["filename", "source", "category", "subcategory", "date", "word_count", "link"]) + "\n", "csv_created": not csv_exists})
    print("CSV entry added.")


def remove_csv_entry(csv_path):
    rows = load_csv_rows(csv_path)
    if not rows:
        print("No CSV rows available to remove.")
        return
    print("\nCSV rows:")
    for idx, row in enumerate(rows, start=1):
        print(f"{idx}. {row.get('filename', '')}, {row.get('category', '')}, {row.get('subcategory', '')}, {row.get('date', '')}")
    choice = input("Enter the row number to remove, or press Enter to cancel: ").strip()
    if not choice.isdigit():
        print("Canceling removal.")
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(rows):
        print("Invalid row number.")
        return
    removed = rows.pop(idx)
    write_csv_rows(csv_path, rows)
    print(f"Removed CSV row: {removed}")


def normalize_folder_name(name):
    return name.strip().lower().replace(" ", "_")


def choose_or_create_folder(parent_dir, folder_type, allow_none=False):
    existing = sorted(
        [
            name
            for name in os.listdir(parent_dir)
            if os.path.isdir(os.path.join(parent_dir, name))
        ]
    )

    if existing:
        print(f"\nSelect an existing {folder_type} in '{parent_dir}':")
        for idx, name in enumerate(existing, start=1):
            print(f"  {idx}. {name}")
        print(f"  {len(existing)+1}. Create a new {folder_type}")
        if allow_none:
            print(f"  {len(existing)+2}. No {folder_type}")

        while True:
            choice = input(
                f"Enter a number (1-{len(existing)+1}{'/' + str(len(existing)+2) if allow_none else ''}): "
            ).strip()
            if choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(existing):
                    return existing[choice_num - 1]
                if choice_num == len(existing) + 1:
                    break
                if allow_none and choice_num == len(existing) + 2:
                    return None
            print("Invalid choice. Please enter a valid number.")

    else:
        print(f"\nNo existing {folder_type}s found in '{parent_dir}'.")

    while True:
        name = input(f"Enter the name of the {folder_type}: ").strip()
        if name:
            return normalize_folder_name(name)
        print("Please enter a valid name.")


category = choose_or_create_folder(data_root, "folder")
output_dir = os.path.join(data_root, category)
ensure_dir(output_dir)

subfolder_name = choose_or_create_folder(output_dir, "subfolder", allow_none=True)
if subfolder_name:
    output_dir = os.path.join(output_dir, subfolder_name)
    ensure_dir(output_dir)
    subsubfolder_name = choose_or_create_folder(output_dir, "sub-subfolder", allow_none=True)
    if subsubfolder_name:
        output_dir = os.path.join(output_dir, subsubfolder_name)
        ensure_dir(output_dir)
        subfolder_name = subsubfolder_name
else:
    subfolder_name = "none"

# Step 2: English file tracking label
english_label = (
    input("🔤 Enter short English name for the file (e.g., bicycle_history): ")
    .strip()
    .lower()
    .replace(" ", "_")
)
filename = f"{english_label}.txt"
output_path = os.path.join(output_dir, filename)

print("\nProcessing your link and verifying directory path...")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        content_div = soup.find("div", class_="mw-parser-output")

        if content_div:
            paragraphs = content_div.find_all("p")
            article_text = "\n\n".join(
                [p.get_text() for p in paragraphs if p.get_text().strip() != ""]
            )

            clean_text = re.sub(r"\[\d+\]", "", article_text)

            raw_title = url.split("/")[-1]
            malayalam_title = urllib.parse.unquote(raw_title).replace("_", " ")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"TITLE: {malayalam_title}\n")
                f.write(f"CATEGORY: {category.upper()}\n")
                # FIXED: Check if subfolder_name is not 'none' instead of using subfolder_choice
                if subfolder_name != "none":
                    f.write(f"SUBCATEGORY: {subfolder_name.upper()}\n")
                f.write("=" * 30 + "\n\n")
                f.write(clean_text)

            # record created file for undo
            push_action({"type": "create_file", "path": output_path})

            words = len(clean_text.split())

            # --- AUTOMATED CSV METADATA LOGGING WITH EXCEL FIX ---
            csv_dir = "metadata"
            csv_path = os.path.join(csv_dir, "sources.csv")
            ensure_dir(csv_dir, record=False)

            csv_exists = os.path.isfile(csv_path)

            csv_row = f"{filename},Malayalam Wikipedia,{category.capitalize()},{subfolder_name},2026-06-17,{words},{url}\n"

            with open(csv_path, "a", encoding="utf-8") as csv_file:
                if not csv_exists:
                    # '\ufeff' is the magic BOM signature that forces Excel to show Malayalam correctly
                    csv_file.write(
                        "\ufefffilename,source,category,subcategory,date,word_count,link\n"
                    )
                csv_file.write(csv_row)
            # record appended metadata row for undo
            push_action({"type": "append_csv", "path": csv_path, "row": csv_row, "csv_created": (not csv_exists)})
            # -----------------------------------------------------

            print("-" * 60)
            print(f"🎉 Success! Target location verified and file saved.")
            print(f"📍 Text File: {output_path} ({words} words)")
            print(f"✅ Metadata: Automatically logged entry inside {csv_path}!")
            print("-" * 60)

            while True:
                print("\nChoose what to do next:")
                print("1. Undo last step (CSV)")
                print("2. Remove all operations")
                print("3. Keep all changes and finish")
                choice = input("Enter 1-3: ").strip()
                if choice == "1":
                    undo_last_csv(csv_path)
                elif choice == "2":
                    current_actions = load_actions()
                    if current_actions:
                        do_undo(len(current_actions))
                    print("All operations have been removed.")
                    break
                elif choice == "3":
                    print("Finished. Keeping changes.")
                    break
                else:
                    print("Invalid choice. Please enter a number from 1 to 3.")
        else:
            print("❌ Error: Could not extract layout content.")
    else:
        print(f"❌ Wikipedia request failed with Status Code: {response.status_code}")

except Exception as e:
    print(f"❌ Error running the smart pipeline: {e}")