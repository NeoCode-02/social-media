import { api } from './client'
import type { TokenResponse, UserMe } from './types'

export interface RegisterBody {
  email: string
  username: string
  password: string
  display_name: string
}

export const registerUser = (body: RegisterBody) => api.post('/auth/register', body)

export const verifyEmail = (email: string, code: string) =>
  api.post<TokenResponse>('/auth/verify-email', { email, code })

export const resendCode = (email: string) => api.post('/auth/resend-code', { email })

export const login = (email: string, password: string) =>
  api.post<TokenResponse>('/auth/login', { email, password })

export const logout = () => api.post('/auth/logout')

export const getMe = () => api.get<UserMe>('/users/me')

export const getWsTicket = async (): Promise<string | null> => {
  try {
    const { data } = await api.get<{ ticket: string }>('/auth/ws-ticket')
    return data.ticket
  } catch {
    return null
  }
}

export const googleLoginUrl = '/api/auth/google/login'
