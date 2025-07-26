"""
Convert Day One JSON Files to HTML.
"""

import json
import sys
import markdown
import os
from typing import List
import datetime
import subprocess
from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd


def set_creation_date(file_path, dt):
    formatted_date = dt.strftime("%m/%d/%Y %H:%M:%S")
    subprocess.run(["SetFile", "-d", formatted_date, file_path])


def create_output_directory(out_dir: str) -> None:
    if os.path.exists(out_dir):
        subprocess.run(["rm", "-rf", out_dir])
    os.makedirs(out_dir)


def write_html_file(entry, out_path: str) -> None:
    template_start = BeautifulSoup("<html><head></head><body>", "html.parser")
    template_end = BeautifulSoup("</body></html>", "html.parser")

    with open(out_path, "w+") as outfile:
        outfile.write(str(template_start))

        if "text" in entry:
            soup = BeautifulSoup(markdown.markdown(entry["text"]), "html.parser")
            outfile.write(str(soup))

        outfile.write(str(template_end))


def main(input_json_path: str) -> None:
    out_dir = "out"
    journal_name = os.path.splitext(os.path.basename(input_json_path))[0]
    entries: List[dict] = json.loads(open(input_json_path).read())

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    html_out_dir = os.path.join(out_dir, journal_name)
    create_output_directory(html_out_dir)
    entry_data = []

    for entry in tqdm(entries["entries"], desc="Converting entries to HTML", unit="entry"):  # type: ignore
        date, time = entry["creationDate"].split("T")
        hours, minutes, seconds = time.replace("Z", "").split(":")
        out_path = os.path.join(html_out_dir, entry["uuid"] + ".html")
        assert not os.path.exists(out_path), f"File {out_path} already exists!"
        write_html_file(entry, out_path)

        create_date = datetime.datetime(
            int(date.split("-")[0]),
            int(date.split("-")[1]),
            int(date.split("-")[2]),
            int(hours),
            int(minutes),
            int(seconds),
        )
        set_creation_date(out_path, create_date)

        entry_data.append(
            {
                "uuid": entry["uuid"],
                "html_path": out_path,
                "renamed": False,
            }
        )

    pd.DataFrame(entry_data).to_csv(
        os.path.join(out_dir, f"{journal_name}_entries.csv"), index=False
    )


if __name__ == "__main__":
    main(sys.argv[1])
