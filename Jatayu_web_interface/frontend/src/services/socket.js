import { io } from 'socket.io-client';

const SOCKET_URL = 'http://localhost:5000';

class SocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect() {
    this.socket = io(SOCKET_URL);
    
    this.socket.on('connect', () => {
      console.log('Connected to server');
      this.emitEvent('connected', true);
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from server');
      this.emitEvent('disconnected', true);
    });

    // Register all event listeners
    this.setupEventListeners();
  }

  setupEventListeners() {
    const events = [
      'fault_detected',
      'fault_updated',
      'fault_assigned',
      'device_created',
      'device_updated',
      'device_deleted',
      'lineman_created',
      'lineman_updated',
      'lineman_deleted'
    ];

    events.forEach(event => {
      this.socket.on(event, (data) => {
        this.emitEvent(event, data);
      });
    });
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emitEvent(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        callback(data);
      });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export const socketService = new SocketService();