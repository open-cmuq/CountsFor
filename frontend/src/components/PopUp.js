import React from "react";
import Draggable from "react-draggable";
import { ResizableBox } from "react-resizable";

const Popup = ({ isOpen, onClose, type, content }) => {
  if (!isOpen) return null;

  return (
    <div className="popup-overlay">
      <Draggable handle=".popup-header">
        <ResizableBox width={400} height={300} minConstraints={[300, 200]} maxConstraints={[800, 600]}>
          <div className="popup-content">
            {/* Header (Drag Handle) */}
            <div className="popup-header">
              <span>{type === "course" ? "Course Details" : "Courses for Requirement"}</span>
              <button className="close-btn" onClick={onClose}>✖</button>
            </div>

            {/* Popup Content */}
            <div className="popup-body">
              {type === "course" ? (
                <>
                  <p><b>Course Code:</b> {content.course_code}</p>
                  <p><b>Course Name:</b> {content.course_name}</p>
                  <p><b>Prerequisites:</b> {content.prerequisites || "None"}</p>
                  <p><b>Offered:</b> {content.offered?.join(", ") || "N/A"}</p>
                  <p><b>Description:</b> {content.description || "No description available."}</p>
                </>
              ) : type === "requirement" ? (
                <>
                  <p><b>Requirement:</b> {content.requirement}</p>
                  <ul>
                    {content.courses.length > 0 ? (
                      content.courses.map((course) => (
                        <li key={course.course_code}>
                          {course.course_code} - {course.course_name}
                        </li>
                      ))
                    ) : (
                      <p>No courses fulfill this requirement.</p>
                    )}
                  </ul>
                </>
              ) : null}
            </div>
          </div>
        </ResizableBox>
      </Draggable>
    </div>
  );
};

export default Popup;
