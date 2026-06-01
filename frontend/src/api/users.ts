import { api } from './client'
import type { UserMe, UserProfile, UserPublic } from './types'

export const searchUsers = (q: string) => api.get<UserPublic[]>('/users/search', { params: { q } })

export interface ProfileUpdate {
  display_name?: string
  bio?: string | null
  location?: string | null
  website?: string | null
  is_private?: boolean
}

export const updateMe = (body: ProfileUpdate) => api.patch<UserMe>('/users/me', body)

export const getUser = (id: string) => api.get<UserProfile>(`/users/${id}`)

export const getUserByUsername = (username: string) =>
  api.get<UserProfile>(`/users/by-username/${encodeURIComponent(username)}`)

export const uploadAvatar = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<UserMe>('/users/me/avatar', form)
}
