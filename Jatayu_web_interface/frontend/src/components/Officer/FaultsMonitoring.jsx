import React, { useState, useEffect } from 'react';
import { faultAPI, linemanAPI } from '../../services/api';
import Table from '../Common/Table';
import Modal from '../Common/Modal';
import { useSocket } from '../../hooks/useSocket';

const FaultsMonitoring = () => {
  const [faults, setFaults] = useState([]);
  const [linemen, setLinemen] = useState([]);
  const [filters, setFilters] = useState({ status: 'all', severity: 'all' });
  const [assignModal, setAssignModal] = useState({ open: false, fault: null });

  useEffect(() => {
    loadFaults();
    loadLinemen();
  }, [filters]);

  useSocket('fault_detected', (newFault) => {
    setFaults(prev => [newFault, ...prev]);
  });

  useSocket('fault_updated', (updatedFault) => {
    setFaults(prev => prev.map(f => f.id === updatedFault.id ? updatedFault : f));
  });

  const loadFaults = async () => {
    try {
      const params = {};
      if (filters.status !== 'all') params.status = filters.status;
      if (filters.severity !== 'all') params.severity = filters.severity;
      
      const response = await faultAPI.getAll(params);
      setFaults(response.data);
    } catch (error) {
      console.error('Error loading faults:', error);
    }
  };

  const loadLinemen = async () => {
    try {
      const response = await linemanAPI.getAll({ status: 'available' });
      setLinemen(response.data);
    } catch (error) {
      console.error('Error loading linemen:', error);
    }
  };

  const handleAssign = async (faultId, linemanId) => {
    try {
      await faultAPI.assign(faultId, linemanId);
      setAssignModal({ open: false, fault: null });
      loadFaults();
    } catch (error) {
      console.error('Error assigning fault:', error);
    }
  };

  const getSeverityClass = (severity) => {
    const classes = {
      low: 'severity-low',
      medium: 'severity-medium',
      high: 'severity-high',
      critical: 'severity-critical'
    };
    return classes[severity] || 'severity-medium';
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Faults Monitoring</h1>
        <div className="flex space-x-4">
          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="all">All Status</option>
            <option value="detected">Detected</option>
            <option value="assigned">Assigned</option>
            <option value="in-progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
          <select
            value={filters.severity}
            onChange={(e) => setFilters(prev => ({ ...prev, severity: e.target.value }))}
            className="border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="all">All Severity</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <Table
        headers={['Device', 'Fault Type', 'Severity', 'Timestamp', 'Status', 'Assigned To', 'Actions']}
        emptyMessage="No faults detected"
      >
        {faults.map(fault => (
          <tr key={fault.id}>
            <td className="table-cell font-mono">{fault.device_info?.device_id}</td>
            <td className="table-cell capitalize">{fault.fault_type}</td>
            <td className="table-cell">
              <span className={`status-badge ${getSeverityClass(fault.severity)}`}>
                {fault.severity}
              </span>
            </td>
            <td className="table-cell">
              {new Date(fault.timestamp).toLocaleString()}
            </td>
            <td className="table-cell">
              <span className={`status-badge ${
                fault.status === 'resolved' ? 'bg-green-100 text-green-800' :
                fault.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                fault.status === 'assigned' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {fault.status}
              </span>
            </td>
            <td className="table-cell">
              {fault.lineman_info?.name || 'Not assigned'}
            </td>
            <td className="table-cell space-x-2">
              {fault.status === 'detected' && (
                <button
                  onClick={() => setAssignModal({ open: true, fault })}
                  className="btn-primary text-xs"
                >
                  Assign
                </button>
              )}
            </td>
          </tr>
        ))}
      </Table>

      <Modal
        isOpen={assignModal.open}
        onClose={() => setAssignModal({ open: false, fault: null })}
        title="Assign Fault to Lineman"
      >
        {assignModal.fault && (
          <div className="space-y-4">
            <p>Assign fault at {assignModal.fault.device_info?.device_id} to:</p>
            <select className="w-full border border-gray-300 rounded-md px-3 py-2">
              <option value="">Select Lineman</option>
              {linemen.map(lineman => (
                <option key={lineman.id} value={lineman.id}>
                  {lineman.name} - {lineman.assigned_area}
                </option>
              ))}
            </select>
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => setAssignModal({ open: false, fault: null })}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const select = document.querySelector('select');
                  if (select.value) {
                    handleAssign(assignModal.fault.id, parseInt(select.value));
                  }
                }}
                className="btn-primary"
              >
                Assign
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default FaultsMonitoring;