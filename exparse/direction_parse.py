import re
from pathlib import Path

import pandas as pd

from .common_functions import regex_substitution, test_current_data


def parse_directions(file: Path) -> pd.DataFrame:
    HEADINGS = [
        "Directions",
        "Mnemonic",
        "Direction Name",
        "Active",
        "Use as Equivalent",
        "Day Schedule",
        "DayScheduleDisplay",
        "Average Doses Per Day",
        "Rank",
        "Default Schedule for Meds",
        "Number of Hours to First Dose",
        "Location",
        "Equivalent Direction",
        "Equiv Name",
        "Outpatient Label Comment",
        "FSV Identifier",
        "FSV Name",
        "MPAC",
        "MPAD",
        "MPC",
        "MPD",
    ]

    # Read the text file
    with open(file, "r") as f:
        data = f.read()

    # cleanup file
    # Regex patterns to match headers and blank lines
    patterns = [
        (r"\*TEST\* .*\n.*\n.*", ""),
        (r"^Facility.*", ""),
        (r"^\s*\n", ""),
        ("Day Schedule Display", "DayScheduleDisplay"),
        (r"(Mnemonic.*?)(\s+)Name", r"\1\2Direction Name"),
        (r"(Location.*?)(\s+)Name", r"\1\2Equiv Name"),
    ]

    data = regex_substitution(data, patterns)
    test_current_data(data)  # debug
    # split the data into directions groups
    groups = re.split(r"(?=Mnemonic)", data)

    heading_pattern = "|".join(re.escape(key) for key in HEADINGS)
    all_indications = list()
    for group in groups:
        # capture data to a dict using a list of headings
        split_data = re.split(r"(" + heading_pattern + r")", group)
        string_dict = dict()
        current_key = None
        for part in split_data:
            if part in HEADINGS:
                current_key = part
            elif current_key:
                string_dict[current_key] = part.strip()
                current_key = None
        all_indications.append(string_dict)

    df = pd.DataFrame(all_indications)
    df.dropna(how="all", axis="index", inplace=True)

    facilities = ["MPAC", "MPAD", "MPC", "MPD"]
    facility_headers = [
        # "Facility",
        # "Active",
        "Application",
        "Use Day Schedule from Start Time",
        "Time",
        "Special Time",
    ]

    facility_col_regex = r"\s*(?P<Application>.{13})(?P<UseDayScheduleFromStartTime>.{34})(?P<Time>.{5})(?P<SpecialTime>.*)"

    facilities_df = pd.DataFrame()
    for facility in facilities:
        # create separate facility dataframe
        facility_df = df[["Mnemonic", facility]].copy()
        # Add facility column
        facility_df["Facility"] = facility
        # get Active column
        facility_df[["Facility Active", facility]] = facility_df[
            facility
        ].str.split(" ", n=1, expand=True)
        # split into separate row for each new line and pad the string to length
        facility_df[facility] = facility_df[facility].str.split("\n")
        facility_df = facility_df.explode(facility)
        # pad strings to same length
        facility_df[facility] = (
            facility_df[facility].astype(str).str.ljust(100)
        )

        facility_df[facility_headers] = (
            facility_df[facility].astype(str).str.extract(facility_col_regex)
        )

        facilities_df = pd.concat([facilities_df, facility_df])
    # remove facility detail column
    df.drop(columns=facilities, inplace=True)
    facilities_df.drop(columns=facilities, inplace=True)
    df = pd.merge(df, facilities_df, how="outer", on="Mnemonic")

    # remove leading and trailing whitespace for entire dataframe
    for col in df.columns:
        df[col] = df[col].str.strip(" ")
    return df
