// import CourseTableMock from "./components/courseTableMock/courseTableMock.js";
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import DataUpload from './components/DataUpload';
import CourseTablePage from './components/CourseTablePage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<CourseTablePage />} />
        <Route path="/upload" element={<DataUpload />} />
      </Routes>
    </Router>
  );
}

export default App;

