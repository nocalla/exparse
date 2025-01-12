import re
from pathlib import Path

import pandas as pd
import xlwings as xw


def file_to_dataframe(
    file: Path, headings: list[str], id:str, replace: list[tuple[str, str]]
):
    # Regex patterns to match headers and blank lines
    COMMON_CLEANUP_REGEX = [
        (r"^\s*\n", ""),
        (r"\*LIVE\* .*\n.*\n.*", ""),
        (r"\*LSTD\* .*\n.*\n.*", ""),
        (r"\*TEST\* .*\n.*\n.*", ""),
        (r"\*TSTD\* .*\n.*\n.*", ""),
    ]
    # Read the text file
    with open(file, "r") as f:
        data = f.read()

    # cleanup file
    patterns = COMMON_CLEANUP_REGEX + replace
    data = regex_substitution(data, patterns)
    debug_test_current_data(data)
    # convert to dataframe
    df = text_data_to_dataframe(text=data, id=id, headings=headings)
    return df


def regex_substitution(text: str, substitutions: list[tuple]) -> str:
    # Apply all match subtitutions to the text
    for regex, replacement in substitutions:
        text = re.sub(regex, replacement, text, flags=re.MULTILINE)
    return text


def text_data_to_dataframe(
    text: str, id: str, headings: list[str]
) -> pd.DataFrame:
    """
    Converts a string into a dataframe through use of a regex to split the string into chunks based on an ID and then by applying a regex search using a list of headings contained within the text.

    :param text: string to convert to dataframe
    :type text: str
    :param id: ID string to group the data by
    :type id: str
    :param headings: list of headings contained within each group
    :type headings: list[str]
    :return: dataframe containing each ID as a row and the list of headings as columns
    :rtype: pd.DataFrame
    """
    # split the data into groups based on ID
    groups = re.split(f"(?={id})", text)

    heading_pattern = "|".join(re.escape(key) for key in headings)
    all_entries = list()
    for group in groups:
        # capture data to a dict using a list of headings
        split_data = re.split(r"(" + heading_pattern + r")", group)
        string_dict = dict()
        current_key = None
        for part in split_data:
            if part in headings:
                current_key = part
            elif current_key:
                string_dict[current_key] = part.strip()
                current_key = None
        all_entries.append(string_dict)

    df = pd.DataFrame(all_entries)
    df.dropna(how="all", axis="index", inplace=True)
    return df


def debug_test_current_data(text: str, error_flag: bool = False) -> None:
    """
    Debugging function to test the current state of a string being worked on
    by writing it to a text file.

    :param data: the string to be written to the file
    :type data: str
    :param error_flag: whether or not to raise an error on calling the function
    :type error_flag: bool
    :raises NotImplementedError: Error to bring the run to a halt.
    """
    test_path = Path("output", "test.txt")
    with open(test_path, "w") as f:
        f.write(text)
    if error_flag:
        raise NotImplementedError


def debug_test_dataframe(
    df: pd.DataFrame | pd.Series,
    error_flag: bool = False,
    format: str = "xlsx",
    show_index: bool = False,
) -> None:
    """
    Debugging function to test the current state of a dataframe being worked on
    by writing it to an Excel file.

    :param data: the dataframe or series to be written to the file
    :type data: str
    :param error_flag: whether or not to raise an error on calling the function
    :type error_flag: bool
    :param format: the file extension to use - xlsx or csv
    :type format: str
    :raises NotImplementedError: Error to bring the run to a halt.
    """
    test_path = Path("output", f"test.{format}")

    close_excel_workbook_if_open(test_path)
    df.to_excel(test_path, engine="xlsxwriter", index=show_index)

    open_file_in_excel(test_path)
    if error_flag:
        raise NotImplementedError


def open_file_in_excel(filepath: Path) -> None:
    """
    Open up Excel file

    :param filepath: Path to the file to check
    :type filepath: Path
    """
    # xw.App(visible=True)
    xw.Book(filepath)


def close_excel_workbook_if_open(filepath: Path) -> None:
    """
    Close an open Excel document if it is open.

    :param filepath: Path to the file to check.
    :type filepath: Path
    """
    # Try to connect to a running Excel instance
    try:
        app = xw.apps.active
    except AttributeError:
        # Excel not running
        return

    # Check if there is an instance of Excel
    if not app:
        return

    # Resolve the file path for robust comparison
    target_path = filepath.resolve()

    # Iterate through open workbooks
    for wb in app.books:
        try:
            open_path = Path(wb.fullname).resolve()
            if target_path == open_path:
                # close workbook
                wb.close()
                return
        except OSError:
            # If a workbook has no associated file, skip it
            continue
