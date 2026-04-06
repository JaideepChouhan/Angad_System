import React, { useState } from 'react';
import { deviceAPI } from '../../services/api';

const DeviceRegistration = () => {
  const [formData, setFormData] = useState({
    device_id: '',
    latitude: '',
    longitude: '',
    installation_date: ''
  });
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    
    try {
      await deviceAPI.create({
        ...formData,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude)
      });
      
      setMessage('Device registered successfully!');
      setFormData({
        device_id: '',
        latitude: '',
        longitude: '',
        installation_date: ''
      });
    } catch (error) {
      setMessage('Error registering device: ' + (error.response?.data?.error || error.message));
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Device Registration</h1>
        
        {message && (
          <div className={`p-4 rounded-md mb-4 ${
            message.includes('Error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
          }`}>
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Device ID</label>
            <input
              type="text"
              required
              pattern="device\d{4}"
              title="Device ID must be in format device0001, device0002, etc."
              value={formData.device_id}
              onChange={(e) => setFormData(prev => ({ ...prev, device_id: e.target.value }))}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="device0001"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Latitude</label>
              <input
                type="number"
                step="any"
                required
                min="-90"
                max="90"
                value={formData.latitude}
                onChange={(e) => setFormData(prev => ({ ...prev, latitude: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="12.3456"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Longitude</label>
              <input
                type="number"
                step="any"
                required
                min="-180"
                max="180"
                value={formData.longitude}
                onChange={(e) => setFormData(prev => ({ ...prev, longitude: e.target.value }))}
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="78.9012"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Installation Date</label>
            <input
              type="text"
              required
              pattern="\d{2}/\d{2}/\d{4}"
              title="Date must be in DD/MM/YYYY format"
              value={formData.installation_date}
              onChange={(e) => setFormData(prev => ({ ...prev, installation_date: e.target.value }))}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="DD/MM/YYYY"
            />
          </div>

          <button type="submit" className="w-full btn-primary">
            Register Device
          </button>
        </form>
      </div>
    </div>
  );
};

export default DeviceRegistration;