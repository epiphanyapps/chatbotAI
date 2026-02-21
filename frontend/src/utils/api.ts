const API_BASE = '/api'

export async function api(path: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }))
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}

export function setAuthToken(token: string) {
  localStorage.setItem('access_token', token)
}

export function getAuthToken(): string | null {
  return localStorage.getItem('access_token')
}

export function clearAuthToken() {
  localStorage.removeItem('access_token')
}

export async function apiWithAuth(path: string, options: RequestInit = {}) {
  const token = getAuthToken()
  return api(path, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: token ? `Bearer ${token}` : ''
    }
  })
}
