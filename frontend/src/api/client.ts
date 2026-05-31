import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

// Relative baseURL → dev proxy (vite) / same-origin (prod) forwards to backend.
export const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // send refresh-token cookie
})

// Access token kept in memory; refresh token lives in an httpOnly cookie.
let accessToken: string | null = null
let onAuthFail: (() => void) | null = null

export function setAccessToken(token: string | null): void {
  accessToken = token
}
export function getAccessToken(): string | null {
  return accessToken
}
export function setOnAuthFail(cb: () => void): void {
  onAuthFail = cb
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

let refreshing: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  try {
    const { data } = await axios.post<{ access_token: string }>(
      '/api/auth/refresh',
      {},
      { withCredentials: true },
    )
    accessToken = data.access_token
    return accessToken
  } catch {
    return null
  }
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const config = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined
    const url = config?.url ?? ''
    if (error.response?.status === 401 && config && !config._retry && !url.includes('/auth/')) {
      config._retry = true
      refreshing ??= refreshAccessToken()
      const token = await refreshing
      refreshing = null
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
        return api(config)
      }
      onAuthFail?.()
    }
    return Promise.reject(error)
  },
)
