import React, { useState, useEffect } from "react";
import CourseTablePage from "./CourseTablePage";
import PlanCourseTab from "./PlanCourseTab";
import AnalyticsPage from "./Analytics";

const MainTabs = () => {
  // Use localStorage to persist the active tab
  const [activeTab, setActiveTab] = useState(() => {
    const savedTab = localStorage.getItem("activeTab");
    return savedTab || "general";
  });

  // Update localStorage when activeTab changes
  useEffect(() => {
    localStorage.setItem("activeTab", activeTab);
  }, [activeTab]);

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
        {activeTab === "general" && <CourseTablePage key="general" />}
        {activeTab === "plan" && <PlanCourseTab key="plan" />}
        {activeTab === "analytics" && <AnalyticsPage key="analytics" />}
      </div>
    </div>
  );
};

export default MainTabs;
