import { api } from './client'
import type { UserPublic } from './types'

export const blockUser = (id: string) => api.post(`/users/${id}/block`)
export const unblockUser = (id: string) => api.delete(`/users/${id}/block`)
export const muteUser = (id: string) => api.post(`/users/${id}/mute`)
export const unmuteUser = (id: string) => api.delete(`/users/${id}/mute`)

export const listBlocked = () => api.get<UserPublic[]>('/users/me/blocks')
export const listMuted = () => api.get<UserPublic[]>('/users/me/mutes')
