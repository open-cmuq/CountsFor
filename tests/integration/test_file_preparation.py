"""Integration tests for file preparation utilities."""

import os
import shutil
import zipfile
from unittest.mock import MagicMock

import pytest

from backend.app.utils.file_handler import (
    find_json_files,
    organize_audit_files,
    save_upload_file,
    unzip_and_flatten,
    validate_zip_content,
)

# Mark all tests in this file as asyncio


# --- Fixtures ---

@pytest.fixture
def mock_upload_file():
    """Creates a basic mock UploadFile object."""
    mock_file = MagicMock()
    mock_file.filename = "test.txt"
    # Simulate the .file attribute which is often a SpooledTemporaryFile
    mock_file.file = MagicMock()
    # Simulate async read() if needed, or simple read()
    async def async_read():
        return b"Test content"
    mock_file.read = async_read # Use if save_upload_file expects await file.read()
    mock_file.file.read = lambda: b"Test content" # For synchronous reads if needed
    mock_file.file.close = MagicMock()
    return mock_file

@pytest.fixture(scope="module")
def sample_files_dir(tmp_path_factory):
    """Creates a directory with sample files for testing ZIPs."""
    fixtures_dir = tmp_path_factory.mktemp("test_fixtures")

    # --- Sample Course ZIP ---
    course_zip_path = fixtures_dir / "sample_course.zip"
    course_dir = fixtures_dir / "course_src"
    course_dir.mkdir()
    course1_content = '{"code": "01-101", "name": "Course 1", "success": true}'
    (course_dir / "course1.json").write_text(course1_content)
    course2_content = '{"code": "01-102", "name": "Course 2", "success": true}'
    (course_dir / "course2.json").write_text(course2_content)
    # Create a dummy __MACOSX (should be ignored)
    macosx_dir = course_dir / "__MACOSX"
    macosx_dir.mkdir()
    (macosx_dir / "dummy").touch()

    with zipfile.ZipFile(course_zip_path, 'w') as zf:
        for file in course_dir.rglob('*'):
            # Write files relative to the course_src directory to mimic structure
            zf.write(file, arcname=file.relative_to(course_dir))

    # --- Sample Audit ZIP (with direct JSONs and major folders) ---
    audit_zip_path = fixtures_dir / "sample_audit.zip"
    audit_dir = fixtures_dir / "audit_src"
    audit_dir.mkdir()
    # File that should be organized
    audit_content = '{"requirement": { "screen_name": "CS Core Req"}}'
    (audit_dir / "cs_core_audit.json").write_text(audit_content)
    # Existing major folder
    cs_audit_subdir = audit_dir / "cs"
    cs_audit_subdir.mkdir()
    published_content = '{"requirement": { "screen_name": "CS GenEd Req"}}'
    (cs_audit_subdir / "published.json").write_text(published_content)

    with zipfile.ZipFile(audit_zip_path, 'w') as zf:
        for file in audit_dir.rglob('*'):
            zf.write(file, arcname=file.relative_to(audit_dir))

    return fixtures_dir


# --- Test Functions ---

@pytest.mark.asyncio
async def test_save_upload_file_success(tmp_path, mock_upload_file): # pylint: disable=redefined-outer-name
    """Test successfully saving a simulated uploaded file."""
    dest_path = tmp_path / "output" / mock_upload_file.filename
    # Set specific content
    mock_upload_file.file.read = lambda: b"Simulated file content."

    await save_upload_file(
        mock_upload_file.file, mock_upload_file.filename, dest_path
    )

    assert dest_path.exists()
    assert dest_path.read_text() == "Simulated file content."
    mock_upload_file.file.close.assert_called_once() # Ensure file is closed

@pytest.mark.asyncio
async def test_save_upload_file_empty(tmp_path, mock_upload_file): # pylint: disable=redefined-outer-name
    """Test saving an empty file raises ValueError."""
    dest_path = tmp_path / "output" / mock_upload_file.filename
    # Simulate empty content
    async def async_read_empty():
        return b""
    mock_upload_file.read = async_read_empty
    mock_upload_file.file.read = lambda: b""

    with pytest.raises(ValueError, match="Uploaded file test.txt is empty."):
        await save_upload_file(
            mock_upload_file.file, mock_upload_file.filename, dest_path
        )
    assert not dest_path.exists() # File should not be created
    mock_upload_file.file.close.assert_called_once()

@pytest.mark.asyncio
async def test_save_upload_file_io_error(tmp_path, mock_upload_file): # pylint: disable=redefined-outer-name
    """Test that IOErrors during saving are propagated."""
    # Make destination unwritable (e.g., by making parent a file)
    dest_dir = tmp_path / "output"
    dest_dir.touch() # Create output as a file, so cannot write inside it
    dest_path = dest_dir / mock_upload_file.filename

    with pytest.raises(IOError):
        await save_upload_file(
            mock_upload_file.file, mock_upload_file.filename, dest_path
        )

    mock_upload_file.file.close.assert_called_once()

