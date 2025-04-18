"""
Utility functions for handling file uploads, extraction, and validation
in the data upload process.
"""

import os
import zipfile
import shutil
import logging
from pathlib import Path
from typing import IO
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

def find_json_files(directory: str) -> list[str]:
    """Find all JSON files in the given directory and its subdirectories."""
    json_files = []
    for root, dirs, files in os.walk(directory):
        # Modify dirs in-place to prevent descending into unwanted directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__MACOSX']

        # Skip hidden files
        files = [f for f in files if not f.startswith('.')]

        for file in files:
            # Check for .json extension
            if file.endswith('.json'):
                json_files.append(os.path.join(root, file))
    return json_files


def unzip_and_flatten(zip_path: str, extract_to: str):
    """
    Unzips a ZIP file, flattens its structure into the target directory,
    and ignores macOS specific metadata folders.
    """
    # Use Path objects for consistency
    zip_path_obj = Path(zip_path)
    extract_to_obj = Path(extract_to)
    base_name = zip_path_obj.stem # Get filename without extension

    # Use a more robust temporary directory name
    temp_extract_path = extract_to_obj.parent / f"{base_name}_temp_extract_{os.urandom(4).hex()}"
    os.makedirs(temp_extract_path, exist_ok=True)
    logging.debug("Temporary extraction path: %s", temp_extract_path)

    try:
        with zipfile.ZipFile(zip_path_obj, "r") as zip_ref:
            zip_ref.extractall(temp_extract_path)
        logging.debug("Initial extraction complete for %s", zip_path_obj.name)

        # Walk through the extracted content and move files, flattening structure
        files_moved = 0
        for item_path in temp_extract_path.rglob('*'):
            # Skip the __MACOSX directory and its contents, also .DS_Store
            if '__MACOSX' in item_path.parts or item_path.name == '.DS_Store':
                continue

            if item_path.is_file():
                # Calculate relative path to maintain structure *within* the zip,
                # but place it directly under 'extract_to'
                # Example: if zip contains dir1/file.txt, it moves to extract_to/file.txt
                # If we want to keep internal structure:
                # relative_path = item_path.relative_to(temp_extract_path)
                # dest = extract_to_obj / relative_path

                # Current logic flattens: places all files directly in extract_to
                dest = extract_to_obj / item_path.name # Flattened destination

                # Ensure destination directory exists (redundant if dest is always flat, but safe)
                # dest.parent.mkdir(parents=True, exist_ok=True) # Needed if keeping structure

                try:
                    shutil.move(str(item_path), str(dest))
                    files_moved += 1
                except (shutil.Error, OSError) as move_error: # Catch more specific errors
                    # Handle potential file conflicts if flattening causes name collisions
                    logging.warning(
                        "Could not move %s to %s (maybe duplicate filename?): %s",
                        item_path.name, dest, move_error
                    )


        logging.info("Moved %d files from %s archive to %s",
                     files_moved, zip_path_obj.name, extract_to_obj)

    except zipfile.BadZipFile as bad_zip_err:
        logging.error("Bad ZIP file: %s", zip_path)
        raise ValueError(f"Invalid or corrupted ZIP file: {zip_path_obj.name}") from bad_zip_err
    except Exception as e: # Catch other potential errors during extraction/moving
        logging.error("Error during unzipping/flattening %s: %s", zip_path, e)
        raise # Re-raise other exceptions, implicitly chains
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_extract_path):
            try:
                shutil.rmtree(temp_extract_path)
                logging.debug("Cleaned up temporary directory: %s", temp_extract_path)
            except OSError as cleanup_error:
                logging.error("Error removing temporary directory %s: %s",
                              temp_extract_path, cleanup_error)


