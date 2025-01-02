import re
from pathlib import Path

import pandas as pd

from .common_functions import regex_substitution


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
        (r"\*LIVE\* .*\n.*\n.*", ""),
        (r"^Facility.*", ""),
        (r"^\s*\n", ""),
        ("Day Schedule Display", "DayScheduleDisplay"),
        (r"(Mnemonic.*?)(\s+)Name", r"\1\2Direction Name"),
        (r"(Location.*?)(\s+)Name", r"\1\2Equiv Name"),
    ]

    data = regex_substitution(data, patterns)
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

    # facility_col_regex = r"\s*(?P<Application>.{13})(?P<UseDayScheduleFromStartTime>.{3})(?P<Time>.{5})(?P<SpecialTime>.*)"
    facility_col_regex = (
        r"^\s*(?P<Application>[A-Za-z.]+)?"  # Application is optional
        r"(?:\s+(?P<UseDayScheduleFromStartTime>Yes))?"  # UseDaySchedule is optional
        r"(?:\s+(?P<Time>[0-9]{2}:[0-9]{2}))?"  # Time is optional
        r"(?:\s+(?P<SpecialTime>.+))?$"  # SpecialTime is optional
    )

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
        # split into separate row for each new line
        facility_df[facility] = facility_df[facility].str.split("\n")
        facility_df = facility_df.explode(facility)
        # pad strings to same length
        facility_df[facility] = (
            facility_df[facility].astype(str).str.ljust(100)
        )
        # split into columns based on regex
        facility_df[facility_headers] = (
            # facility_df = (
            facility_df[facility]
            .astype(str)
            .str.extract(facility_col_regex)
        )
        # fill in blank applications
        facility_df["Application"] = facility_df["Application"].ffill()
        # fill NaN values in Time column
        facility_df["Time"] = facility_df["Time"].fillna("")
        # merge time values for each application
        facility_df["Time"] = facility_df.groupby(["Mnemonic", "Application"])[
            "Time"
        ].transform(lambda x: ", ".join(x))
        # remove facility detail column
        facility_df.drop(columns=facility, inplace=True)

        # add this facility's data to the list of facilities
        facilities_df = pd.concat([facilities_df, facility_df])

    # remove duplicate rows
    facilities_df.drop_duplicates(inplace=True)

    # merge facility specific data back to main direction data
    df = pd.merge(df, facilities_df, how="outer", on="Mnemonic")

    # remove leading and trailing whitespace for entire dataframe
    for col in df.columns:
        df[col] = df[col].str.strip(" ")
    return df
