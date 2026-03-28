import { useState, useEffect, useCallback, useRef } from 'react';

export const useWebSocket = (url: string) => {
  const [lastMessage, setLastMessage] = useState<any>(null);
  const [readyState, setReadyState] = useState(WebSocket.CLOSED);
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!url || socketRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);
    socketRef.current = ws;

    ws.onopen = () => setReadyState(WebSocket.OPEN);
    ws.onclose = () => setReadyState(WebSocket.CLOSED);
    ws.onerror = (error) => console.error("WebSocket Error:", error);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (e) {
        setLastMessage(event.data);
      }
    };
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      socketRef.current?.close();
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    }
  }, []);

  return { lastMessage, readyState, sendMessage };
};
