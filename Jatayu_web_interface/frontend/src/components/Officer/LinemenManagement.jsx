import React, { useState, useEffect } from 'react';
import { linemanAPI } from '../../services/api';
import Table from '../Common/Table';
import Modal from '../Common/Modal';

const LinemenManagement = () => {
  const [linemen, setLinemen] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    contact: '',
    assigned_area: ''
  });

  useEffect(() => {
    loadLinemen();
  }, []);

  const loadLinemen = async () => {
    try {
      const response = await linemanAPI.getAll();
      setLinemen(response.data);
    } catch (error) {
      console.error('Error loading linemen:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await linemanAPI.create(formData);
      setModalOpen(false);
      setFormData({ name: '', contact: '', assigned_area: '' });
      loadLinemen();
    } catch (error) {
      console.error('Error creating lineman:', error);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this lineman?')) {
      try {
        await linemanAPI.delete(id);
        loadLinemen();
      } catch (error) {
        console.error('Error deleting lineman:', error);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Linemen Management</h1>
        <button
          onClick={() => setModalOpen(true)}
          className="btn-primary"
        >
          Register Lineman
        </button>
      </div>

      <Table
        headers={['Name', 'Contact', 'Assigned Area', 'Status', 'Actions']}
        emptyMessage="No linemen registered"
      >
        {linemen.map(lineman => (
          <tr key={lineman.id}>
            <td className="table-cell font-medium">{lineman.name}</td>
            <td className="table-cell">{lineman.contact}</td>
            <td className="table-cell">{lineman.assigned_area}</td>
            <td className="table-cell">
              <span className={`status-badge ${
                lineman.status === 'available' ? 'bg-green-100 text-green-800' :
                lineman.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {lineman.status}
              </span>
            </td>
            <td className="table-cell">
              <button
                onClick={() => handleDelete(lineman.id)}
                className="btn-danger text-xs"
              >
                Remove
              </button>
            </td>
          </tr>
        ))}
      </Table>

      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Register New Lineman"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Contact</label>
            <input
              type="text"
              required
              value={formData.contact}
              onChange={(e) => setFormData(prev => ({ ...prev, contact: e.target.value }))}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Assigned Area</label>
            <input
              type="text"
              required
              value={formData.assigned_area}
              onChange={(e) => setFormData(prev => ({ ...prev, assigned_area: e.target.value }))}
              className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2"
            />
          </div>
          <div className="flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setModalOpen(false)}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary">
              Register
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default LinemenManagement;