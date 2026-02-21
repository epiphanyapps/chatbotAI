import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api, apiWithAuth, setAuthToken, getAuthToken, clearAuthToken } from '../utils/api'

interface User {
  email: string
  age_verified: boolean
}

interface AuthContextType {
  isAuthenticated: boolean
  isAgeVerified: boolean
  user: User | null
  loading: boolean
  login: (token: string) => void
  logout: () => Promise<void>
  refreshToken: () => Promise<boolean>
  checkAgeStatus: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const checkAgeStatus = async () => {
    try {
      const data = await apiWithAuth('/legal/age-status')
      setUser(prev => prev ? { ...prev, age_verified: data.age_verified } : null)
    } catch (error) {
      console.error('Failed to check age status:', error)
    }
  }

  const refreshToken = async (): Promise<boolean> => {
    try {
      const data = await api('/auth/refresh', { method: 'POST' })
      setAuthToken(data.access_token)
      return true
    } catch (error) {
      clearAuthToken()
      setUser(null)
      return false
    }
  }

  const login = (token: string) => {
    setAuthToken(token)
    // Will trigger checkAgeStatus on next render
    setUser({ email: '', age_verified: false })
  }

  const logout = async () => {
    try {
      await api('/auth/logout', { method: 'POST' })
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuthToken()
      setUser(null)
    }
  }

  useEffect(() => {
    const initAuth = async () => {
      const token = getAuthToken()
      if (!token) {
        setLoading(false)
        return
      }

      // Try to verify token by checking age status
      try {
        const data = await apiWithAuth('/legal/age-status')
        setUser({ email: '', age_verified: data.age_verified })
      } catch (error) {
        // Token might be expired, try refresh
        const refreshed = await refreshToken()
        if (refreshed) {
          try {
            const data = await apiWithAuth('/legal/age-status')
            setUser({ email: '', age_verified: data.age_verified })
          } catch {
            clearAuthToken()
          }
        }
      }
      setLoading(false)
    }

    initAuth()
  }, [])

  return (
    <AuthContext.Provider value={{
      isAuthenticated: !!user,
      isAgeVerified: user?.age_verified ?? false,
      user,
      loading,
      login,
      logout,
      refreshToken,
      checkAgeStatus
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
