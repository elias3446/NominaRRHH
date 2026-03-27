/**
 * Cliente Maestro para conectar el Frontend (React) con tu Backend (Django)
 * Reemplaza de forma definitiva las conexiones antiguas hacia Supabase.
 */

// Toma la URL dinámicamente que configuramos en el archivo .env principal
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  /**
   * Petición para Obtener datos (Equivalente a supabase.from('...').select())
   */
  get: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        // En un futuro, si usas permisos de usuarios en Django, aquí iría el Token:
        // "Authorization": `Bearer ${localStorage.getItem('token')}`
      },
    });

    if (!response.ok) {
      throw new Error(`Error en API GET [${endpoint}]: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Petición para Insertar datos (Equivalente a supabase.from('...').insert())
   */
  post: async <T>(endpoint: string, bodyData: any): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // "Authorization": `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(bodyData),
    });

    if (!response.ok) {
      throw new Error(`Error en API POST [${endpoint}]: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Petición para Actualizar datos (Equivalente a supabase.from('...').update())
   */
  put: async <T>(endpoint: string, bodyData: any): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "PUT",
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
   * Petición para Eliminar datos (Equivalente a supabase.from('...').delete())
   */
  delete: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: "DELETE",
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
