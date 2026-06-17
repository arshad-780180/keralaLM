import os
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

# Step 1: Base Inputs
url = input("🔗 Paste the Malayalam Wikipedia URL: ").strip()
category = (
    input("📂 Enter base category (technology / science / geography / history): ")
    .strip()
    .lower()
)

# Step 2: Dynamic Subfolder Management
subfolder_choice = (
    input("📁 Do you need a subfolder inside this category? (y/n): ")
    .strip()
    .lower()
)

if subfolder_choice == "y":
    subfolder_name = (
        input("✍️ Enter name of the subfolder: ").strip().lower().replace(" ", "_")
    )
    output_dir = os.path.join("data", "wikipedia", category, subfolder_name)
else:
    subfolder_name = "none"
    output_dir = os.path.join("data", "wikipedia", category)

os.makedirs(output_dir, exist_ok=True)

# Step 3: English file tracking label
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
                if subfolder_choice == "y":
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