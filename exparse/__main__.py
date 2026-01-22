from pathlib import Path

import pandas as pd

from conflict_parse import parse_conflicts
from direction_parse import parse_directions
from dosing_set_parse import parse_dosing_sets
from order_string_parse import parse_order_strings
from outside_location_parse import parse_locations
from solarwinds_parse import parse_solarwinds
from unit_of_measure_parse import parse_units

SEARCH_FILENAMES = {
    "dosing_sets": ["dosing", parse_dosing_sets],
    "order_strings": ["order_string", parse_order_strings],
    "directions": ["direction", parse_directions],
    "outside_locations": ["location", parse_locations],
    "conflicts": ["conflict", parse_conflicts],
    "unit_of_measure": ["unit", parse_units],
    "solarwinds": ["solarwinds", parse_solarwinds],
}


def get_file_list(search_params: dict[str, list]) -> dict[str, tuple]:
    # Get files from the "input" folder
    files = [f for f in Path("input").iterdir() if f.is_file()]
    file_mapping = dict()

    # Loop through the search dictionary
    for key, params in search_params.items():
        # Find the file that contains the relevant search value
        matching_file = next((f for f in files if params[0] in f.stem), None)

        # If a matching file is found, map the key to the file path and relevant function
        if matching_file:
            file_mapping[key] = (matching_file, params[1])

    return file_mapping


def parse_file(category: str, file_path: Path, func) -> pd.DataFrame | None:
    print(f"Parsing {category} dictionary...")
    if func == None:
        return pd.DataFrame()
    return func(file=file_path)


def export_dfs_to_excel(dfs: list[tuple]) -> None:
    filename = f"{"_".join([pairing[0] for pairing in dfs])}_dict_export.xlsx"
    output_path = Path("output", filename)
    with pd.ExcelWriter(output_path) as writer:
        for sheetname, df in dfs:
            df.to_excel(writer, sheet_name=sheetname)


def main() -> None:
    # TODO - create input/output folders if needed
    file_dict = get_file_list(SEARCH_FILENAMES)
    print(f"Parsing files: {file_dict}")  # debug
    dataframes = list()
    for category in file_dict.keys():
        dataframes.append(
            (category, parse_file(category, *file_dict[category]))
        )

    export_dfs_to_excel(dataframes)


if __name__ == "__main__":
    main()
    print("Done!")
