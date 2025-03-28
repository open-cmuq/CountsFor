<<<<<<< HEAD
import React, { useState } from "react";
import CourseTablePage from "./components/CourseTablePage";
import AnalyticsPage from "./components/Analytics";
import "./styles.css";

const App = () => {
  const [currentPage, setCurrentPage] = useState("table");
=======
// import CourseTableMock from "./components/courseTableMock/courseTableMock.js";
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DataUpload from './components/DataUpload';
import CourseTablePage from './components/CourseTablePage';
>>>>>>> main

  return (
<<<<<<< HEAD
    <div>
      <nav style={{ padding: "10px", backgroundColor: "#eee", marginBottom: "20px" }}>
        <button onClick={() => setCurrentPage("table")}>Main Page</button>
        <button onClick={() => setCurrentPage("analytics")} style={{ marginLeft: "10px" }}>
          Analytics Page
        </button>
      </nav>
      {currentPage === "table" ? <CourseTablePage /> : <AnalyticsPage />}
    </div>
=======
    <Router>
      <Routes>
        <Route path="/" element={<CourseTablePage />} />
        <Route path="/upload" element={<DataUpload />} />
      </Routes>
    </Router>
>>>>>>> main
  );
};

export default App;
