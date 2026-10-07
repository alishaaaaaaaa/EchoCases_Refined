// API client: keeps the login token and attaches it to every request.
//
// The token lives in sessionStorage, so it is cleared when the tab closes and
// is never shared across tabs. It expires on the server after 8 hours anyway.

export const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000/api';

const TOKEN_KEY = 'echocases_token';
const USER_KEY = 'echocases_user';

let onUnauthorized = () => {};
// Fallback copy for browsers where sessionStorage is blocked.
let memorySession = null;

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export function getSession() {
  try {
    const token = sessionStorage.getItem(TOKEN_KEY);
    const user = JSON.parse(sessionStorage.getItem(USER_KEY) || 'null');
    return token && user ? { token, user } : memorySession;
  } catch {
    return memorySession;
  }
}

export function clearSession() {
  memorySession = null;
  try {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
  } catch {
    // storage unavailable; nothing to clear
  }
}

export async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'Login failed.');
  }
  memorySession = { token: data.token, user: data.user };
  try {
    sessionStorage.setItem(TOKEN_KEY, data.token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(data.user));
  } catch {
    // storage unavailable: session lasts until reload
  }
  return { token: data.token, user: data.user };
}

// fetch() with the token attached. A 401 means the session is gone
// (expired, signed out, or the account was deactivated), so we sign out.
export async function apiFetch(path, options = {}) {
  const session = getSession();
  const headers = { ...(options.headers || {}) };
  if (session) headers.Authorization = `Bearer ${session.token}`;

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401) {
    clearSession();
    onUnauthorized();
  }
  return response;
}
