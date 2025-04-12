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
    for root, _, files in os.walk(directory):
        # Skip hidden files/folders
        files = [f for f in files if not f.startswith('.')]
        # dirs[:] = [d for d in dirs if not d.startswith('.')] # Not needed as we only care about files here

        for file in files:
            # Added check for __MACOSX which can appear in zips from macOS
            if file.endswith('.json') and '__MACOSX' not in root:
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
                 except Exception as move_error:
                      # Handle potential file conflicts if flattening causes name collisions
                      logging.warning("Could not move %s to %s (maybe duplicate filename?): %s", item_path.name, dest, move_error)


        logging.info("Moved %d files from %s archive to %s", files_moved, zip_path_obj.name, extract_to_obj)

    except zipfile.BadZipFile:
         logging.error("Bad ZIP file: %s", zip_path)
         raise ValueError(f"Invalid or corrupted ZIP file: {zip_path_obj.name}")
    except Exception as e:
         logging.error("Error during unzipping/flattening %s: %s", zip_path, e)
         raise # Re-raise other exceptions
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_extract_path):
            try:
                 shutil.rmtree(temp_extract_path)
                 logging.debug("Cleaned up temporary directory: %s", temp_extract_path)
            except OSError as cleanup_error:
                 logging.error("Error removing temporary directory %s: %s", temp_extract_path, cleanup_error)


def validate_zip_content(zip_path: str, expected_type: str) -> bool:
    """Validate that a ZIP file contains the expected type of data."""
    logging.debug("Validating ZIP content for %s as type '%s'", zip_path, expected_type)
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            file_list = zip_ref.namelist()

            # Filter out macOS metadata common in zips
            relevant_files = [f for f in file_list if not f.startswith('__MACOSX') and not f.endswith('.DS_Store')]

            if not relevant_files:
                 logging.warning("ZIP file %s contains no relevant files after filtering metadata.", zip_path)
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
                # Optional: Stricter checks? e.g., presence of 'published.json' or major codes in paths
                logging.debug("Audit ZIP validation result for %s: %s", zip_path, has_json)
                return has_json
            else:
                 logging.warning("Unknown expected_type '%s' for ZIP validation.", expected_type)
                 return False # Or raise error for unknown type
    except zipfile.BadZipFile:
         logging.error("Cannot validate bad ZIP file: %s", zip_path)
         return False
    except Exception as e:
         logging.error("Error validating ZIP content for %s: %s", zip_path, e)
         return False


def organize_audit_files(audit_root_str: str):
    """
    Organizes audit JSON files found directly under audit_root into subfolders
    named after majors ('ba', 'bio', 'cs', 'is') based on filename.
    """
    audit_root = Path(audit_root_str) # Work with Path object
    logging.info("Organizing audit files in %s...", audit_root)
    allowed_majors = {'ba', 'bio', 'cs', 'is'}

    # Check if major subfolders already exist
    major_folders_exist = any(d.is_dir() and d.name in allowed_majors for d in audit_root.iterdir())

    # Find JSON files directly in the root audit directory
    direct_json_files = [f for f in audit_root.iterdir() if f.is_file() and f.suffix == '.json']

    if not major_folders_exist and direct_json_files:
        logging.info("No major folders found, attempting to organize %d audit files by major...", len(direct_json_files))
        files_moved = 0
        found_dirs = set()
        for json_file_path in direct_json_files:
            file_name_lower = json_file_path.stem.lower()
            major = None
            for m in allowed_majors:
                # Simple check if major code is in filename
                if m in file_name_lower:
                    major = m
                    break

            if major:
                major_folder = audit_root / major
                major_folder.mkdir(exist_ok=True)
                dest_path = major_folder / json_file_path.name
                try:
                    # Use move for efficiency
                    shutil.move(str(json_file_path), str(dest_path))
                    logging.info("Moved %s to %s", json_file_path.name, dest_path)
                    found_dirs.add(major)
                    files_moved += 1
                except Exception as move_error:
                    logging.error("Error moving %s to %s: %s", json_file_path.name, dest_path, move_error)

        if files_moved > 0:
            logging.info("Organized %d audit files into major folders: %s", files_moved, list(found_dirs))
        else:
            # Warn only if still no major folders exist after trying
            if not any(d.is_dir() and d.name in allowed_majors for d in audit_root.iterdir()):
                 logging.warning("Could not identify majors from audit filenames to organize them.")

    # Final check for logging/validation
    final_major_dirs = {d.name for d in audit_root.iterdir() if d.is_dir() and d.name in allowed_majors}
    if not final_major_dirs:
        logging.warning("Audit directory %s does not contain expected major subfolders after processing.", audit_root)
    else:
        logging.debug("Found major subfolders after organization: %s", list(final_major_dirs))

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

        if not content:
            logging.warning("Uploaded file '%s' is empty.", filename)
            raise ValueError(f"Uploaded file {filename} is empty.")

        with open(destination, "wb") as f:
            f.write(content)
        logging.info("Successfully saved uploaded file '%s' (%d bytes) to %s",
                     filename, len(content), destination)
    except Exception as e:
        logging.error("Failed to save uploaded file '%s' to %s: %s",
                      filename, destination, e)
        raise IOError(f"Could not save file {filename}: {e}") from e
    finally:
         # Ensure the file-like object is closed if it has a close method
         if hasattr(file_like, 'close'):
              file_like.close()

# Placeholder for higher-level function - we will build this out later
# async def prepare_upload_files(...): -> Dict[str, Any]
#    pass