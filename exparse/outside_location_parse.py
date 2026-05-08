from pathlib import Path

import pandas as pd

from common_functions import file_to_dataframe


def parse_locations(file: Path) -> pd.DataFrame:
    HEADINGS = [
        "Mnemonic",
        "Name",
        "Active",
        "Address",
        "Phone",
        "Address2",
        "Direct Address",
        "Town/City",
        "Fax",
        "Type",
        "County",
        "FaxAttention",
        "Eircode",
        "Default Send Cover Page",
        "Contact",
        "Performing Loc Exception",
        "Internal Referral Location",
        "External Identifier",
        "NCPDP Identifier",
        "Open 24 hours",
        "Accepts eRx",
        "EPCS",
        "OV Source",
        "OV Source ID",
        "Mail Order",
        "Payer ID",
        "Email",
        "Web Address",
        "Description",
    ]
    patterns = [
        (r"Address 2", "Address2"),
        (r"Fax Attention", "FaxAttention"),
    ]
    df = file_to_dataframe(
        file=file, record_id="Mnemonic", headings=HEADINGS, replace=patterns
    ).fillna("MISSING")

    df = df[df["Mnemonic"].str.contains("PHA.")]

    return df
