import re
from pathlib import Path

import pandas as pd
import xlwings as xw


def file_to_dataframe(
    file: Path,
    headings: list[str],
    record_id: str,
    replace: list[tuple[str, str]],
) -> pd.DataFrame:
    with open(file, "r") as f:
        data = f.read()

    data = regex_substitution(data, replace)
    df = text_data_to_dataframe(text=data, record_id=record_id, headings=headings)
    return df


def regex_substitution(text: str, substitutions: list[tuple[str, str]]) -> str:
    common_cleanup_regex = [
        # Meditech uses \f (form feed, 0x0C) as a page separator, often mid-line
        # before the *LSTD*/*LIVE* header. Normalise to \n so the header patterns
        # below can match at the start of a line.
        (r"\f", "\n"),
        # Strip other illegal control characters (openpyxl rejects 0x00-0x08, 0x0B, 0x0E-0x1F)
        (r"[\x00-\x08\x0B\x0E-\x1F]", ""),
        (r"^\s*\n", ""),
        (r"[^\x00-\x7F]+", ""),
        (r"^-+\n", ""),
        (r"^\s*\*LIVE\*.*\n.*\n.*", ""),
        (r"^\s*\*LSTD\*.*\n.*\n.*", ""),
        (r"^\s*\*TEST\*.*\n.*\n.*", ""),
        (r"^\s*\*TSTD\*.*\n.*\n.*", ""),
        (r"DATE:.*\n", ""),
        (r"USER:.*\n", ""),
    ]
    substitutions = common_cleanup_regex + substitutions
    for regex, replacement in substitutions:
        text = re.sub(regex, replacement, text, flags=re.MULTILINE)
    return text


def build_heading_pattern(headings: list[str]) -> str:
    return "|".join(re.escape(h) for h in headings)


def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(lambda col: col.str.strip() if col.dtype == "object" else col)


def text_data_to_dataframe(
    text: str, record_id: str, headings: list[str]
) -> pd.DataFrame:
    """
    Converts a string into a dataframe through use of a regex to split the string into chunks based on an ID and then by applying a regex search using a list of headings contained within the text.

    :param text: string to convert to dataframe
    :type text: str
    :param record_id: ID string to group the data by
    :type record_id: str
    :param headings: list of headings contained within each group
    :type headings: list[str]
    :return: dataframe containing each ID as a row and the list of headings as columns
    :rtype: pd.DataFrame
    """
    groups = re.split(f"(?={record_id})", text)

    heading_pattern = build_heading_pattern(headings)
    all_entries = []
    for group in groups:
        split_data = re.split(r"(" + heading_pattern + r")", group)
        string_dict = {}
        current_key = None
        for part in split_data:
            if part in headings:
                current_key = part
            elif current_key:
                string_dict[current_key] = part.strip()
                current_key = None
        all_entries.append(string_dict)

    df = pd.DataFrame(all_entries)
    df = df.dropna(how="all", axis="index")
    return df


def debug_test_current_data(text: str, error_flag: bool = False) -> None:
    """
    Debugging function to test the current state of a string being worked on
    by writing it to a text file.

    :param text: the string to be written to the file
    :type text: str
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

    :param df: the dataframe or series to be written to the file
    :type df: pd.DataFrame | pd.Series
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
    xw.Book(filepath)


def close_excel_workbook_if_open(filepath: Path) -> None:
    """
    Close an open Excel document if it is open.

    :param filepath: Path to the file to check.
    :type filepath: Path
    """
    try:
        app = xw.apps.active
    except AttributeError:
        return

    if not app:
        return

    target_path = filepath.resolve()

    for wb in app.books:
        try:
            open_path = Path(wb.fullname).resolve()
            if target_path == open_path:
                wb.close()
                return
        except OSError:
            continue


def infer_table_structure(
    table_text: str,
) -> tuple[list[str], list[str], list[int]]:
    """
    Infer the column headers, content lines, and column boundaries from a string containing a table.

    :param table_text: String containing the table to parse.
    :type table_text: str
    :return: Tuple containing the headers, content lines, and column boundaries.
    :rtype: tuple[list[str], list[str], list[int]]
    """
    lines = table_text.strip().split("\n")
    header_line = lines[0]
    content_lines = lines[1:]
    longest_line_length = max(len(line) for line in lines)

    # Match words with optional spaces between them, followed by at least 2 whitespaces or the last heading
    pattern = r"\S+(?: \S+)*(?=\s{2,})|\S+(?: \S+)*$"

    headings = re.finditer(pattern, header_line)

    column_starts = [match.start() for match in headings]

    column_boundaries = column_starts + [longest_line_length]

    headers = [
        header_line[start:end].strip()
        for start, end in zip(column_boundaries[:-1], column_boundaries[1:])
    ]

    return headers, content_lines, column_boundaries


def process_dataframe_linebreaks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Account for linebreaks within cells by merging values in all columns up to the previous row if the first column is empty.

    :param df: Dataframe to process
    :type df: pd.DataFrame
    :return: Processed dataframe
    :rtype: pd.DataFrame
    """
    first_col_name = df.columns[0]
    df[first_col_name] = df[first_col_name].replace("", pd.NA).ffill()
    for col in df.columns[1:]:
        df[col] = df.groupby(first_col_name)[col].transform(
            lambda x: " ".join(x.dropna())
        )
    df = df.dropna(subset=[df.columns[0]])
    df.reset_index(drop=True, inplace=True)
    return df


def parse_fixed_width_table_from_text(
    table_text: str,
    account_for_linebreaks: bool = True,
    exclude_columns: list[str] | None = None,
) -> pd.DataFrame:
    """
    Parse a fixed width table from text to a dataframe.

    :param table_text: String containing the table to parse.
    :param account_for_linebreaks: whether or not to account for linebreaks within cells, defaults to True
    :type account_for_linebreaks: bool, optional
    :param exclude_columns: list of columns to ignore from table, defaults to None
    :type exclude_columns: list[str] | None, optional
    :return: Dataframe containing the parsed table
    :rtype: pd.DataFrame
    """
    if exclude_columns is None:
        exclude_columns = []

    headers, content_lines, column_boundaries = infer_table_structure(table_text)

    rows = []
    for line in content_lines:
        row = [
            line[start:end].strip()
            for start, end in zip(
                column_boundaries[:-1], column_boundaries[1:]
            )
        ]
        rows.append(row)

    df = pd.DataFrame(rows, columns=headers)
    df.drop(labels=exclude_columns, axis=1, errors="ignore", inplace=True)
    if account_for_linebreaks:
        df = process_dataframe_linebreaks(df)
    return df
