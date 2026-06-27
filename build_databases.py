# this script reads the three bangladesh csv files from the local data folder
# and converts each one into its own sqlite database
# run this once before running the agent, it creates the db files inside the data folder

import os
import re
import sqlite3
import pandas as pd

# this is where the downloaded csv files live and where the generated db files will be saved
DATA_DIR = "data"


def clean_column_name(column_name):
    # this function turns messy csv headers into clean sql friendly column names
    # example: "Hospital Name " becomes "hospital_name"
    name = column_name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    if name == "":
        name = "unnamed_column"
    return name


def build_sqlite_from_csv(csv_path, db_name, table_name):
    # this function loads one local csv file and writes it into a sqlite db as one table
    print(f"loading data for {table_name} from {csv_path}")
    df = pd.read_csv(csv_path)

    # clean up every column name so sql queries do not break on spaces or symbols
    df.columns = [clean_column_name(col) for col in df.columns]

    # drop fully empty rows since they add no value to the database
    df = df.dropna(how="all")

    # try to convert numeric looking text columns into real numeric types
    # this matters for columns like rating or bed counts where we want REAL or INTEGER not TEXT
    for col in df.columns:
        if df[col].dtype == object:
            converted = pd.to_numeric(df[col], errors="coerce")
            # only switch the column to numeric if most values actually converted successfully
            if converted.notna().sum() >= 0.8 * df[col].notna().sum() and df[col].notna().sum() > 0:
                df[col] = converted

    db_path = os.path.join(DATA_DIR, db_name)
    connection = sqlite3.connect(db_path)
    df.to_sql(table_name, connection, if_exists="replace", index=False)
    connection.close()

    print(f"saved {len(df)} rows into {db_path} as table '{table_name}'")
    print(f"columns: {list(df.columns)}")
    print()


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # institutional information of bangladesh, this is a school college and madrasha registry
    build_sqlite_from_csv(
        csv_path=os.path.join(DATA_DIR, "Institutional-Information-of-Bangladesh-Data.csv"),
        db_name="institutions.db",
        table_name="institutions",
    )

    # all bangladeshi hospitals, this is really a health facility directory
    # it includes hospitals, clinics, health offices, and other DGHS facilities
    build_sqlite_from_csv(
        csv_path=os.path.join(DATA_DIR, "All-Bangladesh-Hosptals-Data.csv"),
        db_name="hospitals.db",
        table_name="hospitals",
    )

    # bangladeshi restaurant data, sourced from google maps place listings
    build_sqlite_from_csv(
        csv_path=os.path.join(DATA_DIR, "Bangladeshi-Restaurant-Data.csv"),
        db_name="restaurants.db",
        table_name="restaurants",
    )

    print("all three databases were built successfully inside the data folder")


if __name__ == "__main__":
    main()
