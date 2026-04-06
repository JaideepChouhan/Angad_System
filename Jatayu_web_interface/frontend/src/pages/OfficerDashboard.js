import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import io from "socket.io-client";

const socket = io("http://127.0.0.1:5000");

export default function OfficerDashboard() {
  const [devices, setDevices] = useState([]);
  const [faults, setFaults] = useState([]);
  const [linemen, setLinemen] = useState([]);
  const [linemanForm, setLinemanForm] = useState({ name: "", contact: "", assigned_area: "" });

  useEffect(() => {
    api.get("/devices").then((res) => setDevices(res.data));
    api.get("/faults").then((res) => setFaults(res.data));
    api.get("/linemen").then((res) => setLinemen(res.data));
    socket.on("new_fault", () => api.get("/faults").then((res) => setFaults(res.data)));
    socket.on("fault_update", () => api.get("/faults").then((res) => setFaults(res.data)));
    socket.on("lineman_update", () => api.get("/linemen").then((res) => setLinemen(res.data)));
    return () => socket.disconnect();
  }, []);

  const registerLineman = () => {
    if(!linemanForm.name || !linemanForm.contact || !linemanForm.assigned_area) return;
    api.post("/linemen", linemanForm).then(() => api.get("/linemen").then((res) => setLinemen(res.data)));
    setLinemanForm({ name: "", contact: "", assigned_area: "" });
  };
  const removeLineman = (id) => api.delete(`/linemen/${id}`).then(() => api.get("/linemen").then((res) => setLinemen(res.data)));

  return (
    <div className="p-4 space-y-8">
      <section>
        <h2 className="text-xl font-bold mb-2">Devices List</h2>
        <table className="min-w-full border">
          <thead><tr><th>Device ID</th><th>Location</th><th>Status</th><th>Installation Date</th></tr></thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.id}><td>{d.device_id}</td><td>{d.latitude},{d.longitude}</td><td>{d.status}</td><td>{d.installation_date}</td></tr>
            ))}
          </tbody>
        </table>
      </section>
      <section>
        <h2 className="text-xl font-bold mb-2">Faults Monitoring</h2>
        <table className="min-w-full border">
          <thead>
            <tr>
              <th>Device ID</th>
              <th>Type</th>
              <th>Severity</th>
              <th>Timestamp</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {faults.map((f) => (
              <tr key={f.id}
                className={
                  f.severity === "critical"
                    ? "bg-red-600 text-white"
                    : f.severity === "high"
                    ? "bg-yellow-600"
                    : f.severity === "medium"
                    ? "bg-yellow-200"
                    : ""}
              >
                <td>{f.device_id}</td>
                <td>{f.fault_type}</td>
                <td>{f.severity}</td>
                <td>{new Date(f.timestamp).toLocaleString()}</td>
                <td>{f.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section>
        <h2 className="text-xl font-bold mb-2">Linemen Management</h2>
        <div className="mb-4">
          <input
            placeholder="Name"
            value={linemanForm.name}
            onChange={(e) => setLinemanForm({ ...linemanForm, name: e.target.value })}
            className="border p-1 mr-2"
          />
          <input
            placeholder="Contact"
            value={linemanForm.contact}
            onChange={(e) => setLinemanForm({ ...linemanForm, contact: e.target.value })}
            className="border p-1 mr-2"
          />
          <input
            placeholder="Assigned Area"
            value={linemanForm.assigned_area}
            onChange={(e) => setLinemanForm({ ...linemanForm, assigned_area: e.target.value })}
            className="border p-1 mr-2"
          />
          <button className="bg-blue-700 text-white px-2 py-1" onClick={registerLineman}>Register Lineman</button>
        </div>
        <table className="min-w-full border">
          <thead>
            <tr>
              <th>Name</th>
              <th>Contact</th>
              <th>Assigned Area</th>
              <th>Status</th>
              <th>Remove</th>
            </tr>
          </thead>
          <tbody>
            {linemen.map((l) => (
              <tr key={l.id}>
                <td>{l.name}</td>
                <td>{l.contact}</td>
                <td>{l.assigned_area}</td>
                <td>{l.status}</td>
                <td>
                  <button className="bg-red-700 text-white px-2 py-1" onClick={() => removeLineman(l.id)}>Remove</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