def test_find_json_files(tmp_path):
    """Test finding JSON files, skipping hidden files/dirs."""
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    (dir1 / "file1.json").touch()
    (dir1 / ".hidden.json").touch() # Hidden file

    dir2 = tmp_path / "dir2"
    dir2.mkdir()
    subdir = dir2 / "subdir"
    subdir.mkdir()
    (subdir / "file2.json").touch()

    hidden_dir = tmp_path / ".hidden_dir"
    hidden_dir.mkdir()
    (hidden_dir / "file3.json").touch() # File in hidden dir

    macosx_dir = tmp_path / "__MACOSX"
    macosx_dir.mkdir()
    (macosx_dir / "file4.json").touch() # File in macosx dir

    (tmp_path / "root.json").touch()

    found_files = find_json_files(str(tmp_path))
    found_basenames = {os.path.basename(f) for f in found_files}

    assert found_basenames == {"file1.json", "file2.json", "root.json"}
    assert len(found_files) == 3

def test_validate_zip_content_course_ok(sample_files_dir): # Removed unused tmp_path, pylint: disable=redefined-outer-name
    """Test validation passes for a valid course zip."""
    zip_path = sample_files_dir / "sample_course.zip"
    assert validate_zip_content(str(zip_path), "course") is True

def test_validate_zip_content_audit_ok(sample_files_dir): # Removed unused tmp_path, pylint: disable=redefined-outer-name
    """Test validation passes for a valid audit zip."""
    zip_path = sample_files_dir / "sample_audit.zip"
    assert validate_zip_content(str(zip_path), "audit") is True

def test_validate_zip_content_empty_zip(tmp_path): # tmp_path is used here
    """Test validation fails for an empty zip."""
    zip_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf: # pylint: disable=unused-variable
        pass # Create empty zip
    assert validate_zip_content(str(zip_path), "course") is False

def test_validate_zip_content_no_json(tmp_path): # tmp_path is used here
    """Test validation fails if zip contains no JSON files."""
    zip_path = tmp_path / "no_json.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("readme.txt", "hello")
    assert validate_zip_content(str(zip_path), "course") is False

def test_validate_zip_content_bad_zip(tmp_path): # tmp_path is used here
    """Test validation fails for a corrupted zip."""
    zip_path = tmp_path / "bad.zip"
    zip_path.write_text("this is not a zip file")
    assert validate_zip_content(str(zip_path), "course") is False

def test_unzip_and_flatten_course(tmp_path, sample_files_dir): # pylint: disable=redefined-outer-name
    """Test unzipping and flattening a course zip."""
    zip_path = sample_files_dir / "sample_course.zip"
    extract_dir = tmp_path / "extracted_courses"
    extract_dir.mkdir()

    unzip_and_flatten(str(zip_path), str(extract_dir))

    extracted_files = {f.name for f in extract_dir.iterdir() if f.is_file()}
    # Should contain the JSONs, but not __MACOSX content
    assert extracted_files == {"course1.json", "course2.json"}
    assert not (extract_dir / "__MACOSX").exists()

def test_organize_audit_files_needs_org(tmp_path, sample_files_dir): # pylint: disable=redefined-outer-name
    """Test organizing audit files when JSON is at the root."""
    # Simulate extracted state before organization
    audit_root = tmp_path / "audit_prep"
    audit_root.mkdir()
    # Copy the file that needs organizing
    shutil.copy(sample_files_dir / "audit_src" / "cs_core_audit.json", audit_root)
    # Copy the already existing folder
    shutil.copytree(sample_files_dir / "audit_src" / "cs", audit_root / "cs")

    organize_audit_files(str(audit_root))

    # Check that the loose file was moved
    assert not (audit_root / "cs_core_audit.json").exists()
    assert (audit_root / "cs" / "cs_core_audit.json").exists()
    # Check the originally present file is still there
    assert (audit_root / "cs" / "published.json").exists()

def test_organize_audit_files_pre_organized(tmp_path, sample_files_dir): # pylint: disable=redefined-outer-name
    """Test organizing does nothing if structure is already correct."""
    audit_root = tmp_path / "audit_prep"
    audit_root.mkdir()
    # Copy only the already existing folder
    shutil.copytree(sample_files_dir / "audit_src" / "cs", audit_root / "cs")

    # Record initial state
    initial_files = set(
        p.relative_to(audit_root) for p in audit_root.rglob('*')
    )

    organize_audit_files(str(audit_root))

    # Record final state
    final_files = set(p.relative_to(audit_root) for p in audit_root.rglob('*'))

    # Assert no files were moved or created/deleted
    assert initial_files == final_files
    assert (audit_root / "cs" / "published.json").exists()
