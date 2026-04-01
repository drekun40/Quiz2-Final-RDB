import argparse
import csv
import sqlite3
from pathlib import Path
from typing import List, Sequence


def quote_identifier(name: str) -> str:
    """Quote SQL identifier to handle special characters"""
    return '"' + name.replace('"', '""') + '"'


def infer_sqlite_types(csv_path: Path, sample_size: int = 5000) -> List[str]:
    """Infer SQLite column types from CSV data"""
    with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)

        is_int = [True] * len(header)
        is_float = [True] * len(header)
        seen_non_empty = [False] * len(header)

        for i, row in enumerate(reader):
            if sample_size and i >= sample_size:
                break

            for idx, value in enumerate(row):
                value = value.strip()
                if value == "":
                    continue

                seen_non_empty[idx] = True

                if is_int[idx]:
                    try:
                        int(value)
                    except ValueError:
                        is_int[idx] = False

                if is_float[idx]:
                    try:
                        float(value)
                    except ValueError:
                        is_float[idx] = False

        types = []
        for idx in range(len(header)):
            if not seen_non_empty[idx]:
                types.append("TEXT")
            elif is_int[idx]:
                types.append("INTEGER")
            elif is_float[idx]:
                types.append("REAL")
            else:
                types.append("TEXT")

        return types


def create_table_from_csv(db_path: Path, csv_path: Path, table_name: str) -> None:
    """Create SQLite table from CSV file"""
    if not csv_path.exists():
        print(f"Warning: {csv_path} not found. Skipping table creation.")
        return

    types = infer_sqlite_types(csv_path)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        header = next(reader)

        # Create table
        columns = ", ".join(
            f"{quote_identifier(h)} {t}"
            for h, t in zip(header, types)
        )
        create_sql = f"CREATE TABLE IF NOT EXISTS {quote_identifier(table_name)} ({columns})"
        cursor.execute(create_sql)

        # Insert data
        placeholders = ", ".join(["?"] * len(header))
        insert_sql = (
            f"INSERT INTO {quote_identifier(table_name)} "
            f"({', '.join(quote_identifier(h) for h in header)}) "
            f"VALUES ({placeholders})"
        )

        for row in reader:
            try:
                cursor.execute(insert_sql, row)
            except sqlite3.Error as e:
                print(f"Error inserting row {row}: {e}")

    conn.commit()
    conn.close()
    print(f"Table '{table_name}' created successfully from {csv_path}")


def initialize_database(db_path: str = "erie_otters.db", data_dir: str = "./data") -> None:
    """Initialize the Erie Otters database from CSV files"""
    db_path = Path(db_path)
    data_dir = Path(data_dir)

    if db_path.exists():
        print(f"Database {db_path} already exists.")
        response = input("Overwrite? (y/n): ").strip().lower()
        if response != "y":
            print("Aborting.")
            return
        db_path.unlink()

    # Create tables from CSV files
    csv_files = {
        "erie_otters_stats.csv": "erie_otters_stats",
        "games_data.csv": "games",
        "player_stats.csv": "player_stats",
    }

    for csv_file, table_name in csv_files.items():
        csv_path = data_dir / csv_file
        create_table_from_csv(db_path, csv_path, table_name)

    print(f"\nDatabase initialized: {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Erie Otters database")
    parser.add_argument("--db", default="erie_otters.db", help="Database file path")
    parser.add_argument("--data-dir", default="./data", help="Data directory path")
    args = parser.parse_args()

    initialize_database(args.db, args.data_dir)
