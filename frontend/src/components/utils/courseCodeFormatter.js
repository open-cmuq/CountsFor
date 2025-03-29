export const formatCourseCode = (code) => {
  if (!code) return code;

  // Remove all spaces and convert to uppercase
  code = code.replace(/\s+/g, '').toUpperCase();

  // If the code is just numbers, add dash between department number and course number
  if (/^\d+$/.test(code)) {
    return code.replace(/^(\d{2})(\d{3})$/, '$1-$2');
  }

  // If it already has a dash, return as is
  if (code.includes('-')) {
    return code;
  }

  return code;
};