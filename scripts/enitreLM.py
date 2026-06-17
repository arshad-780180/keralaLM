import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

# Step 1: Base Inputs
url = input("🔗 Paste the Malayalam Wikipedia URL: ").strip()

data_root = "data"
os.makedirs(data_root, exist_ok=True)


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
os.makedirs(output_dir, exist_ok=True)

subfolder_name = choose_or_create_folder(output_dir, "subfolder", allow_none=True)
if subfolder_name:
    output_dir = os.path.join(output_dir, subfolder_name)
    os.makedirs(output_dir, exist_ok=True)
    subsubfolder_name = choose_or_create_folder(output_dir, "sub-subfolder", allow_none=True)
    if subsubfolder_name:
        output_dir = os.path.join(output_dir, subsubfolder_name)
        os.makedirs(output_dir, exist_ok=True)
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

            words = len(clean_text.split())

            # --- AUTOMATED CSV METADATA LOGGING WITH EXCEL FIX ---
            csv_dir = "metadata"
            csv_path = os.path.join(csv_dir, "sources.csv")
            os.makedirs(csv_dir, exist_ok=True)

            csv_exists = os.path.isfile(csv_path)

            csv_row = f"{filename},Malayalam Wikipedia,{category.capitalize()},{subfolder_name},2026-06-17,{words},{url}\n"

            with open(csv_path, "a", encoding="utf-8") as csv_file:
                if not csv_exists:
                    # '\ufeff' is the magic BOM signature that forces Excel to show Malayalam correctly
                    csv_file.write(
                        "\ufefffilename,source,category,subcategory,date,word_count,link\n"
                    )
                csv_file.write(csv_row)
            # -----------------------------------------------------

            print("-" * 60)
            print(f"🎉 Success! Target location verified and file saved.")
            print(f"📍 Text File: {output_path} ({words} words)")
            print(f"✅ Metadata: Automatically logged entry inside {csv_path}!")
            print("-" * 60)
        else:
            print("❌ Error: Could not extract layout content.")
    else:
        print(f"❌ Wikipedia request failed with Status Code: {response.status_code}")

except Exception as e:
    print(f"❌ Error running the smart pipeline: {e}")