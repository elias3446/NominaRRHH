const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const API_BASE_URL = BASE.endsWith("/api") ? BASE : `${BASE}/api`;

export const api = async (endpoint: string, options: RequestInit = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  // Incluimos las cookies/credenciales automáticamente para SimpleJWT
  const config: RequestInit = {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    credentials: "include", // Importante para enviar HttpOnly cookies
  };

  try {
    let response = await fetch(url, config);
    
    // Auto-Refresh Interceptor
    // Si la ruta no es la del propio refresh/login y obtenemos 401, el access_token caducó.
    if (response.status === 401 && !endpoint.includes('/auth/refresh') && !endpoint.includes('/auth/login')) {
      const refreshResponse = await fetch(`${API_BASE_URL}/auth/refresh/`, {
        method: "POST",
        credentials: "include" // Envía la cookie de refresh sola para conseguir uno nuevo
      });

      if (refreshResponse.ok) {
        // Todo salió bien, el backend inyectó una nueva cookie Access Token
        // ¡Reintentemos la petición original!
        response = await fetch(url, config);
      } else {
        // Si el refresh también falló (caducó el refresh_token o fue blacklistado), es hora de desloguear
        window.dispatchEvent(new CustomEvent('auth:expired'));
      }
    }

    let data = null;
    
    // Solo intentamos parsear si hay contenido
    const textContent = await response.text();
    if (textContent) {
      try {
        data = JSON.parse(textContent);
      } catch (e) {
        // Error de parseo si no era JSON puro
      }
    }

    if (!response.ok) {
      return { error: data || { message: "Error de servidor" }, status: response.status };
    }

    return { data, status: response.status };
  } catch (error: any) {
    console.error("API Call Error:", error);
    return { error: { message: error.message || "No se pudo conectar con el servidor" }, status: 500 };
  }
};
