// Central helper for talking to the Handoff backend.
// Every page uses apiFetch so the login token is attached
// automatically and expired sessions are handled in one place.

export const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const TOKEN_KEY = 'handoffToken'
const USER_KEY = 'handoffUser'
const ROLE_KEY = 'userRole'

export function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
  localStorage.setItem(ROLE_KEY, user.role)
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(ROLE_KEY)
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getCurrentUser() {
  const stored = localStorage.getItem(USER_KEY)
  return stored ? JSON.parse(stored) : null
}

// Reads the expiry time inside the token. This only improves the
// user experience; the backend still verifies every request.
function tokenIsExpired(token) {
  try {
    const payloadPart = token
      .split('.')[1]
      .replace(/-/g, '+')
      .replace(/_/g, '/')

    const payload = JSON.parse(atob(payloadPart))

    return payload.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

export function isLoggedIn() {
  const token = getToken()

  if (!token) {
    return false
  }

  if (tokenIsExpired(token)) {
    clearSession()
    return false
  }

  return true
}

// FastAPI returns validation errors as a list, so this turns
// any error response into a readable sentence.
export function errorMessage(data, fallback) {
  return typeof data?.detail === 'string' ? data.detail : fallback
}

export async function apiFetch(path, options = {}) {
  const headers = { ...options.headers }
  const token = getToken()

  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers
  })

  // The server rejected our token (expired or invalid).
  if (response.status === 401 && token) {
    clearSession()
    window.location.href = '/login'
  }

  return response
}