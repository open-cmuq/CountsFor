"""
This script is used to export the database tables to CSV files. for easy viewing and editing.
"""
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

# Load database URL (Default: SQLite)
DATABASE_URL = "sqlite:///backend/database/gened_db.sqlite"

# Define the tables you want to export
tables = [
    "department",
    "course",
    "offering",
    "requirement",
    "audit",
    "countsfor",
    "prereqs",
    "course_instructor",
    "enrollment"
]

def export_tables_to_csv(output_dir="data/csv_exports", database_url=None):
    """
    Export all database tables to CSV files

    Args:
        output_dir (str): Directory where CSV files will be saved
        database_url (str): Database URL to connect to (defaults to module-level DATABASE_URL)

    Returns:
        dict: A dictionary with table names as keys and export status as values
    """
    # Use the provided database_url or default to the module-level constant
    db_url = database_url or DATABASE_URL

    # Create the engine
    engine = create_engine(db_url)

    # Create a directory to save the CSV files
    os.makedirs(output_dir, exist_ok=True)

    results = {}

    # Export each table to a CSV file
    for table in tables:
        try:
            # Read the table into a DataFrame
            df = pd.read_sql_table(table, con=engine)

            # Define the output file path
            output_file = os.path.join(output_dir, f"{table}.csv")

            # Write the DataFrame to a CSV file
            df.to_csv(output_file, index=False)
            print(f"Exported {table} to {output_file}")
            results[table] = "success"

        except SQLAlchemyError as e:
            print(f"Database error while exporting {table}: {e}")
            results[table] = f"database_error: {str(e)}"
        except FileNotFoundError as e:
            print(f"File not found error while exporting {table}: {e}")
            results[table] = f"file_not_found: {str(e)}"
        except pd.errors.EmptyDataError as e:
            print(f"Empty data error while exporting {table}: {e}")
            results[table] = f"empty_data: {str(e)}"
        except Exception as e: # pylint: disable=broad-exception-caught
            print(f"Unexpected error while exporting {table}: {e}")
            results[table] = f"unexpected_error: {str(e)}"

    return results

if __name__ == "__main__":
    export_tables_to_csv()
