import React, { useState } from "react";
import CourseTablePage from "./CourseTablePage";
import PlanCourseTab from "./PlanCourseTab"; 

const MainTabs = () => {
  const [activeTab, setActiveTab] = useState("general");

  return (
    <div>
      {/* Tab Selector */}
      <div className="tab-bar">
        <button
          className={activeTab === "general" ? "tab active" : "tab"}
          onClick={() => setActiveTab("general")}
        >
          View
        </button>
        <button
          className={activeTab === "plan" ? "tab active" : "tab"}
          onClick={() => setActiveTab("plan")}
        >
          Plan
        </button>
        <button
          className={activeTab === "analytics" ? "tab active" : "tab"}
          onClick={() => setActiveTab("analytics")}
        >
          Analytics
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === "general" && <CourseTablePage />}
        {activeTab === "plan" && <PlanCourseTab />}
      </div>
    </div>
  );
};

export default MainTabs;
