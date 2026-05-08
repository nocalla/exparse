import logging
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable

import pandas as pd

from conflict_parse import parse_conflicts
from direction_parse import parse_directions
from dosing_set_parse import parse_dosing_sets
from order_string_parse import parse_order_strings
from outside_location_parse import parse_locations
from solarwinds_parse import parse_solarwinds
from unit_of_measure_parse import parse_units

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParserConfig:
    filename_fragment: str
    parser: Callable[[Path], pd.DataFrame]


SEARCH_FILENAMES: dict[str, ParserConfig] = {
    "dosing_sets": ParserConfig("dosing", parse_dosing_sets),
    "order_strings": ParserConfig("order_string", parse_order_strings),
    "directions": ParserConfig("direction", parse_directions),
    "outside_locations": ParserConfig("location", parse_locations),
    "conflicts": ParserConfig("conflict", parse_conflicts),
    "unit_of_measure": ParserConfig("unit", parse_units),
    "solarwinds": ParserConfig("solarwinds", parse_solarwinds),
}


def get_file_list(
    search_params: dict[str, ParserConfig],
) -> dict[str, tuple[Path, Callable[[Path], pd.DataFrame]]]:
    files = [f for f in Path("input").iterdir() if f.is_file()]
    file_mapping: dict[str, tuple[Path, Callable[[Path], pd.DataFrame]]] = {}

    for key, config in search_params.items():
        matching_file = next(
            (f for f in files if config.filename_fragment in f.stem), None
        )
        if matching_file:
            file_mapping[key] = (matching_file, config.parser)

    return file_mapping


def parse_file(
    category: str,
    file_path: Path,
    func: Callable[[Path], pd.DataFrame],
) -> pd.DataFrame:
    log.info("Parsing %s dictionary...", category)
    return func(file=file_path)


def export_dfs_to_excel(dfs: list[tuple[str, pd.DataFrame]]) -> None:
    sheet_names = "_".join(pairing[0] for pairing in dfs)
    filename = f"{sheet_names}_dict_export.xlsx"
    output_path = Path("output", filename)
    with pd.ExcelWriter(output_path) as writer:
        for sheetname, df in dfs:
            df.to_excel(writer, sheet_name=sheetname)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    Path("input").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)

    file_dict = get_file_list(SEARCH_FILENAMES)
    log.debug("Files found: %s", file_dict)
    dataframes: list[tuple[str, pd.DataFrame]] = []
    for category, (file_path, func) in file_dict.items():
        try:
            dataframes.append((category, parse_file(category, file_path, func)))
        except Exception:
            log.exception("Failed to parse %s — skipping", category)

    export_dfs_to_excel(dataframes)


if __name__ == "__main__":
    main()
    log.info("Done!")
