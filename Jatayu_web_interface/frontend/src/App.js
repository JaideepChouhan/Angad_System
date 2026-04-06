import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import OfficerDashboard from "./pages/OfficerDashboard";
import LinemanDashboard from "./pages/LinemanDashboard";

function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/officer" element={<OfficerDashboard />} />
        <Route path="/lineman/:id" element={<LinemanDashboard />} />
        <Route path="/" element={<OfficerDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;
