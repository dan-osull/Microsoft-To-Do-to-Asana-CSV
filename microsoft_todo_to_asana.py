import json
import logging
import os
from typing import Optional

import pandas as pd
from pathvalidate import sanitize_filename  # pyright: ignore reportPrivateImportUsage
from bs4 import BeautifulSoup

JSON_FILENAME = "microsoft_todo.json"
OUTPUT_FOLDER = "asana_data"
CSV_ROW_TARGET = 1900
CSV_ROW_ERROR = 2000


def format_date(date_time: str) -> str:
    """
    In:
    2019-05-05
    or
    2020-05-06T07:06:35.869

    Out: 05/05/2019
    """
    new_date = date_time[:10].split("-")
    # US date format
    new_date = new_date[1], new_date[2], new_date[0]
    return "/".join(new_date)


def get_filename_prefix(title: str) -> str:
    return str(sanitize_filename(title)).strip() + "_"


def convert_task(task: dict, subtask_of: Optional[str] = None) -> dict:
    """
    Convert individual task in Microsoft To Do format to Asana format

    https://asana.com/guide/help/api/csv-importer
    """
    asana_task = {
        "Name": task["title"],
        # "Completed": task["completed"],
        "_position": task["position"],
    }

    if task["completed"]:
        # Set "Section" based on completed status
        asana_task["Section"] = "Done"
    else:
        asana_task["Section"] = "To do"

    if subtask_of:
        asana_task["Subtask of"] = subtask_of
        # Completed subtasks get name prepended with DONE
        if task["completed"]:
            asana_task["Name"] = "DONE " + asana_task["Name"]
    else:
        # Guarantee None value for sorting
        asana_task["Subtask of"] = None
    try:
        asana_task["Description"] = (
            BeautifulSoup(task["note"], features="html.parser").get_text().strip()
        )
    except KeyError:
        # Guarantee creation of column
        asana_task["Description"] = None
    # Please re-title "Start Date" column header to "Created" and move it after (to the right of) Description column,
    # so it will be added to Description text in this relationship.
    asana_task["Created"] = format_date(task["created_at"]["date_time"])
    try:
        asana_task["Due Date"] = format_date(task["due_date"]["date_time"])
    except KeyError:
        pass
    try:
        asana_task["Completed"] = format_date(task["completed_at"]["date_time"])
    except KeyError:
        pass

    return asana_task


def todo_to_asana(list_info: dict, all_todo_data: dict, output_dir: str) -> None:
    """
    Process one To Do list of tasks

    Generates a list of dict and passes to "sort_and_write_csv" function.

    Breaks longer lists into chunks if necessary.
    """
    logging.info(f'{list_info["title"]=}')
    filename_prefix = get_filename_prefix(list_info["title"])
    asana_data: list[dict] = []
    file_number = 0

    # Matching tasks
    tasks = [
        task for task in all_todo_data["tasks"] if task["list_id"] == list_info["id"]
    ]
    for task in tasks:
        if len(asana_data) > CSV_ROW_ERROR:
            raise Exception(
                f"CSV file exceeded {CSV_ROW_ERROR} rows! Reduce CSV_ROW_TARGET."
            )
        elif len(asana_data) > CSV_ROW_TARGET:
            # Large list should be split into multiple CSVs
            logging.info(f"Large To Do list. Writing out current progress...")
            sort_and_write_csv(asana_data, file_number, filename_prefix, output_dir)
            file_number += 1
            # New list
            asana_data = []

        asana_data.append(convert_task(task))
        # Find steps / sub-tasks
        steps = [
            step for step in all_todo_data["steps"] if step["task_id"] == task["id"]
        ]
        for step in steps:
            asana_data.append(convert_task(step, subtask_of=task["title"]))

    # Write final CSV (long lists) or only CSV (short lists)
    sort_and_write_csv(asana_data, file_number, filename_prefix, output_dir)


def sort_and_write_csv(
    asana_data: list[dict], file_number: int, filename_prefix: str, output_dir: str
) -> None:
    if len(asana_data) == 0:
        # XML Data Link list contains no data
        return

    logging.info(f"Writing CSV... {len(asana_data)=}")
    csv_filename = filename_prefix + str(file_number) + ".csv"
    logging.info(f"{csv_filename=}")
    csv_path = os.path.join(output_dir, csv_filename)
    # Main tasks first, sorted by position, followed by subtasks, sorted by position
    df = pd.DataFrame(asana_data).sort_values(
        ["Subtask of", "_position"],
        # Position sorting needs False. Default: True.
        ascending=[True, False],
        # Puts subtasks at end. Default: last.
        na_position="first",
    )
    # Drop position column
    del df["_position"]
    # Export to CSV
    df.to_csv(csv_path, index=False, encoding="UTF-8")


def main():
    logging.basicConfig(level=logging.INFO)
    script_dir = os.path.abspath(os.path.dirname(__file__))
    output_dir = os.path.join(script_dir, OUTPUT_FOLDER)
    json_path = os.path.join(script_dir, JSON_FILENAME)

    with open(json_path, encoding="utf8") as file:
        all_todo_data = json.load(file)

    try:
        os.mkdir(output_dir)
    except FileExistsError:
        logging.warning("Directory already exists")

    for list_info in all_todo_data["lists"]:
        todo_to_asana(list_info, all_todo_data, output_dir)


if __name__ == "__main__":
    main()
