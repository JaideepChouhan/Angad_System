import { useEffect, useRef } from 'react';
import { socketService } from '../services/socket';

export const useSocket = (event, callback) => {
  const callbackRef = useRef(callback);

  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const handler = (data) => callbackRef.current(data);
    
    socketService.on(event, handler);
    
    return () => {
      socketService.off(event, handler);
    };
  }, [event]);
};