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
                  onClick={() => console.log("Remove", course.course_code)}
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
                if (reqObjects.length === 0) return <td key={major}></td>;

                const filteredReqObjects = filterRequirementObjects(reqObjects);

                // Map each filtered requirement object to a formatted element.
                const formattedRequirements = filteredReqObjects.map((reqObj, index) => {
                  const formattedText = reqObj.requirement
                    .replace(/^[^-]+---/, "")
                    .replace(/---/g, " → ");
                  return reqObj.type
                    ? <i key={index}>{formattedText}</i>
                    : <b key={index}>{formattedText}</b>;
                });

                return (
                  <td
                    key={major}
                    className={`cell cell-${major.toLowerCase()}`}
                    onClick={() =>
                      openPopup("requirement", {
                        requirement: filteredReqObjects,
                        courses: courses.filter((c) =>
                          c.requirements?.[major]?.some(
                            (rObj) => rObj.requirement === reqObjects[0].requirement
                          )
                        ),
                      })
                    }
                    style={{
                      cursor: "pointer",
                      color: "blue",
                      textAlign: "left",
                    }}
                  >
                    <ul
                      style={{
                        margin: "5px 0",
                        paddingLeft: "20px",
                        textAlign: "left",
                      }}
                    >
                      {formattedRequirements.map((el, index) => (
                        <li key={index} style={{ listStyleType: "disc" }}>
                          {el}
                        </li>
                      ))}
                    </ul>
                  </td>
                );
              })}
              <td>{course.offered.join(", ")}</td>
              <td>{course.prerequisites || "NONE"}</td>
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
