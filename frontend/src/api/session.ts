import axios from 'axios'

import { getMe } from './auth'
import { setAccessToken } from './client'
import { useAuth } from '@/store/auth'

/** Exchange an access token for the user profile and mark the session authed. */
export async function establishSession(token: string): Promise<void> {
  setAccessToken(token)
  const me = await getMe()
  useAuth.getState().setSession(token, me.data)
}

/** On app load: use the refresh cookie to silently restore a session. */
export async function bootstrapSession(): Promise<boolean> {
  try {
    const { data } = await axios.post<{ access_token: string }>(
      '/api/auth/refresh',
      {},
      { withCredentials: true },
    )
    await establishSession(data.access_token)
    return true
  } catch {
    useAuth.getState().clear()
    return false
  }
}
