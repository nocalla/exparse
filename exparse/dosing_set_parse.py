from pathlib import Path

import pandas as pd



def parse_dosing_sets(file: Path) -> pd.DataFrame:

    headers = [
        "Dosing Set",
        "PHA Site",
        "Drug",
        "IV Fluid String",
        "IV Fluid",
        "String Text",
        "Smart Pump Alias",
        "Dosing Amount",
        "Dosing Unit",
        "Dosing per Factor",
        "Weight or BSA Formula",
        "Round To",
        "Frequency",
        "Route",
        "Schedule",
        "Total Doses",
        "Min/Max Dose Error",
        "Min Dose",
        "Min Dose Unit",
        "Max Dose",
        "Max Dose Unit",
        "From Age",
        "Thru Age",
        "From Weight or BSA",
        "Thru Weight or BSA",
        "Order String Group",
        "Order Type",
        "Infuse Over Protocol",
        "Infuse Over Unit",
        "Ordered Rate",
        "Rate",
        "Label Comments",
        "Dose Instructions",
        "Precautions",
        "Creatinine Clearance",
    ]

    print("Reading file")
    with open(file) as f:
        lines = f.read()
    # Get dosing set name on the same row as the header
    lines = lines.replace("Dosing Set\n", "Dosing Set ")

    # rename unit based headers to avoid confusion
    lines = lines.replace("Dose Unit", "Dosage Unit")
    # remove commas
    lines = lines.replace(",", "")
    temp_headers = list()
    for header in headers:
        temp_headers.append(header.replace("Dose Unit", "Dosage Unit"))
    headers = temp_headers

    # TODO - get the dosing group into a column - no idea how

    print("Filtering relevant rows")
    filter_char = "~"
    unspaced_headers = list()
    for header in headers:
        # take all the spaces out of the column headers where they occur in the file
        header_unspaced = header.replace(" ", "")
        # create a list of unspaced headers for use later
        unspaced_headers.append(header_unspaced)
        # mark each row with a character for filtering
        lines = lines.replace(header, f"{filter_char}{header_unspaced}")

    # convert the string to a list
    rows = lines.split("\n")
    # filter rows using the filter_char to just get rows with the desired headings
    filtered_rows = [
        row.strip()[1:] for row in rows if row.strip().startswith(filter_char)
    ]
    # convert the rows back into a string
    new_lines = "\n".join(filtered_rows)

    # split into dosing set chunks
    set_delimiter = "SET DELIMITER"
    new_lines = new_lines.replace(unspaced_headers[0], set_delimiter)
    chunk_list = new_lines.split(set_delimiter)
    dosing_set_list = list()
    header_tuple = tuple(unspaced_headers)
    for chunk in chunk_list:
        # re-add the DosingSet header
        chunk = unspaced_headers[0] + chunk
        # split chunk string into a list
        chunk_items = chunk.split("\n")
        set_dict = dict()
        # if the item starts with a header, add to a dict under that header as a key
        for item in chunk_items:
            if any(
                item.startswith(match := header) for header in unspaced_headers
            ):
                set_dict[match] = item[len(match) :]

        dosing_set_list.append(set_dict)

    # convert to dataframe
    df = pd.DataFrame(dosing_set_list)

    # strip leading and trailing whitespace from all columns
    for column in df.columns:
        df[column] = df[column].str.strip()

    # split columns where needed
    df[["DosingSet", "SetName"]] = df["DosingSet"].str.split(
        " ", n=1, expand=True
    )
    df[["DrugMnemonic", "Drug"]] = df["Drug"].str.split(
        " - ", n=1, expand=True
    )

    # strip leading and trailing whitespace from all columns again
    for column in df.columns:
        df[column] = df[column].str.strip()

    # convert numeric strings to numeric datatypes
    # NB: this will break in a future version of pandas
    df = df.apply(
        pd.to_numeric,
        errors="ignore",
    )
    # print(df.dtypes)
    # drop rows and columns where all values are missing
    df.dropna(axis="index", how="all", inplace=True)
    df.dropna(axis="columns", how="all", inplace=True)

    # print(df.head())  # debug

    return df


# if __name__ == "__main__":
#     parse_dosing_sets(FILE)
