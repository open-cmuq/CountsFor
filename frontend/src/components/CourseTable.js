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

  return (
    <div>
      <table>
        <thead>
          <tr>
            <th></th>
            <th>COURSES</th>
            {Object.keys(allRequirements).map((major) => (
              <th key={major} className={`header-${major.toLowerCase()}`}>
                {major}
                <br />
                {/* For filtering, we pass an array of strings (requirement texts) */}
                <MultiSelectDropdown
                  major={major}
                  allRequirements={allRequirements[major]} // pass directly!
                  selectedFilters={selectedFilters}
                  handleFilterChange={handleFilterChange}
                  clearFilters={clearFilters}
                />
              </th>
            ))}
            <th>
              OFFERED
              <br />
              <MultiSelectDropdown
                major="offered"
                allRequirements={offeredOptions}
                // Wrap our offered filter state in an object so the dropdown works as expected
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
                  onClick={() =>
                    console.log("Remove", course.course_code)
                  }
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
                // Get the array of requirement objects for this major
                const reqObjects = course.requirements?.[major] || [];
                if (reqObjects.length === 0) return <td key={major}></td>;

                // Map each requirement object to a formatted element.
                const formattedRequirements = reqObjects.map((reqObj, index) => {
                  const formattedText = reqObj.requirement
                    .replace(/^[^-]+---/, "")
                    .replace(/---/g, " → ");
                  return reqObj.type
                    ? <i key={index}>{formattedText}</i>  // Italics for GenEd
                    : <b key={index}>{formattedText}</b>; // Bold for Core
                });

                return (
                  <td
                    key={major}
                    className={`cell cell-${major.toLowerCase()}`}
                    onClick={() =>
                      openPopup("requirement", {
                        requirement: reqObjects, // Pass raw requirement objects to the popup
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
