from pathlib import Path

import pandas as pd

from .common_functions import file_to_dataframe


def parse_locations(file: Path) -> pd.DataFrame:
    HEADINGS = [
        "Mnemonic",
        "Name",
        "Active",
        "Address",
        "Phone",
        "Addres2",  # renamed Address 2
        "Direct Address",
        "Town/City",
        "Fax",
        "Type",
        "County",
        "FaAttention",  # renamed Fax Attention
        "Eircode",
        "Default Send Cover Page",
        "Contact",
        "Performing Loc Exception",
        "Internal Referral Location",
        "External Identifier",
        "NCPDP Identifier",
        "Open 24 hours",
        "Accepts eRx",
        "EPCS" "OV Source",
        "OV Source ID",
        "Mail Order",
        "Payer ID",
        "Email",
        "Web Address",
        "Description",
    ]
    patterns = [
        (r"Address 2", "Addres2"),
        (r"Fax Attention", "FaAttention"),
    ]
    df = file_to_dataframe(
        file=file, id="Mnemonic", headings=HEADINGS, replace=patterns
    ).fillna("MISSING")

    # filter for just pharmacy entries
    df = df[df["Mnemonic"].str.contains("PHA.")]

    # debug_test_dataframe(df, error_flag=True)

    return df
