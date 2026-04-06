import React from "react";
import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="bg-blue-800 text-white p-4 flex justify-between">
      <div>
        <Link to="/officer" className="mr-6 font-bold">
          Officer Dashboard
        </Link>
        <Link to="/lineman/1" className="font-bold">
          Lineman Dashboard
        </Link>
      </div>
    </nav>
  );
}
