from pathlib import Path

import pandas as pd

from exparse.common_functions import (
    infer_table_structure,
    parse_table_from_text,
)

from .common_functions import debug_test_dataframe, file_to_dataframe


def parse_conflicts(file: Path) -> pd.DataFrame:
    heading_groups = [
        [
            "Main",
            [
                "Mnemonic",
                "Name",
                "Valid For",
            ],
        ],
        [
            "Dose Checking",
            [
                "Use Dose Range Checking",
                "PRN Checks",  # TODO - check if this is a heading or an actual setting
                "Dose Range Check Requires Override",
                "Restrict PRN Dose Checks",
                "Restrict Frequency Checks",
                "Allowed Low Rounding Percent",
                "Allowed Max Rounding Percent",
                "Restrict General Warnings",
                "Restrict Dose Type",
                "Restrict Dose Range Check to Dose Type",
            ],
        ],
        [
            "Drug Screening",
            [
                "Drug Screening Conflicts",
                "Drug Screening Warnings",
                "Problem Status to Include in Screening",
                "Ignore Pharmacogenomic results for 'Consider Testing'",
            ],
        ],
        [
            "Preferences",
            [
                "Allow Interaction Auto-Override",  # TODO need to fix for visit & discharge meds
                "Check Against DC'd Orders",
                "DC'd Within How Many Days",
                "Check Interactions Against Home Medications",
                "Check Duplicates Against Home Medications",
                "Stop Checking Home Medications After LOS Days",
                ### Inpt/OBS Visits - check the allocation of sections here
                "Exclude Medications on Other Visits from Interaction Checks",
                "Exclude Medications on Other Visits from Duplicate Checks",
                "Exclude Medications on Other Visits after LOS Days",
                "Exclude Acute Medications on Same Visit from Interaction Checks",
                "Exclude Acute Medications on Same Visit from Duplicate Checks",
                ### Allergy Checking
                "Check Supplemental Allergens",
                "Hide Comments When Not Required",
                ### immunisation
                "Check Immunization Conflicts",
                "Immunization Conflict Requires Override",
                "Check Immunization Schedule Conflicts",
                "Immunization Schedule Conflict Requires Override",
                "Check Interactions for Not Given",
            ],
        ],
    ]
    regex_replacements = [
        ("Preferences", ""),
        ("Immunizations", ""),
        ("Dose Checking", ""),
        ("Inpt/OBS Visits", ""),
        ("Allergy Checking", ""),
        (
            "Ignore Pharmacogenomics",
            "Ignore Pharmacogenomic",
        ),
        ("Pharmacogenomics", ""),
        (
            r"PRN Checks\n Require Override",
            "Dose Range Check Requires Override",
        ),
        (
            r"Restrict Frequency Checks\n Require Override",
            "Restrict Frequency Checks\n Dose Range Check Requires Override",
        ),
        (
            r"(Stop Checking Home Medications After LOS Days\s+)(\d+)?(\s+)Require Override",
            r"\1\2\3Immunization Conflict Requires Override",
        ),
        (
            r"(Hide Comments When Not Required\s+)(\d+|Yes|No)?(\s+)Require Override",
            r"\1\2\3Immunization Schedule Conflict Requires Override",
        ),
        (
            r"Restrict Dose Type \(Inpatient\)\s+Restrict Dose Type \(Outpatient\)",
            "Restrict Dose Type",
        ),
        (r"(Visit Medications\s+)(\d+)?(\s+)Discharge Home Medications", ""),
        (
            r"(Problem Status to Include in Screening\n)(\s+)(Acute)",
            lambda m: f"{m.group(1)}Status{' ' * (len(m.group(2)) - len('Status'))}{m.group(3)}",
        ),
        (
            r"(Schedule)(\s+)(Dose Type)(\s+)(Default)(\s+)(Dose Type)(\s+)(Default)",
            r"\1\2\3\4\5\6Outpatient \7\8Outpatient \9",
        ),
    ]

    headings_to_extract = [
        item for _, group in heading_groups for item in group
    ]
    heading_parents = {
        item: parent for parent, group in heading_groups for item in group
    }

    df = file_to_dataframe(
        file=file,
        headings=headings_to_extract,
        id="Mnemonic",
        replace=regex_replacements,
    )

    # set row index to Mnemonic
    df.set_index("Mnemonic", inplace=True)
    # Extract Active status from Name column
    df["Active"] = df["Name"].str.extract(
        r"(?i)active\s+(Yes|No)$", expand=True
    )
    # Remove the "active Yes/No" part from the original "Name" column
    df["Name"] = (
        df["Name"]
        .str.replace(r"(?i)active\s+(Yes|No)$", "", regex=True)
        .str.strip()
    )

    df, new_column_parents = parse_subtables(
        df,
        [
            ("Drug Screening Conflicts", []),
            ("Drug Screening Warnings", []),
            ("Problem Status to Include in Screening", []),
            (
                "Restrict Dose Type",
                ["Outpatient Dose Type", "Outpatient Default"],
            ),
            ("Restrict Dose Type", ["Dose Type", "Default"]),
        ],
    )

    # add additional headings that were created during runtime
    heading_parents.update(
        [
            ("Active", "Main"),
        ]
        + new_column_parents
    )

    # Create a MultiIndex from heading_parents, checking if the heading is in use
    multi_index = pd.MultiIndex.from_tuples(
        [(heading_parents[column], column) for column in df.columns],
        names=["Section", "Parameter"],
    )
    # set columns to use multi-index
    df.columns = multi_index
    # sort columns by Section using a predefined order
    section_order = [
        "Main",
        "Dose Checking",
        "Restrict Dose Type",
        "Drug Screening Conflicts",
        "Drug Screening Warnings",
        "Problem Status to Include in Screening",
        "Drug Screening",
        "Preferences",
    ]
    df = df.reindex(
        columns=pd.MultiIndex.from_tuples(
            sorted(df.columns, key=lambda x: section_order.index(x[0])),
            names=["Section", "Parameter"],
        )
    )
    # transpose dataframe
    df = df.T

    debug_test_dataframe(df, show_index=True)
    return df


