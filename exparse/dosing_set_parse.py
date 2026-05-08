import logging
from pathlib import Path

import pandas as pd

from common_functions import strip_whitespace

log = logging.getLogger(__name__)

FILTER_CHAR = "~"
SET_DELIMITER = "SET DELIMITER"


def parse_dosing_sets(file: Path) -> pd.DataFrame:
    headers = [
        "Dosing Set",
        "PHA Site",
        "Drug",
        "IV Fluid String",
        "IV Fluid",
        "String Text",
        "Smart Pump Alias",
        "Dosing Amount",
        "Dosing Unit",
        "Dosing per Factor",
        "Weight or BSA Formula",
        "Round To",
        "Frequency",
        "Route",
        "Schedule",
        "Total Doses",
        "Min/Max Dose Error",
        "Min Dose",
        "Min Dose Unit",
        "Max Dose",
        "Max Dose Unit",
        "From Age",
        "Thru Age",
        "From Weight or BSA",
        "Thru Weight or BSA",
        "Order String Group",
        "Order Type",
        "Infuse Over Protocol",
        "Infuse Over Unit",
        "Ordered Rate",
        "Rate",
        "Label Comments",
        "Dose Instructions",
        "Precautions",
        "Creatinine Clearance",
    ]

    log.debug("Reading file")
    with open(file) as f:
        lines = f.read()
    # Get dosing set name on the same row as the header
    lines = lines.replace("Dosing Set\n", "Dosing Set ")

    lines = lines.replace("Dose Unit", "Dosage Unit")
    lines = lines.replace(",", "")
    headers = [h.replace("Dose Unit", "Dosage Unit") for h in headers]

    # TODO - get the dosing group into a column - no idea how

    log.debug("Filtering relevant rows")
    unspaced_headers = []
    for header in headers:
        header_unspaced = header.replace(" ", "")
        unspaced_headers.append(header_unspaced)
        lines = lines.replace(header, f"{FILTER_CHAR}{header_unspaced}")

    rows = lines.split("\n")
    filtered_rows = [
        row.strip()[1:] for row in rows if row.strip().startswith(FILTER_CHAR)
    ]
    new_lines = "\n".join(filtered_rows)

    new_lines = new_lines.replace(unspaced_headers[0], SET_DELIMITER)
    chunk_list = new_lines.split(SET_DELIMITER)
    dosing_set_list = []
    for chunk in chunk_list:
        # re-add the DosingSet header
        chunk = unspaced_headers[0] + chunk
        # split chunk string into a list
        chunk_items = chunk.split("\n")
        set_dict = dict()
        # if the item starts with a header, add to a dict under that header as a key
        for item in chunk_items:
            if any(
                item.startswith(match := header) for header in unspaced_headers
            ):
                set_dict[match] = item[len(match) :]

        dosing_set_list.append(set_dict)

    df = pd.DataFrame(dosing_set_list)
    df = strip_whitespace(df)

    df[["DosingSet", "SetName"]] = df["DosingSet"].str.split(" ", n=1, expand=True)
    df[["DrugMnemonic", "Drug"]] = df["Drug"].str.split(" - ", n=1, expand=True)

    df = strip_whitespace(df)

    for col in df.columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        df[col] = converted.where(converted.notna(), df[col])
    df.dropna(axis="index", how="all", inplace=True)
    df.dropna(axis="columns", how="all", inplace=True)

    return df
