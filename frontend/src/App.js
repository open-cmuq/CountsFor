// import CourseTableMock from "./components/courseTableMock/courseTableMock.js";
// import CourseTableMock from "./components/CourseTablePage";
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainTabs from "./components/MainTabs";
// import CourseTablePage from './components/CourseTablePage';
import DataUpload from './components/DataUpload';
import AnalyticsPage from './components/Analytics';
import "./styles.css";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainTabs />} />
        <Route path="/upload" element={<DataUpload />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Routes>
    </Router>
  );
};

export default App;
