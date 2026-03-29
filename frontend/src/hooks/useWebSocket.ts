import { useState, useEffect, useCallback, useRef } from 'react';
import { tokenStorage } from '@/lib/tokenStorage';

/**
 * Hook de WebSocket con autenticación JWT automática.
 * 
 * Estrategia de auth:
 * 1. Si hay cookies HttpOnly (producción HTTPS) → el browser las envía automáticamente
 * 2. Si hay token en sessionStorage/localStorage (dev HTTP) → se envía como ?token=<jwt>
 *    y el JWTAuthMiddleware del backend lo lee desde los query params.
 */
export const useWebSocket = (url: string | null) => {
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CLOSED);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const buildUrl = useCallback((baseUrl: string): string => {
    const token = tokenStorage.getAccess();
    if (token) {
      // Pasar token como query param para entornos donde las cookies no funcionan
      const separator = baseUrl.includes('?') ? '&' : '?';
      return `${baseUrl}${separator}token=${encodeURIComponent(token)}`;
    }
    return baseUrl;
  }, []);

  const connect = useCallback(() => {
    if (!url) return;
    if (socketRef.current?.readyState === WebSocket.OPEN) return;
    if (socketRef.current?.readyState === WebSocket.CONNECTING) return;

    const fullUrl = buildUrl(url);
    const ws = new WebSocket(fullUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      setReadyState(WebSocket.OPEN);
      // Limpiar timer de reconexión si existía
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
    };

    ws.onclose = (event) => {
      setReadyState(WebSocket.CLOSED);
      // Reconectar automáticamente si no fue un cierre limpio (code 1000)
      if (event.code !== 1000 && url) {
        reconnectTimer.current = setTimeout(() => connect(), 3000);
      }
    };

    ws.onerror = (error) => console.error('WebSocket Error:', error);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (e) {
        setLastMessage(event.data);
      }
    };
  }, [url, buildUrl]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      socketRef.current?.close(1000, 'Component unmounted');
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    }
  }, []);

  return { lastMessage, readyState, sendMessage };
};
