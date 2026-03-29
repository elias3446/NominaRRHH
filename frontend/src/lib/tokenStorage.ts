/**
 * Token Storage - Fallback para entornos donde las HttpOnly cookies no funcionan
 * (p.ej.: frontend en puerto 3000, backend en puerto 8000 con HTTP - SameSite issues)
 *
 * Prioridad de autenticación:
 *  1. HttpOnly Cookie (enviada automáticamente por el browser si no hay restricción SameSite)
 *  2. sessionStorage/localStorage → enviado como "Authorization: Bearer <token>" header
 */

const ACCESS_KEY = 'nom_access';
const REFRESH_KEY = 'nom_refresh';

export const tokenStorage = {
  setTokens(access: string, refresh: string, persist = false) {
    const storage = persist ? localStorage : sessionStorage;
    storage.setItem(ACCESS_KEY, access);
    storage.setItem(REFRESH_KEY, refresh);
  },

  getAccess(): string | null {
    return sessionStorage.getItem(ACCESS_KEY) ?? localStorage.getItem(ACCESS_KEY);
  },

  getRefresh(): string | null {
    return sessionStorage.getItem(REFRESH_KEY) ?? localStorage.getItem(REFRESH_KEY);
  },

  updateAccess(access: string) {
    // Actualizar en el almacén donde fue guardado originalmente
    if (localStorage.getItem(REFRESH_KEY)) {
      localStorage.setItem(ACCESS_KEY, access);
    } else {
      sessionStorage.setItem(ACCESS_KEY, access);
    }
  },

  clear() {
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },

  hasTokens(): boolean {
    return !!(this.getAccess());
  },
};
