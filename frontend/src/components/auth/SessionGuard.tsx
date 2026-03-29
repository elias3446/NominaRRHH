import { useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useWebSocket } from "@/hooks/useWebSocket";
import { toast } from "sonner";

export const SessionGuard = ({ children }: { children: React.ReactNode }) => {
  const { user, logout } = useAuth();

  // Canal universal de notificaciones para el usuario autenticado
  const wsUrl = user 
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${import.meta.env.VITE_API_URL 
        ? new URL(import.meta.env.VITE_API_URL).host 
        : "localhost:8000"}/ws/users/`
    : null;

  const { lastMessage } = useWebSocket(wsUrl);

  useEffect(() => {
    if (lastMessage && (lastMessage.type === "force_logout" || lastMessage.type === "auth_error")) {
      toast.error("Sesión terminada", {
        description: lastMessage.message || "Tu acceso ha sido revocado.",
      });
      logout();
    }
  }, [lastMessage, logout]);

  return <>{children}</>;
};
