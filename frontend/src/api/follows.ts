import { api } from './client'
import type { UserPublic } from './types'

export const followUser = (id: string) => api.post(`/users/${id}/follow`)
export const unfollowUser = (id: string) => api.delete(`/users/${id}/follow`)

export const listFollowers = (id: string) => api.get<UserPublic[]>(`/users/${id}/followers`)
export const listFollowing = (id: string) => api.get<UserPublic[]>(`/users/${id}/following`)
