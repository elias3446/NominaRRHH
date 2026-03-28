/**
 * Cliente Maestro para conectar el Frontend (React) con tu Backend (Django)
 * Reemplaza de forma definitiva las conexiones antiguas hacia Supabase.
 */

// Toma la URL dinámicamente que configuramos en el archivo .env principal
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_BASE_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL}/api`;

export const api = {
  /**
   * Petición para Obtener datos
   */
  get: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "GET",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Error en API GET [${endpoint}]: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Petición para Insertar datos
   */
  post: async <T>(endpoint: string, bodyData: any): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(bodyData),
    });

    if (!response.ok) {
      throw new Error(`Error en API POST [${endpoint}]: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Petición para Actualizar datos
   */
  put: async <T>(endpoint: string, bodyData: any): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PUT",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(bodyData),
    });

    if (!response.ok) {
      throw new Error(`Error en API PUT [${endpoint}]: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Petición para Eliminar datos
   */
  delete: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Error en API DELETE [${endpoint}]: ${response.statusText}`);
    }

    return response.json();
  }
};

