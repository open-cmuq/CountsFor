"""
This script is used to export the database tables to CSV files. for easy viewing and editing.
"""
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy.orm import Session

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

# Define dummy Base if import fails to prevent further import errors elsewhere, though functionality will fail
class Base: pass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the models explicitly if Base.metadata.tables isn't reliable or desired
# Alternatively, rely on Base.metadata.tables which should be populated after model definition
# Example: table_models = { 'department': Department, 'course': Course, ... }

# Renamed db parameter to session for clarity
def export_tables_to_csv(session: Session = None, output_dir: str = None) -> dict:
    """
    Exports all tables defined in models.py (via Base.metadata) to CSV files.

    Args:
        session (Session, optional): Existing database session. If None, a new one is created.
        output_dir (str, optional): Directory to save CSV files. Defaults to '../../data/csv_exports'.

    Returns:
        dict: Status of export for each table ('success' or error message).
    """
    results = {}
    close_session_after = False
    if session is None:
        session = SessionLocal()
        close_session_after = True
        logging.info("Created new DB session for CSV export.")

    if output_dir is None:
        # Default output directory relative to this file's location
        output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/csv_exports"))

    logging.info(f"Exporting tables to CSV in directory: {output_dir}")

    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        if not hasattr(Base, 'metadata') or not Base.metadata.tables:
             logging.error("Base.metadata.tables is not populated. Cannot determine tables to export.")
             return {"error": "Metadata not found"}

        # Iterate through all tables defined in the metadata
        for table_name, table in Base.metadata.tables.items():
            csv_file_path = os.path.join(output_dir, f"{table_name}.csv")
            logging.debug(f"Attempting to export table '{table_name}' to '{csv_file_path}'")
            try:
                # Use pandas to read SQL table and write to CSV
                # Using the session's connection for transaction context
                df = pd.read_sql_table(table_name, con=session.connection())
                df.to_csv(csv_file_path, index=False, encoding='utf-8')
                results[table_name] = "success"
                logging.info(f"Successfully exported table '{table_name}' to {csv_file_path}")
            except SQLAlchemyError as e:
                error_msg = f"SQLAlchemyError exporting table {table_name}: {e}"
                logging.error(error_msg)
                results[table_name] = error_msg
            except IOError as e:
                error_msg = f"IOError writing CSV for table {table_name} to {csv_file_path}: {e}"
                logging.error(error_msg)
                results[table_name] = error_msg
            except Exception as e: # Catch other potential errors like pandas issues
                error_msg = f"Unexpected error exporting table {table_name}: {e}"
                logging.exception(error_msg) # Use exception for full traceback
                results[table_name] = error_msg

    except OSError as e:
         # Error during makedirs
         error_msg = f"OSError creating output directory {output_dir}: {e}"
         logging.error(error_msg)
         return {"error": error_msg}
    except Exception as e:
        # Catch-all for other unexpected errors during setup
        error_msg = f"Unexpected error during CSV export setup: {e}"
        logging.exception(error_msg)
        return {"error": error_msg}

    finally:
        if close_session_after and session:
            session.close()
            logging.info("Closed DB session created for CSV export.")

    return results

if __name__ == "__main__":
    export_tables_to_csv()
