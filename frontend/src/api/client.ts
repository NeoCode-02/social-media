import axios from 'axios'

// Relative baseURL → dev proxy (vite) / same-origin (prod) forwards to backend.
export const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // send refresh-token cookie
})

// Access token kept in memory; set after login (M1).
let accessToken: string | null = null

export function setAccessToken(token: string | null): void {
  accessToken = token
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})
