import { create } from 'zustand'
import axios from 'axios'

interface User {
  id: string
  email: string
  display_name: string
  avatar_url?: string
  timezone: string
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isLoading: boolean
  error: string | null

  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName: string) => Promise<void>
  logout: () => void
  refreshTokens: () => Promise<void>
  googleLogin: () => Promise<void>
}

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000'

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  refreshToken: null,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await axios.post(`${API_URL}/api/v1/auth/login`, {
        email,
        password,
      })
      const { access_token, refresh_token, user } = response.data
      localStorage.setItem('token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      set({ user, token: access_token, refreshToken: refresh_token, isLoading: false, error: null })
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail?.message || 'Login failed'
      set({ isLoading: false, error: errorMessage })
      throw error
    }
  },

  register: async (email: string, password: string, displayName: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await axios.post(`${API_URL}/api/v1/auth/register`, {
        email,
        password,
        display_name: displayName,
      })
      const { access_token, refresh_token, user } = response.data
      localStorage.setItem('token', access_token)
      localStorage.setItem('refresh_token', refresh_token)
      set({ user, token: access_token, refreshToken: refresh_token, isLoading: false, error: null })
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail?.message || 'Registration failed'
      set({ isLoading: false, error: errorMessage })
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    set({ user: null, token: null, refreshToken: null, error: null })
  },

  refreshTokens: async () => {
    const { refreshToken } = get()
    if (!refreshToken) return

    try {
      const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
        refresh_token: refreshToken,
      })
      const { access_token } = response.data
      localStorage.setItem('token', access_token)
      set({ token: access_token })
    } catch (error) {
      get().logout()
      throw error
    }
  },

  googleLogin: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await axios.get(`${API_URL}/api/v1/auth/google/url`)
      // Redirect user to Google OAuth URL
      window.location.href = response.data.auth_url
    } catch (error: any) {
      set({ isLoading: false, error: error.response?.data?.detail?.message || 'Failed to initiate Google login' })
      throw error
    }
  },
}))