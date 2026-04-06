import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = ({ userRole, onLogout }) => {
  const location = useLocation();

  const officerLinks = [
    { to: '/officer/devices', label: 'Devices' },
    { to: '/officer/faults', label: 'Fault Monitoring' },
    { to: '/officer/linemen', label: 'Linemen Management' },
  ];

  const linemanLinks = [
    { to: '/lineman/devices', label: 'Device Registration' },
    { to: '/lineman/faults', label: 'Assigned Faults' },
  ];

  const links = userRole === 'officer' ? officerLinks : linemanLinks;

  return (
    <nav className="bg-blue-600 shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-white text-xl font-bold">
              Fault Detection System
            </Link>
            <div className="ml-10 flex items-baseline space-x-4">
              {links.map(link => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    location.pathname === link.to
                      ? 'bg-blue-700 text-white'
                      : 'text-blue-100 hover:bg-blue-500'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-blue-100 mr-4">
              Logged in as {userRole}
            </span>
            <button
              onClick={onLogout}
              className="bg-blue-500 hover:bg-blue-400 text-white px-4 py-2 rounded-md text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;