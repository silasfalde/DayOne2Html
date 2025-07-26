import os
import sys
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from tqdm import tqdm
import pandas as pd

load_dotenv("config.env")

API_URL = "https://router.huggingface.co/v1/chat/completions"
API_KEY = os.environ.get("API_KEY")
assert API_KEY is not None, "API_KEY env variable not set!"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def get_summary_title(text) -> str | None:
    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Create a short, few-word, simple title for the following journal entry: "
                + text,
            },
        ],
        "model": "seacorn/llama3.1-8b-reasoning-summarizer:featherless-ai",
        "max_tokens": 20,
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    try:
        summary = response.json()["choices"][0]["message"]["content"]

        if summary.find(":"):
            summary = summary.split(":")[0].strip()

        summary = "".join(e for e in summary if e.isalnum() or e.isspace())
        summary = summary.title()

        return summary.strip()
    except Exception:
        print("Exception:", response.json())
        return None


def get_next_file_path(directory, base_filename):
    """
    Given a directory and base_filename, returns a unique file path.
    """
    name, ext = os.path.splitext(base_filename)
    counter = 1
    candidate = os.path.join(directory, base_filename)
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{name}-{counter}{ext}")
        counter += 1
    return candidate


def generate_filename(entry: dict) -> str:
    date = entry["creationDate"].split("T")[0]
    year, month, day = date.split("-")[:3]
    target_filename = f"{year}-{month}-{day}"

    if "text" in entry:
        title = get_summary_title(entry["text"])
        if title:
            target_filename += f" {title}"

    target_filename = target_filename + ".html"
    return target_filename


def main(journal_name="Journal", out_dir="out"):
    journal_data_path = os.path.join(out_dir, journal_name + ".csv")
    journal_data = pd.read_csv(journal_data_path)
    to_rename = journal_data[journal_data["renamed"] == False]["html_path"].tolist()
    print(f"Found {len(to_rename)} entries to rename.")

    for entry_path in tqdm(to_rename, desc="Renaming entries"):
        text = BeautifulSoup(
            open(entry_path, "r", encoding="utf-8"), "html.parser"
        ).get_text()
        title = get_summary_title(text)

        if not title:
            break

        new_filename = title + ".html"
        new_filename = get_next_file_path(
            os.path.join(out_dir, journal_name), new_filename
        )
        os.rename(entry_path, new_filename)
        journal_data.loc[journal_data["html_path"] == entry_path, "html_path"] = (
            new_filename
        )
        journal_data.loc[journal_data["html_path"] == new_filename, "renamed"] = True

    journal_data.to_csv(journal_data_path, index=False)


if __name__ == "__main__":
    main(sys.argv[1])
