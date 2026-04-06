import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import { useParams } from "react-router-dom";
import io from "socket.io-client";

const socket = io("http://127.0.0.1:5000");

export default function LinemanDashboard() {
  const { id } = useParams();
  const [deviceForm, setDeviceForm] = useState({
    device_id: "",
    latitude: "",
    longitude: "",
    installation_date: ""
  });
  const [assignedFaults, setAssignedFaults] = useState([]);

  const fetchFaults = () => {
    api.get("/faults").then(res => {
      const filtered = res.data.filter(
        f => f.assigned_to && f.assigned_to === id
      );
      setAssignedFaults(filtered);
    });
  };

  useEffect(() => {
    fetchFaults();

    socket.on("fault_assigned", () => {
      fetchFaults();
    });

    return () => {
      socket.off("fault_assigned");
      socket.disconnect();
    };
  }, [id]);

  const registerDevice = () => {
    if (
      !deviceForm.device_id ||
      !deviceForm.latitude ||
      !deviceForm.longitude ||
      !deviceForm.installation_date
    )
      return;

    api
      .post("/devices", {
        ...deviceForm,
        latitude: parseFloat(deviceForm.latitude),
        longitude: parseFloat(deviceForm.longitude)
      })
      .then(() =>
        setDeviceForm({
          device_id: "",
          latitude: "",
          longitude: "",
          installation_date: ""
        })
      );
  };

  const updateFaultStatus = (fid, status) => {
    api
      .put(`/faults/${fid}`, { status })
      .then(() => fetchFaults());
  };

  return (
    <div className="p-4 space-y-8">
      {/* Device Registration */}
      <section>
        <h2 className="text-xl font-bold mb-2">Device Registration</h2>
        <div>
          <input
            placeholder="Device ID"
            value={deviceForm.device_id}
            onChange={e =>
              setDeviceForm({ ...deviceForm, device_id: e.target.value })
            }
            className="border p-1 mr-2"
          />
          <input
            placeholder="Latitude"
            type="number"
            step="any"
            value={deviceForm.latitude}
            onChange={e =>
              setDeviceForm({ ...deviceForm, latitude: e.target.value })
            }
            className="border p-1 mr-2"
          />
          <input
            placeholder="Longitude"
            type="number"
            step="any"
            value={deviceForm.longitude}
            onChange={e =>
              setDeviceForm({ ...deviceForm, longitude: e.target.value })
            }
            className="border p-1 mr-2"
          />
          <input
            placeholder="Installation Date (DD/MM/YYYY)"
            value={deviceForm.installation_date}
            onChange={e =>
              setDeviceForm({
                ...deviceForm,
                installation_date: e.target.value
              })
            }
            className="border p-1 mr-2"
          />
          <button
            className="bg-blue-700 text-white px-2 py-1"
            onClick={registerDevice}
          >
            Register Device
          </button>
        </div>
      </section>

      {/* Assigned Faults */}
      <section>
        <h2 className="text-xl font-bold mb-2">Assigned Faults</h2>
        <table className="min-w-full border">
          <thead>
            <tr>
              <th>Device ID</th>
              <th>Location</th>
              <th>Severity</th>
              <th>Detection Time</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {assignedFaults.map(f => (
              <tr key={f.id}>
                <td>{f.device_id}</td>
                <td>
                  {f.location?.lat},{f.location?.lng}
                </td>
                <td>{f.severity}</td>
                <td>{new Date(f.timestamp).toLocaleString()}</td>
                <td>{f.status}</td>
                <td>
                  {f.status === "assigned" && (
                    <button
                      className="bg-yellow-600 text-white px-2 py-1"
                      onClick={() => updateFaultStatus(f.id, "in-progress")}
                    >
                      Start Work
                    </button>
                  )}
                  {f.status === "in-progress" && (
                    <button
                      className="bg-green-700 text-white px-2 py-1"
                      onClick={() => updateFaultStatus(f.id, "resolved")}
                    >
                      Mark Resolved
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
