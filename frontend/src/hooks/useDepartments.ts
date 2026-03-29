import { useState, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';

export interface Department {
  id: string;
  name: string;
  description?: string;
}

/**
 * Hook reutilizable para obtener y sincronizar en tiempo real la lista de departamentos.
 * Maneja la conexión WebSocket y espera a que esté abierta antes de pedir datos.
 */
export const useDepartments = () => {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);

  const wsHostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const { lastMessage, sendMessage, readyState } = useWebSocket(
    `ws://${wsHostname}:8000/ws/department-management/`
  );

  // Solicitar la lista cuando la conexión esté abierta
  useEffect(() => {
    if (readyState === WebSocket.OPEN) {
      sendMessage({ action: 'list' });
    }
  }, [readyState, sendMessage]);

  // Procesar mensajes entrantes
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.status === 'success' && lastMessage.action === 'list') {
      setDepartments(lastMessage.data || []);
      setLoading(false);
    }

    // Sincronización en tiempo real
    if (lastMessage.event === 'department_created') {
      setDepartments(prev => {
        if (prev.find(d => d.id === lastMessage.data.id)) return prev;
        return [...prev, lastMessage.data];
      });
    } else if (lastMessage.event === 'department_updated') {
      setDepartments(prev => prev.map(d => d.id === lastMessage.data.id ? lastMessage.data : d));
    } else if (lastMessage.event === 'department_deleted') {
      setDepartments(prev => prev.filter(d => d.id !== lastMessage.data.id));
    }
  }, [lastMessage]);

  return { departments, loading };
};