def unzip_preserve_structure(zip_path: str, extract_to: str):
    """
    Unzips a ZIP file to a specified directory, preserving the internal folder structure.
    Ignores macOS specific metadata folders.
    Returns the path to the directory where files were extracted.
    """
    zip_path_obj = Path(zip_path)
    extract_to_obj = Path(extract_to)
    os.makedirs(extract_to_obj, exist_ok=True)
    logging.debug("Extracting %s to %s preserving structure...", zip_path_obj.name, extract_to_obj)

    try:
        with zipfile.ZipFile(zip_path_obj, "r") as zip_ref:
            # Extract all members except those in __MACOSX or .DS_Store
            members_to_extract = [m for m in zip_ref.infolist()
                                if not m.filename.startswith('__MACOSX/') and
                                '.DS_Store' not in m.filename]
            zip_ref.extractall(extract_to_obj, members=members_to_extract)
        logging.info("Successfully extracted archive %s to %s", zip_path_obj.name, extract_to_obj)
        return str(extract_to_obj)
    except zipfile.BadZipFile as bad_zip_err:
        logging.error("Bad ZIP file: %s", zip_path)
        raise ValueError(f"Invalid or corrupted ZIP file: {zip_path_obj.name}") from bad_zip_err
    except (OSError, Exception) as e: # Catch potential OS errors or other unexpected issues
        logging.error("Error during extraction of %s: %s", zip_path, e)
        raise # Re-raise other exceptions, implicitly chains

def validate_zip_content(zip_path: str, expected_type: str) -> bool:
    """Validate that a ZIP file contains the expected type of data."""
    logging.debug("Validating ZIP content for %s as type '%s'", zip_path, expected_type)
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            file_list = zip_ref.namelist()

            # Filter out macOS metadata common in zips
            relevant_files = [f for f in file_list if not f.startswith('__MACOSX') and
                              not f.endswith('.DS_Store')]

            if not relevant_files:
                logging.warning("ZIP file %s contains no relevant files after filtering metadata.",
                                 zip_path)
                return False

            if expected_type == "course":
                # Check for course JSON files (must end in .json)
                has_json = any(f.endswith('.json') for f in relevant_files)
                # Optional: Add stricter checks, e.g., filename patterns if known
                logging.debug("Course ZIP validation result for %s: %s", zip_path, has_json)
                return has_json
            elif expected_type == "audit":
                # Check for audit JSON files (must end in .json)
                has_json = any(f.endswith('.json') for f in relevant_files)
                logging.debug("Audit ZIP validation result for %s: %s", zip_path, has_json)
                return has_json
            else:
                logging.warning("Unknown expected_type '%s' for ZIP validation.", expected_type)
                return False # Or raise error for unknown type
    except zipfile.BadZipFile:
        logging.error("Cannot validate bad ZIP file: %s", zip_path)
        return False
    except (OSError, Exception) as e: # pylint: disable=broad-exception-caught
        logging.error("Error validating ZIP content for %s: %s", zip_path, e)
        return False

async def save_upload_file(file_like: IO, filename: str, destination: Path) -> None:
    """
    Saves an uploaded file-like object to the specified destination path.
    Accepts a file-like object (like UploadFile.file) and filename explicitly.
    """
    logging.debug("Saving uploaded file '%s' to '%s'", filename, destination)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Check if file_like supports async read (like SpooledTemporaryFile)
        if hasattr(file_like, 'read') and asyncio.iscoroutinefunction(file_like.read):
            content = await file_like.read()
        elif hasattr(file_like, 'read'):
            # Fallback to synchronous read for standard file objects
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, file_like.read)
        else:
            raise TypeError("Unsupported file-like object type")

        # Check for empty content *before* attempting to write
        if not content:
            logging.warning("Uploaded file '%s' is empty.", filename)
            raise ValueError(f"Uploaded file {filename} is empty.")

        # Now, try writing the file
        with open(destination, "wb") as f:
            f.write(content)
        logging.info("Successfully saved uploaded file '%s' (%d bytes) to %s",
                     filename, len(content), destination)
    except (IOError, OSError, TypeError) as e: # Catch specific expected errors
        logging.error("Failed to save uploaded file '%s' to %s: %s",
                      filename, destination, e)
        # Re-raise as IOError for consistent error handling upstream, unless it was the ValueError
        if not isinstance(e, ValueError):
            raise IOError(f"Could not save file {filename}: {e}") from e
        else:
            raise # Re-raise the original ValueError if it occurred earlier
    finally:
        # Ensure the file-like object is closed if it has a close method
        if hasattr(file_like, 'close'):
            file_like.close()
