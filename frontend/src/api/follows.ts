import { api } from './client'
import type { FollowState, UserPublic } from './types'

export const followUser = (id: string) =>
  api.post<{ status: Exclude<FollowState, 'none'> }>(`/users/${id}/follow`)
export const unfollowUser = (id: string) => api.delete(`/users/${id}/follow`)

export const listFollowers = (id: string) => api.get<UserPublic[]>(`/users/${id}/followers`)
export const listFollowing = (id: string) => api.get<UserPublic[]>(`/users/${id}/following`)

// Follow requests awaiting the current user's approval (private account).
export const listFollowRequests = () => api.get<UserPublic[]>('/users/me/follow-requests')
export const acceptFollowRequest = (followerId: string) =>
  api.post(`/users/me/follow-requests/${followerId}/accept`)
export const rejectFollowRequest = (followerId: string) =>
  api.post(`/users/me/follow-requests/${followerId}/reject`)
