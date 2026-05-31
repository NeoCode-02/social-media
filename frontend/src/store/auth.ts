import { create } from 'zustand'

import { setAccessToken } from '@/api/client'
import type { UserMe } from '@/api/types'

type Status = 'loading' | 'authed' | 'guest'

interface AuthState {
  user: UserMe | null
  status: Status
  setSession: (token: string, user: UserMe) => void
  setUser: (user: UserMe) => void
  setStatus: (status: Status) => void
  clear: () => void
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  status: 'loading',
  setSession: (token, user) => {
    setAccessToken(token)
    set({ user, status: 'authed' })
  },
  setUser: (user) => set({ user }),
  setStatus: (status) => set({ status }),
  clear: () => {
    setAccessToken(null)
    set({ user: null, status: 'guest' })
  },
}))
