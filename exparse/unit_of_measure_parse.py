from pathlib import Path

import pandas as pd

from common_functions import (
    parse_fixed_width_table_from_text,
    regex_substitution,
)


# TODO - no work done on this at all!
def parse_units(file: Path) -> pd.DataFrame:
    HEADINGS = [
        "Mnemonic",
        "Active",
        "Name",
        "Equivalent Unit",
        "Conversion Factor",
        "Code Type",
        "Code",
        "Name",
    ]
    patterns = [
        (r".*Equivalent   Conversion", ""),
    ]
    table_text = file.read_text()
    table_text = regex_substitution(table_text, patterns)

    df = parse_fixed_width_table_from_text(
        table_text=table_text,
        account_for_linebreaks=False,
    )
    df.columns = HEADINGS
    # get rid of rows that are just headers
    df = df[df["Mnemonic"] != "Mnemonic"]
    df.replace("", pd.NA, inplace=True)
    df.ffill(inplace=True)

    return df
