import React, { useState, useEffect } from 'react';
import { deviceAPI } from '../../services/api';
import Table from '../Common/Table';
import Modal from '../Common/Modal';

const DevicesList = () => {
  const [devices, setDevices] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDevices();
  }, [filter]);

  const loadDevices = async () => {
    try {
      const params = filter !== 'all' ? { status: filter } : {};
      const response = await deviceAPI.getAll(params);
      setDevices(response.data);
    } catch (error) {
      console.error('Error loading devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (deviceId, newStatus) => {
    try {
      await deviceAPI.update(deviceId, { status: newStatus });
      loadDevices();
    } catch (error) {
      console.error('Error updating device:', error);
    }
  };

  if (loading) return <div>Loading devices...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Devices Management</h1>
        <div className="flex space-x-4">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      <Table
        headers={['Device ID', 'Location', 'Status', 'Installation Date', 'Actions']}
        emptyMessage="No devices found"
      >
        {devices.map(device => (
          <tr key={device.id}>
            <td className="table-cell font-mono">{device.device_id}</td>
            <td className="table-cell">
              {device.latitude.toFixed(4)}, {device.longitude.toFixed(4)}
            </td>
            <td className="table-cell">
              <span className={`status-badge ${
                device.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {device.status}
              </span>
            </td>
            <td className="table-cell">{device.installation_date}</td>
            <td className="table-cell space-x-2">
              <button
                onClick={() => handleStatusChange(device.id, 
                  device.status === 'active' ? 'inactive' : 'active'
                )}
                className={`btn-secondary text-xs`}
              >
                {device.status === 'active' ? 'Deactivate' : 'Activate'}
              </button>
            </td>
          </tr>
        ))}
      </Table>
    </div>
  );
};

export default DevicesList;