def parse_subtables(
    df: pd.DataFrame, columns: list[tuple[str, list[str]]]
) -> tuple[pd.DataFrame, list[tuple[str, str]]]:
    """
    Examines subtables present in the specified columns and flattens them into the main DataFrame. Flattening is done by prefixing headings in each column with the value in column 1.

    :param df: Dataframe containing the main data
    :type df: pd.DataFrame
    :param columns: Columns containing subtables to be flattened and subcolumns to be omitted
    :type columns: list[str]
    :return: Tuple containing the updated DataFrame and a list pairings of new columns to their parent columns
    :rtype: tuple[pd.DataFrame, list[tuple[str, str]]]
    """
    # Initialize a list to store flattened data
    flattened_data = []
    new_parent_pairings = []
    cols_to_drop = []
    for _, row in df.iterrows():
        flattened_row = {df.index.name: row.name}
        for column, sub_cols_to_drop in columns:
            cols_to_drop.append(column)
            subtable_text = str(row[column])

            # Infer headers, content, and column boundaries
            headers, content_lines, column_boundaries = infer_table_structure(
                subtable_text
            )
            # Parse subtable into a DataFrame
            parsed_df = parse_table_from_text(
                headers=headers,
                content_lines=content_lines,
                column_boundaries=column_boundaries,
                exclude_columns=sub_cols_to_drop,
            )

            # Flatten the subtable into a single dictionary
            for _, sub_row in parsed_df.iterrows():
                for col in parsed_df.columns[1:]:
                    # Create a column name by combining first column label with the other headings
                    flattened_column_name = f"{sub_row.iloc[0]} - {col}"
                    flattened_row[flattened_column_name] = sub_row[col]
                    new_parent_pairings.append((flattened_column_name, column))

        flattened_data.append(flattened_row)

    # Create a DataFrame from the flattened data
    flattened_df = pd.DataFrame(flattened_data)

    # Merge the flattened DataFrame with the main DataFrame
    final_df = pd.merge(
        df.drop(columns=cols_to_drop),
        flattened_df.set_index(df.index.name),
        left_index=True,
        right_index=True,
    )
    return final_df, new_parent_pairings
