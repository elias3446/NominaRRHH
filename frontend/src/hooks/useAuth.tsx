import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface User {
  id: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (userData: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { data, error, status } = await api("/auth/me/");
        if (data && !error) {
          setUser(data);
        } else if (status !== 401) {
          console.error("Auth check failed", error);
        }
      } catch (error) {
        // console.error("Auth check failed", error);
      } finally {
        setLoading(false);
      }
    };
    
    checkAuth();

    // Evento de caducidad global emitido por el interceptor del api.ts
    const handleAuthExpired = () => {
      setUser(null);
      // Opcionalmente redirigir o mostrar toast
    };

    window.addEventListener('auth:expired', handleAuthExpired);

    return () => {
      window.removeEventListener('auth:expired', handleAuthExpired);
    };
  }, []);

  const login = (userData: User) => setUser(userData);
  
  const logout = async () => {
    try {
      await api("/auth/logout/", { method: "POST" });
    } catch (e) {
      console.error("Error logging out", e);
    } finally {
      setUser(null);
      window.location.href = "/"; // Redirigir al login
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
