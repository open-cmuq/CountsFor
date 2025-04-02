import React, { useState } from "react";
import MultiSelectDropdown from "./MultiSelectDropdown";
import Popup from "./PopUp";

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
  coreOnly,    // new prop
  genedOnly,   // new prop
  handleRemoveCourse
}) => {
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [popupType, setPopupType] = useState("");
  const [popupContent, setPopupContent] = useState(null);

  const fetchCourseDetails = async (course_code) => {
    try {
      const response = await fetch(`${API_BASE_URL}/courses/${course_code}`);
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
    const previewText = text.length > 100 ? text.slice(0, 100) + "..." : text;
  
    return (
      <td className="prereq-expandable">
        {expanded ? text : previewText}
        {text.length > 100 && (
          <span
            className="expand-toggle"
            onClick={(e) => {
              e.stopPropagation(); // prevent table row clicks if needed
              setExpanded(!expanded);
            }}
          >
            {expanded ? " Show less" : " Show more"}
          </span>
        )}
      </td>
    );
  };
  


  return (
    <div>
      <table>
        <thead>
          <tr>
            <th></th>
            <th>COURSES</th>
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
                <br />
                <MultiSelectDropdown
                  major={major}
                  // Pass the filtered options (as objects) to the dropdown.
                  allRequirements={optionsForMajor}
                  selectedFilters={selectedFilters}
                  handleFilterChange={handleFilterChange}
                  clearFilters={clearFilters}
                  // (If your dropdown logic still extracts the raw string from each object, it will work.)
                />
              </th>
            );
          })}
            <th>
              OFFERED
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
            </th>
            <th>PRE-REQ</th>
          </tr>
        </thead>
        <tbody>
          {courses.map((course) => (
            <tr key={course.course_code}>
              <td>
                <button
                  className="remove-btn"
                  onClick={() => handleRemoveCourse(course.course_code)}
                >
                  ✖
                </button>
              </td>
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
                  {course.course_code}
                </b>
                <br />
                {course.course_name}
              </td>
              {Object.keys(allRequirements).map((major) => {
              const reqObjects = course.requirements?.[major] || [];
              // Filter out the ones that don’t match the active (Core/GenEd) filter
              const filteredReqObjects = filterRequirementObjects(reqObjects);

              // If, after filtering, there’s nothing left, return an empty cell
              if (filteredReqObjects.length === 0) {
                return <td key={major}></td>;
              }

              // Otherwise, build the list items using the *filtered* objects
              const formattedRequirements = filteredReqObjects.map((reqObj, index) => {
                const formattedText = reqObj.requirement
                  .replace(/^[^-]+---/, "")
                  .replace(/---/g, " → ");
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

              <td>{course.offered.join(", ")}</td>
              <PrereqCell text={course.prerequisites} />
              </tr>
          ))}
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
