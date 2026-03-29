import { tokenStorage } from './tokenStorage';

const getApiUrl = () => {
  const currentHostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
  const envUrlStr = import.meta.env.VITE_API_URL;

  if (envUrlStr) {
    try {
      const urlObj = new URL(envUrlStr);
      if (urlObj.hostname === currentHostname) return envUrlStr;
    } catch (e) {
      // URL inválida, ignorar
    }
  }

  return `http://${currentHostname}:8000/api`;
};

const BASE = getApiUrl();
const API_BASE_URL = BASE.endsWith('/api') ? BASE : `${BASE}/api`;

export const api = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;

  // Construir headers: siempre incluir Content-Type y credenciales para cookies
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  // Fallback: si hay token en storage (para entornos HTTP donde SameSite bloquea cookies),
  // enviarlo como Authorization header. La cookie tiene prioridad si está presente.
  const storedToken = tokenStorage.getAccess();
  if (storedToken && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${storedToken}`;
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Siempre intentar enviar cookies también
  };

  try {
    let response = await fetch(url, config);

    // Auto-Refresh Interceptor
    if (response.status === 401 && !endpoint.includes('/auth/refresh') && !endpoint.includes('/auth/login')) {
      // El 401 en /auth/me es esperado si no hay sesión activa — no es un error real
      const storedRefresh = tokenStorage.getRefresh();
      const refreshBody = storedRefresh ? JSON.stringify({ refresh: storedRefresh }) : undefined;

      const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: refreshBody,
      });

      if (refreshResponse.ok) {
        const refreshData = await refreshResponse.json().catch(() => null);
        // Si el backend devuelve un nuevo access token en el body, actualizarlo en storage
        if (refreshData?.access) {
          tokenStorage.updateAccess(refreshData.access);
          // Reintentar con el nuevo token
          headers['Authorization'] = `Bearer ${refreshData.access}`;
        }
        response = await fetch(url, { ...config, headers });
      } else {
        tokenStorage.clear();
        window.dispatchEvent(new CustomEvent('auth:expired'));
      }
    }

    let data = null;
    const textContent = await response.text();
    if (textContent) {
      try {
        data = JSON.parse(textContent);
      } catch (e) {
        // No era JSON
      }
    }

    if (!response.ok) {
      return { error: data || { message: 'Error de servidor' }, status: response.status };
    }

    return { data, status: response.status };
  } catch (error: any) {
    console.error('API Call Error:', error);
    return { error: { message: error.message || 'No se pudo conectar con el servidor' }, status: 500 };
  }
};
