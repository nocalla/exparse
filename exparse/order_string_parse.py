import re
from pathlib import Path

import pandas as pd

from common_functions import build_heading_pattern, regex_substitution, strip_whitespace


def parse_order_strings(file: Path) -> pd.DataFrame:
    HEADINGS = [
        "Group Mnemonic",
        "Group Active",
        "Group Name",
        "Group Type",
        "Index by Fluid",
        "Restrict to Order Type",
        "Orderable By",
        "OM Sets Only",
        "Dosing Group",
        "Dosing Set",
        "Om Alias",
        "Smart Pump Group Alias",
        "Order Type: ",
        "Description",
        "OM Display Name:",
        "Alternate Names:",
        "File Verified From:",
        "Fixed Total Volume",
        "Calculated Total Vol",
        "Ordered Rate",
        "Rate",
        "Duration",
        "Ordered Volume",
        "Total Volume",
        "Dose Units",
        "Route",
        "Site",
        "Frequency",
        "Scheduled",
        "Sch",
        "IV Fluid",
        "Additive IV",
        "Medication",
        "Ingredient",
        "Total Doses",
        "Total Dose",
        "Inventory",
        "PRN Level",
        "PRN Reason",
        "Infuse Volume",
        "PCA Bolus Dose",
        "Lockout",
        "PCA Max Dose",
        "Time Limit",
        "PCA Data",
        "Start Date",
        "Start Time",
        "Stop:",
        "Soft Stop",
        "Total Bags",
        "Total Volume to Infuse",
        "Fill Frequency",
        "Type",
        "Charge",
        "Order Doctor",
        "Address",
        "License Num",
        "Phone",
        "Fax",
        "Label Comment",
        "Rx Comment",
        "Locations Incl/Excl",
        "For Location",
        "Restrict to",
    ]

    # Read the text file
    with open(file, "r") as f:
        data = f.read()

    substitutions = [
        (r"DATE:.+PAGE.+\nUSER:.+\n-+\n", ""),  # Remove headers and footers
        (
            r"-{2,}|Index by Restrict to|Group\s+Active\s+Name\s+Type Fluid\s+Order Type",
            "",
        ),  # match lines with dashes or headers
        (r"^\s*\n", ""),  # remove empty lines
    ]
    cleaned_data = regex_substitution(data, substitutions)

    group_chunks = re.split(r"\n(?!\s)", cleaned_data)

    heading_pattern = build_heading_pattern(HEADINGS)
    all_order_strings = []
    for group in group_chunks:
        # get shared part of order strings
        common = "Group Mnemonic " + group[: group.find("1)")]
        # get order_strings from group
        order_strings = re.split(r"\d+\)\s*", group[group.find("1)") :])
        # add the common component to each group
        order_strings = [
            f"{common} Order Type: {s}" for s in order_strings if s != ""
        ]
        for order_string in order_strings:
            # capture data to a dict using a list of headings
            split_data = re.split(r"(" + heading_pattern + r")", order_string)
            string_dict = dict()
            current_key = None
            for part in split_data:
                if part in HEADINGS:
                    current_key = part
                elif current_key:
                    string_dict[current_key] = part.strip()
                    current_key = None
            all_order_strings.append(string_dict)

    df = pd.DataFrame(all_order_strings)
    df = strip_whitespace(df)
    # split order type
    df[["Order Type: ", "Description"]] = df["Order Type: "].str.split(
        " ", n=1, expand=True
    )
    df["Description"] = df["Description"].str.strip()
    # split group mnemonic column
    df[
        [
            "Group Mnemonic",
            "Group Type",
            "Index by Fluid",
            "Restrict to Order Type",
        ]
    ] = (
        df["Group Mnemonic"]
        .str.strip(" ")  # remove leading & trailing whitespace
        .replace(r"\s+", " ", regex=True)  # remove consecutive whitespace
        .str.rsplit(
            " ", n=3, expand=True
        )  # split using spaces from right side
    )

    # further splits to group mnemonic column to capture everything before/after " Y " and " N "
    df[["Group Mnemonic", "Group Active", "Group Name"]] = df[
        "Group Mnemonic"
    ].str.extract(r"^(.*)\s(Y|N)\s(.*)$")

    # comment fields: remove consecutive whitespace
    df["Label Comment"] = df["Label Comment"].replace(r"\s+", " ", regex=True)
    df["Rx Comment"] = df["Rx Comment"].replace(r"\s+", " ", regex=True)

    df.dropna(how="all", axis="columns", inplace=True)

    present_headings = [h for h in HEADINGS if h in df.columns]
    df = df[present_headings]  # reorder the columns

    return df
