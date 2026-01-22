from pathlib import Path

import pandas as pd

from common_functions import file_to_dataframe


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

    patterns = [
        (r"^Facility.*", ""),
        (r"^\s*\n", ""),
        ("Day Schedule Display", "DayScheduleDisplay"),
        (r"(Mnemonic.*?)(\s+)Name", r"\1\2Direction Name"),
        (r"(Location.*?)(\s+)Name", r"\1\2Equiv Name"),
    ]
    df = file_to_dataframe(
        file=file, id="Mnemonic", headings=HEADINGS, replace=patterns
    )
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
        # remove duplicate rows
        facility_df.drop_duplicates(
            subset=["Mnemonic", "Application"], inplace=True
        )
        # add this facility's data to the list of facilities
        facilities_df = pd.concat([facilities_df, facility_df])

    # remove facility detail column
    facilities_df.drop(columns=facilities, inplace=True)
    df.drop(columns=facilities, inplace=True)
    # merge facility specific data back to main direction data
    df = pd.merge(df, facilities_df, how="left", on="Mnemonic")

    # remove leading and trailing whitespace for entire dataframe
    for col in df.columns:
        df[col] = df[col].str.strip(" ")
    return df
