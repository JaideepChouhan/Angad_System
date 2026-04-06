import React, { useState, useEffect } from 'react';
import { faultAPI } from '../../services/api';
import Table from '../Common/Table';
import { useSocket } from '../../hooks/useSocket';

// Mock lineman ID - in real app, this would come from authentication
const LINEMAN_ID = 1;

const AssignedFaults = () => {
  const [faults, setFaults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFaults();
  }, []);

  useSocket('fault_assigned', (fault) => {
    if (fault.assigned_to === LINEMAN_ID) {
      setFaults(prev => [fault, ...prev]);
    }
  });

  useSocket('fault_updated', (updatedFault) => {
    setFaults(prev => prev.map(f => f.id === updatedFault.id ? updatedFault : f));
  });

  const loadFaults = async () => {
    try {
      const response = await faultAPI.getAll({ status: 'assigned,in-progress' });
      // Filter faults assigned to this lineman
      const assignedFaults = response.data.filter(fault => fault.assigned_to === LINEMAN_ID);
      setFaults(assignedFaults);
    } catch (error) {
      console.error('Error loading faults:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateFaultStatus = async (faultId, newStatus) => {
    try {
      await faultAPI.update(faultId, { status: newStatus });
      loadFaults();
    } catch (error) {
      console.error('Error updating fault status:', error);
    }
  };

  if (loading) return <div>Loading assigned faults...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Assigned Faults</h1>

      <Table
        headers={['Device', 'Fault Type', 'Severity', 'Detection Time', 'Status', 'Actions']}
        emptyMessage="No faults assigned to you"
      >
        {faults.map(fault => (
          <tr key={fault.id}>
            <td className="table-cell font-mono">{fault.device_info?.device_id}</td>
            <td className="table-cell capitalize">{fault.fault_type}</td>
            <td className="table-cell">
              <span className={`status-badge ${
                fault.severity === 'low' ? 'severity-low' :
                fault.severity === 'medium' ? 'severity-medium' :
                fault.severity === 'high' ? 'severity-high' : 'severity-critical'
              }`}>
                {fault.severity}
              </span>
            </td>
            <td className="table-cell">
              {new Date(fault.timestamp).toLocaleString()}
            </td>
            <td className="table-cell">
              <span className={`status-badge ${
                fault.status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                fault.status === 'resolved' ? 'bg-green-100 text-green-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {fault.status}
              </span>
            </td>
            <td className="table-cell space-x-2">
              {fault.status === 'assigned' && (
                <button
                  onClick={() => updateFaultStatus(fault.id, 'in-progress')}
                  className="btn-primary text-xs"
                >
                  Start Work
                </button>
              )}
              {fault.status === 'in-progress' && (
                <button
                  onClick={() => updateFaultStatus(fault.id, 'resolved')}
                  className="btn-primary text-xs"
                >
                  Mark Resolved
                </button>
              )}
            </td>
          </tr>
        ))}
      </Table>
    </div>
  );
};

export default AssignedFaults;