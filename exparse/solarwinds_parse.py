from pathlib import Path

import pandas as pd


def parse_solarwinds(file: Path) -> pd.DataFrame:
    df = pd.read_csv(file, sep="\t")

    return df
