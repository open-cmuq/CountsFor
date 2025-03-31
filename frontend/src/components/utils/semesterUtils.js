/**
 * Parses a semester string into a comparable format
 * @param {string} semesterString - Semester string in format 'SYY', 'MYY', or 'FYY' (e.g., 'F23', 'S24')
 * @returns {{year: number, seasonOrder: number}} Object containing year and season order
 */
export const parseSemester = (semesterString) => {
  const seasonChar = semesterString[0];
  const year = parseInt(semesterString.slice(1), 10) || 0;

  let seasonOrder;
  switch (seasonChar) {
    case 'S': // Spring
      seasonOrder = 1;
      break;
    case 'M': // Summer
      seasonOrder = 2;
      break;
    case 'F': // Fall
      seasonOrder = 3;
      break;
    default:
      seasonOrder = 0;
  }
  return { year, seasonOrder };
};

/**
 * Sorts semesters by most recent first (for dropdowns)
 * @param {string[]} semesters - Array of semester strings
 * @returns {string[]} Sorted array of semester strings
 */
export const sortSemesters = (semesters) => {
  return [...semesters].sort((s1, s2) => {
    const A = parseSemester(s1);
    const B = parseSemester(s2);
    if (A.year !== B.year) return B.year - A.year; // Most recent year first
    return B.seasonOrder - A.seasonOrder; // Within same year, Fall > Summer > Spring
  });
};

/**
 * Sorts semesters chronologically (oldest to newest, for charts)
 * @param {string[]} semesters - Array of semester strings
 * @returns {string[]} Sorted array of semester strings
 */
export const sortSemestersChronologically = (semesters) => {
  return [...semesters].sort((s1, s2) => {
    const A = parseSemester(s1);
    const B = parseSemester(s2);
    if (A.year !== B.year) return A.year - B.year; // Oldest year first
    return A.seasonOrder - B.seasonOrder; // Within same year, Spring > Summer > Fall
  });
};