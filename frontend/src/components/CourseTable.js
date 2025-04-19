import React, { useState } from "react";
import MultiSelectDropdown from "./MultiSelectDropdown";
import SingleSelectDropdown from "./SingleSelectDropdown";
import Popup from "./PopUp";
import { formatCourseCode } from './utils/courseCodeFormatter';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const CourseTable = ({
  courses,
  allRequirements,
  selectedFilters,
  handleFilterChange,
  clearFilters,
  offeredOptions,
  selectedOfferedSemesters,
  setSelectedOfferedSemesters,
  coreOnly,
  genedOnly,
  allowRemove,
  handleRemoveCourse,
  noPrereqs,
  setNoPrereqs,
  compactViewMode,
  hideDropdowns,
  isPlanTab = false,
}) => {
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [popupType, setPopupType] = useState("");
  const [popupContent, setPopupContent] = useState(null);

  const fetchCourseDetails = async (course_code) => {
    try {
      const formattedCode = formatCourseCode(course_code);
      const response = await fetch(`${API_BASE_URL}/courses/${formattedCode}`);
      if (!response.ok) throw new Error("Failed to fetch course details");
      const data = await response.json();
      return data;
    } catch (error) {
      console.error("Error fetching course details:", error);
      return null;
    }
  };

  const openPopup = async (type, content) => {
    if (type === "course") {
      const fullCourseDetails = await fetchCourseDetails(content.course_code);
      if (fullCourseDetails) {
        setPopupType(type);
        setPopupContent(fullCourseDetails);
        setIsPopupOpen(true);
      }
    } else {
      setPopupType(type);
      setPopupContent(content);
      setIsPopupOpen(true);
    }
  };

  const closePopup = () => {
    setIsPopupOpen(false);
    setPopupType("");
    setPopupContent(null);
  };

  // Helper to filter requirement objects based on coreOnly/genedOnly:
  const filterRequirementObjects = (reqObjs) => {
    return reqObjs.filter(reqObj => {
      if (coreOnly && !genedOnly) {
        return reqObj.type === false; // Only Core
      } else if (genedOnly && !coreOnly) {
        return reqObj.type === true; // Only GenEd
      }
      return true;
    });
  };

  // For expandable Pre-Req cells
    const PrereqCell = ({ text }) => {
      const [expanded, setExpanded] = useState(false);

      // Remove square brackets from the text
      const cleanedText = text ? text.replace(/[[\]]/g, '') : text;
      const previewText = cleanedText.length > 40 ? cleanedText.slice(0, 40) + "..." : cleanedText;

      return (
        <>
          {expanded ? cleanedText : previewText}
          {cleanedText.length > 40 && (
            <span
              className="expand-toggle"
              onClick={(e) => {
                e.stopPropagation();
                setExpanded(!expanded);
              }}
            >
              {expanded ? " Show less" : " Show more"}
            </span>
          )}
        </>
      );
    };

    // Calculate the total number of columns - needed to change the format of table for plan and view tab
    const totalColumns =
    1 + // Course column
    Object.keys(allRequirements).length +
    2 + // Offered + Prereq
    (allowRemove ? 1 : 0);

    // For expandable offered cells
    const OfferedCell = ({ offeredList, compactViewMode }) => {
      const [expanded, setExpanded] = useState(false);
    
      const sortSemestersChronologically = (semesters) => {
        const termOrder = { S: 1, M: 2, F: 3 };
        return semesters.slice().sort((a, b) => {
          const termA = a[0];
          const yearA = parseInt(a.slice(1));
          const termB = b[0];
          const yearB = parseInt(b.slice(1));
          if (yearA !== yearB) return yearA - yearB;
          return termOrder[termA] - termOrder[termB];
        });
      };
    
      // For offered column: sort the semesters and make cell expandable if in compact view
      const sortedSemesters = sortSemestersChronologically(offeredList);
      const text = sortedSemesters.join(", ");
      const previewText = text.length > 50 ? text.slice(0, 50) + "..." : text;
    
      const isCompact = compactViewMode === "last1" || compactViewMode === "last2";
    
      return (
        <td className="cell-offered">
          {/* If in full requirements view, show full text */}
          {isCompact ? (
            <>
              {expanded ? text : previewText}
              {text.length > 50 && (
                <span
                className="expand-toggle"
                onClick={(e) => {
                  e.stopPropagation();
                  setExpanded(!expanded);
                }}
              >
                {expanded ? "Show less" : "Show more"}
              </span>
              )}
            </>
          ) : (
            text
          )}
        </td>
      );
    };
    
    
  return (
    <div>
      <table>
        <thead>
          <tr>
          {allowRemove && <th className="remove-col"> </th>}
          <th className="course-info-col">COURSES</th>
            {Object.keys(allRequirements).map((major) => {
              // Filter the requirement objects for this major based on active type filters.
              const optionsForMajor = allRequirements[major].filter((reqObj) => {
                if (coreOnly && !genedOnly) return reqObj.type === false;
                if (genedOnly && !coreOnly) return reqObj.type === true;
                return true;
              });

              return (
                <th key={major} className={`header-${major.toLowerCase()}`}>
                  {major}
                  {!hideDropdowns && (
                    <>
                      <br />
                      <MultiSelectDropdown
                        major={major}
                        allRequirements={optionsForMajor}
                        selectedFilters={selectedFilters}
                        handleFilterChange={handleFilterChange}
                        clearFilters={clearFilters}
                      />
                    </>
                  )}
                </th>
              );
            })}
            <th className="header-offered">
              OFFERED
              {!hideDropdowns && (
                <>
                  <br />
                  <MultiSelectDropdown
                    major="offered"
                    allRequirements={offeredOptions}
                    selectedFilters={{ offered: selectedOfferedSemesters }}
                    handleFilterChange={(major, newSelection) =>
                      setSelectedOfferedSemesters(newSelection)
                    }
                    clearFilters={() => setSelectedOfferedSemesters([])}
                  />
                </>
              )}
            </th>
            <th className="header-prereq">
              PRE-REQ
              {!hideDropdowns && (
                <>
                  <br />
                  <SingleSelectDropdown
                    major="prereq"
                    options={["all", "with", "without"]}
                    selected={
                      noPrereqs === null
                        ? "all"
                        : noPrereqs === false
                        ? "without"
                        : "with"
                    }
                    onChange={(value) => {
                      if (value === "all") setNoPrereqs(null);
                      else if (value === "without") setNoPrereqs(false);
                      else if (value === "with") setNoPrereqs(true);
                    }}
                  />
                </>
              )}
            </th>
          </tr>
        </thead>
        <tbody>
        {courses.length === 0 ? (
          <tr>
            <td colSpan={totalColumns} className="no-results-msg">
              {isPlanTab
                ? "No planned courses yet. Search and add courses above to get started! 📋"
                : "No courses found. Try adjusting your filters or search criteria."}
            </td>
        </tr>
    ) :(
          courses.map((course) => (
              <tr key={course.course_code}>
            {allowRemove && (
              <td className="remove-col">
                <button className="remove-btn" onClick={() => handleRemoveCourse(course.course_code)}>
                  ✖
                </button>
              </td>
            )}

              <td>
                <b
                  className="clickable"
                  onClick={() => openPopup("course", course)}
                  style={{
                    cursor: "pointer",
                    textDecoration: "underline",
                    color: "black",
                  }}
                >
                  {formatCourseCode(course.course_code)}
                </b>
                <br />
                {course.course_name}
              </td>
              {Object.keys(allRequirements).map((major) => {
              const reqObjects = course.requirements?.[major] || [];
              // Filter out the ones that don't match the active (Core/GenEd) filter
              const filteredReqObjects = filterRequirementObjects(reqObjects);

              // If, after filtering, there's nothing left, return an empty cell
              if (filteredReqObjects.length === 0) {
                return <td key={major}></td>;
              }

              // Otherwise, build the list items using the *filtered* objects
              const formattedRequirements = filteredReqObjects.map((reqObj, index) => {
                let formattedText = reqObj.requirement;

                // Format the requirement text based on its type
                if (reqObj.type) { // GenEd type
                  // Handle different GenEd formats
                  if (formattedText.includes("General Education")) {
                    // Traditional format with "General Education"
                    formattedText = formattedText.replace(/^.*General Education\s*---/, "");
                  } else if (formattedText.includes("University Core Requirements")) {
                    // BA format using "University Core Requirements"
                    const parts = formattedText.split("University Core Requirements");
                    if (parts.length > 1) {
                      formattedText = parts[1].replace(/^---/, "");
                    }
                  } else {
                    // For any other GenEd format, just remove the initial prefix
                    formattedText = formattedText.replace(/^[^-]+---/, "");
                  }
                } else { // Core type
                  // Just remove the initial part as before
                  formattedText = formattedText.replace(/^[^-]+---/, "");
                }

                // Replace all --- with arrows for both types
                formattedText = formattedText.replace(/---/g, " → ");

                if (compactViewMode === "last2") {
                  const parts = formattedText.split("→").map(s => s.trim());
                  formattedText = parts.slice(-2).join(" → ");
                } else if (compactViewMode === "last1") {
                  const parts = formattedText.split("→").map(s => s.trim());
                  formattedText = parts[parts.length - 1];
                }

                return reqObj.type
                  ? <i key={index}>{formattedText}</i>   // GenEd
                  : <b key={index}>{formattedText}</b>;  // Core
              });

              return (
                <td
                  key={major}
                  className={`cell cell-${major.toLowerCase()}`}
                  onClick={() => openPopup("requirement", {
                    // Pass the *filtered* objects to the popup
                    requirement: filteredReqObjects,
                    // Also filter courses based on the *filtered* requirement strings
                    courses: courses.filter((c) =>
                      c.requirements?.[major]?.some((rObj) =>
                        filteredReqObjects.some(
                          (fObj) => fObj.requirement === rObj.requirement
                        )
                      )
                    ),
                  })}
                  style={{
                    cursor: "pointer",
                    color: "blue",
                    textAlign: "left",
                  }}
                >
                  <ul style={{ margin: "5px 0", paddingLeft: "20px", textAlign: "left" }}>
                    {formattedRequirements.map((el, idx) => (
                      <li key={idx} style={{ listStyleType: "disc" }}>
                        {el}
                      </li>
                    ))}
                  </ul>
                </td>
              );
            })}

              <OfferedCell offeredList={course.offered} compactViewMode={compactViewMode} />
              <td className="cell-prereq">
              <PrereqCell text={course.prerequisites} />
              </td>
              </tr>
          )))}
        </tbody>
      </table>

      <Popup
        isOpen={isPopupOpen}
        onClose={closePopup}
        type={popupType}
        content={popupContent}
        openPopup={openPopup}
      />
    </div>
  );
};

export default CourseTable;
