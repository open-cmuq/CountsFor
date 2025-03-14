import React, { useState } from "react";
import MultiSelectDropdown from "./MultiSelectDropdown";
import Popup from "./PopUp";

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL ||
  (window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000/api"
    : "http://countsfor.qatar.cmu.edu/api");


const CourseTable = ({ courses, allCourses, allRequirements, selectedFilters, handleFilterChange, clearFilters, setVisibleCourses }) => {
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
                <MultiSelectDropdown
                  major={major}
                  allRequirements={allRequirements}
                  selectedFilters={selectedFilters}
                  handleFilterChange={handleFilterChange}
                  clearFilters={clearFilters}
                />
              </th>
            ))}
            <th>PRE-REQ</th>
            <th>OFFERED</th>
          </tr>
        </thead>
        <tbody>
          {courses.map((course) => (
            <tr key={course.course_code}>
              <td>
                <button
                  className="remove-btn"
                  onClick={() =>
                    setVisibleCourses((prev) =>
                      prev.filter((c) => c.course_code !== course.course_code)
                    )
                  }
                >
                  ✖
                </button>
              </td>
              <td>
                <b
                  className="clickable"
                  onClick={() => openPopup("course", course)}
                  style={{ cursor: "pointer", textDecoration: "underline", color: "black" }}
                >
                  {course.course_code}
                </b>
                <br />
                {course.course_name}
              </td>

              {Object.keys(allRequirements).map((major) => {
              const requirements = course.requirements?.[major]?.map(req =>
                typeof req === "string" ? req : req.requirement
              ) || [];


              if (requirements.length === 0) return <td key={major}></td>;

              return (
                <td
                  key={major}
                  className={`cell cell-${major.toLowerCase()}`}
                  onClick={() =>
                    openPopup("requirement", {
                      requirement: requirements,
                      courses: allCourses.filter((c) =>
                        c.requirements?.[major]?.some((r) => requirements.includes(r))
                      ),
                    })
                  }
                  style={{ cursor: "pointer", color: "blue", textAlign: "center" }}
                >
                  {requirements.length === 1 ? (
                    requirements[0] // Display single requirement as text
                  ) : (
                    <ul style={{ margin: "5px 0", paddingLeft: "20px", textAlign: "left" }}>
                      {requirements.map((req, index) => (
                        <li key={index} style={{ listStyleType: "disc" }}>{req}</li>
                      ))}
                    </ul>
                  )}
                </td>
              );
            })}

              <td>{course.prerequisites || "NONE"}</td>
              <td>{course.offered.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Popup Component */}
      <Popup isOpen={isPopupOpen} onClose={closePopup} type={popupType} content={popupContent} openPopup={openPopup}/>
    </div>
  );
};

export default CourseTable;
