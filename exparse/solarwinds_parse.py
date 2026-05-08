from pathlib import Path

import pandas as pd


def parse_solarwinds(file: Path) -> pd.DataFrame:
    return pd.read_csv(file, sep="\t")
