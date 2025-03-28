import React, { useState } from 'react';
import { Box, Button, Typography, Paper, Alert, CircularProgress } from '@mui/material';
import { styled } from '@mui/material/styles';
import JSZip from 'jszip';

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const DataUpload = () => {
  const [state, setState] = useState({
    courseZips: [],
    auditZips: [],
    enrollmentFile: null,
    departmentCsv: null,
    reset: false,
    loading: false,
    error: null,
    success: null,
  });

  const validateZipStructure = async (file, type) => {
    try {
      const zip = new JSZip();
      const contents = await zip.loadAsync(file);

      if (type === 'course') {
        // Course ZIP should contain course JSON files
        const hasCourseFiles = Object.keys(contents.files).some(path =>
          path.endsWith('.json') && !path.includes('__MACOSX')
        );
        if (!hasCourseFiles) {
          throw new Error('Course ZIP must contain course JSON files');
        }
      } else if (type === 'audit') {
        // Audit ZIP should contain audit JSON files
        const hasAuditFiles = Object.keys(contents.files).some(path =>
          path.endsWith('.json') && !path.includes('__MACOSX')
        );
        if (!hasAuditFiles) {
          throw new Error('Audit ZIP must contain audit JSON files');
        }
      }
      return true;
    } catch (error) {
      throw new Error(`Invalid ZIP structure: ${error.message}`);
    }
  };

  const validateFileType = (file, type) => {
    // Check file extension
    const fileExtension = file.name.split('.').pop().toLowerCase();

    // Check MIME type
    const mimeType = file.type;

    switch (type) {
      case 'course':
      case 'audit':
        if (fileExtension !== 'zip' || !mimeType.includes('zip')) {
          throw new Error(`${type === 'course' ? 'Course' : 'Audit'} files must be ZIP files`);
        }
        break;
      case 'enrollment':
        if (!['xlsx', 'xls'].includes(fileExtension) ||
            (!mimeType.includes('spreadsheet') && !mimeType.includes('excel'))) {
          throw new Error('Enrollment file must be an Excel file (.xlsx or .xls)');
        }
        break;
      case 'department':
        if (fileExtension !== 'csv' || !mimeType.includes('csv')) {
          throw new Error('Department file must be a CSV file');
        }
        break;
      default:
        throw new Error('Invalid file type');
    }
  };

  const handleFileChange = async (event, field) => {
    const files = event.target.files;
    if (!files) return;

    // Clear any existing error when files are changed
    setState(prev => ({ ...prev, error: null }));

    try {
      if (field === 'courseZips' || field === 'auditZips') {
        const validatedFiles = [];
        for (const file of files) {
          validateFileType(file, field === 'courseZips' ? 'course' : 'audit');
          await validateZipStructure(file, field === 'courseZips' ? 'course' : 'audit');
          validatedFiles.push(file);
        }
        setState(prev => ({
          ...prev,
          [field]: validatedFiles,
        }));
      } else {
        const file = files[0];
        console.log(`Processing ${field}:`, {
          name: file.name,
          type: file.type,
          size: file.size
        });

        validateFileType(file, field === 'enrollmentFile' ? 'enrollment' : 'department');

        // For department CSV, verify it's not empty
        if (field === 'departmentCsv') {
          const text = await file.text();
          console.log('Department CSV content preview:', text.substring(0, 200));
          if (!text.trim()) {
            throw new Error('Department CSV file is empty');
          }
        }

        setState(prev => ({
          ...prev,
          [field]: file,
        }));
      }
    } catch (error) {
      console.error(`Error in handleFileChange for ${field}:`, error);
      setState(prev => ({
        ...prev,
        error: error.message,
        [field]: field === 'courseZips' || field === 'auditZips' ? [] : null,
      }));
    }
  };

  const handleUpload = async () => {
    setState(prev => ({ ...prev, loading: true, error: null, success: null }));

    // Debug log for form data
    console.log('Current state:', {
      courseZips: state.courseZips.length,
      auditZips: state.auditZips.length,
      enrollmentFile: state.enrollmentFile?.name,
      departmentCsv: state.departmentCsv?.name,
      reset: state.reset
    });

    // Validate upload combinations
    if (state.auditZips.length > 0 && state.courseZips.length === 0) {
      setState(prev => ({
        ...prev,
        error: "Audit data requires course data. Please upload course ZIP files along with the audit files.",
        loading: false
      }));
      return;
    }

    if (state.enrollmentFile && state.courseZips.length === 0) {
      setState(prev => ({
        ...prev,
        error: "Enrollment data requires course data. Please upload course ZIP files along with the enrollment file.",
        loading: false
      }));
      return;
    }

    if (state.auditZips.length > 0 && state.enrollmentFile && state.courseZips.length === 0) {
      setState(prev => ({
        ...prev,
        error: "Both audit and enrollment data require course data. Please upload course ZIP files along with the other files.",
        loading: false
      }));
      return;
    }

    const formData = new FormData();

    // Add files only if they exist
    state.courseZips.forEach(file => formData.append('course_zips', file));
    state.auditZips.forEach(file => formData.append('audit_zips', file));
    if (state.enrollmentFile) formData.append('enrollment_file', state.enrollmentFile);
    if (state.departmentCsv) {
      console.log('Adding department CSV to form data:', state.departmentCsv.name);
      formData.append('department_csv', state.departmentCsv);
    }
    formData.append('reset', state.reset.toString());

    // Debug log for form data
    console.log('FormData entries:');
    for (let pair of formData.entries()) {
      console.log(pair[0], pair[1]);
    }

    try {
      const apiUrl = `${API_BASE_URL}/upload/init-db/`;
      console.log('Attempting to fetch from:', apiUrl);

      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      setState(prev => ({
        ...prev,
        success: data.message || (data.loaded_data ? `Successfully loaded: ${data.loaded_data.join(', ')}` : 'Operation completed successfully'),
        loading: false,
      }));
    } catch (error) {
      console.error('Upload error details:', {
        message: error.message,
        stack: error.stack,
        cause: error.cause,
        type: error.name
      });

      let errorMessage = 'Upload failed';
      if (error.message === 'Failed to fetch' || error.message.includes('Cannot connect to the server')) {
        errorMessage = 'Could not connect to the server. Please make sure the backend server is running at http://127.0.0.1:8000';
      } else {
        errorMessage = error.message;
      }

      setState(prev => ({
        ...prev,
        error: errorMessage,
        loading: false,
      }));
    }
  };

  // Add validation for the upload button
  const isUploadDisabled = () => {
    // If no files are selected, disable the button
    if (!state.courseZips.length && !state.auditZips.length && !state.enrollmentFile && !state.departmentCsv) {
      return true;
    }

    // If loading, disable the button
    if (state.loading) {
      return true;
    }

    // If there's an error, disable the button
    if (state.error) {
      return true;
    }

    return false;
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Database Data Upload
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Upload Instructions
        </Typography>
        <Typography paragraph>
          You can upload combinations of the following data types. Note that some data types have dependencies on others.
        </Typography>

        <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, mb: 1 }}>
          Allowed Upload Scenarios:
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          • Department Data: Can be updated independently. Upload department CSV to update department information.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          • Course Data: Can be updated independently. Upload course ZIPs to update course information.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          • Course Data + Department Data: Upload both to update course information with department details.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          • Course Data + Audit Data: Upload both course and audit ZIPs together to update course information and major requirements. Course data is required for audit data.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          • Course Data + Enrollment Data: Upload course ZIPs with enrollment Excel to update course information and enrollment data. Course data is required for enrollment records.
        </Typography>
        <Typography variant="body2" color="text.secondary" paragraph>
          • Full Update: Upload all files together to perform a complete database update. This ensures all dependencies are satisfied.
        </Typography>

        <Typography variant="subtitle1" gutterBottom sx={{ mt: 3, mb: 1, color: 'error.main' }}>
          Not Allowed Scenarios:
        </Typography>
        <Typography variant="body2" color="error" paragraph>
          • Audit Data alone (requires Course Data)
        </Typography>
        <Typography variant="body2" color="error" paragraph>
          • Enrollment Data alone (requires Course Data)
        </Typography>
        <Typography variant="body2" color="error" paragraph>
          • Audit Data + Department Data without Course Data
        </Typography>
        <Typography variant="body2" color="error" paragraph>
          • Enrollment Data + Department Data without Course Data
        </Typography>
        <Typography variant="body2" color="error" paragraph>
          • Audit Data + Enrollment Data without Course Data
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Course Data (ZIP files)
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Upload ZIP files containing course data. Each ZIP should contain course JSON files.
            The folder structure should be: courses.zip → course_files.json
          </Typography>
          <Button
            component="label"
            variant="outlined"
            fullWidth
            sx={{ mb: 1 }}
          >
            Select Course ZIP Files
            <VisuallyHiddenInput
              type="file"
              multiple
              accept=".zip"
              onChange={(e) => handleFileChange(e, 'courseZips')}
            />
          </Button>
          {state.courseZips.length > 0 && (
            <Typography variant="body2" color="text.secondary">
              Selected: {state.courseZips.length} file(s)
            </Typography>
          )}
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Audit Data (ZIP files)
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Upload ZIP files containing audit data. Each ZIP should contain audit JSON files.
            The folder structure should be: audits.zip → audit_files.json
          </Typography>
          <Button
            component="label"
            variant="outlined"
            fullWidth
            sx={{ mb: 1 }}
          >
            Select Audit ZIP Files
            <VisuallyHiddenInput
              type="file"
              multiple
              accept=".zip"
              onChange={(e) => handleFileChange(e, 'auditZips')}
            />
          </Button>
          {state.auditZips.length > 0 && (
            <Typography variant="body2" color="text.secondary">
              Selected: {state.auditZips.length} file(s)
            </Typography>
          )}
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Enrollment Data (Excel file)
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Upload an Excel file containing enrollment data for courses.
            The file must contain the following columns:
          </Typography>
          <Typography variant="body2" color="text.secondary" component="div" sx={{ pl: 2, mb: 2 }}>
            • Semester Id (Schedule)
            <br />
            • Course Id
            <br />
            • Section Id
            <br />
            • Department Id
            <br />
            • Class Id
            <br />
            • Count of Class Id
          </Typography>
          <Button
            component="label"
            variant="outlined"
            fullWidth
            sx={{ mb: 1 }}
          >
            Select Enrollment Excel File
            <VisuallyHiddenInput
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => handleFileChange(e, 'enrollmentFile')}
            />
          </Button>
          {state.enrollmentFile && (
            <Typography variant="body2" color="text.secondary">
              Selected: {state.enrollmentFile.name}
            </Typography>
          )}
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Department Data (CSV file)
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Upload a CSV file containing department information.
            The file should have columns for department code and name.
          </Typography>
          <Button
            component="label"
            variant="outlined"
            fullWidth
            sx={{ mb: 1 }}
          >
            Select Department CSV File
            <VisuallyHiddenInput
              type="file"
              accept=".csv"
              onChange={(e) => handleFileChange(e, 'departmentCsv')}
            />
          </Button>
          {state.departmentCsv && (
            <Typography variant="body2" color="text.secondary">
              Selected: {state.departmentCsv.name}
            </Typography>
          )}
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Database Reset Option
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Check this box to reset the database before uploading new data.
            This will delete all existing data before adding the new data.
          </Typography>
          <Button
            variant={state.reset ? "contained" : "outlined"}
            color={state.reset ? "error" : "primary"}
            onClick={() => setState(prev => ({ ...prev, reset: !prev.reset }))}
            fullWidth
          >
            {state.reset ? "Reset Database (Enabled)" : "Reset Database (Disabled)"}
          </Button>
        </Box>

        {state.error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {state.error}
          </Alert>
        )}

        {state.success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {state.success}
          </Alert>
        )}

        <Button
          variant="contained"
          color="primary"
          onClick={handleUpload}
          disabled={isUploadDisabled()}
          fullWidth
        >
          {state.loading ? <CircularProgress size={24} /> : "Upload Data"}
        </Button>
      </Paper>
    </Box>
  );
};

export default DataUpload;