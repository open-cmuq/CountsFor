import React from "react";

const Popup = ({ isOpen, onClose, type, content, openPopup }) => {
  if (!isOpen) return null;

  // Helper to extract the raw requirement text and format it.
  const formatRequirement = (req) => {
    // If req is an object, extract its 'requirement' property.
    const rawReq = typeof req === "object" ? req.requirement : req;
    const isGenEd = typeof req === "object" && req.type === true;

    // For GenEd requirements, remove everything up to "General Education"
    if (isGenEd && rawReq && rawReq.includes("General Education")) {
      return rawReq.replace(/^.*General Education\s*---/, "").replace(/---/g, " → ");
    }

    // For other requirements, just apply the standard formatting
    return (rawReq || "").replace(/^[^-]+---/, "").replace(/---/g, " → ");
  };

  return (
    <div className="popup-overlay">
      <div className="popup-panel">
        <button className="popup-close-btn" onClick={onClose}>✖</button>

        <h2 className="popup-title">
          {type === "course" ? "Course Details" : "Requirement Details"}
        </h2>

        {type === "course" ? (
          <>
            <p><strong>Course Code:</strong> {content.course_code}</p>
            <p><strong>Name:</strong> {content.course_name}</p>
            <p><strong>Units:</strong> {content.units}</p>
            <p><strong>Description:</strong> {content.description}</p>
            <p>
              <strong>Prerequisites:</strong> {content.prerequisites || "None"}
            </p>
            <p>
              <strong>Semesters Offered:</strong> {content.offered.join(", ")}
            </p>
            <div className="requirements-container">
              <p><strong>Requirements Fulfilled by Course</strong></p>
              {Object.entries(content.requirements)
                .filter(([_, reqs]) => reqs.length > 0)
                .map(([major, reqs]) => (
                  <div key={major} className="requirement-group">
                    <h3>{major}</h3>
                    <ul className="requirement-list">
                      {reqs.map((req, index) => (
                        <li key={index}>{formatRequirement(req)}</li>
                      ))}
                    </ul>
                  </div>
                ))}
            </div>
          </>
        ) : (
          <>
            {content.requirement.map((req, index) => {
              const formattedReq = formatRequirement(req);
              const fulfillingCourses = content.courses.filter((c) =>
                Object.values(c.requirements).some((reqList) =>
                  reqList.some((originalReq) => {
                    const rawOriginal =
                      typeof originalReq === "object"
                        ? originalReq.requirement
                        : originalReq;
                    return rawOriginal.replace(/^[^-]+---/, "").replace(/---/g, " → ") === formattedReq ||
                           rawOriginal === formattedReq;
                  })
                )
              );

              return (
                <div key={index} className="requirement-group">
                  <h3>{formattedReq}</h3>
                  <p className="courses-title">
                    Courses Fulfilling This Requirement{" "}
                    <span className="course-count">[{fulfillingCourses.length}]</span>
                  </p>
                  <ul>
                    {fulfillingCourses.map((c, idx) => (
                      <li key={idx}>
                        <span
                          className="course-link"
                          onClick={() => openPopup("course", c)}
                        >
                          {c.course_code} - {c.course_name}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
};

export default Popup;
