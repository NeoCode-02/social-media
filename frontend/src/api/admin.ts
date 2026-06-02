import { api } from './client'
import type {
  AdminStats,
  AdminUser,
  AdminUserPage,
  PostPage,
  ReportPage,
  ReportTarget,
} from './types'

export const adminStats = () => api.get<AdminStats>('/admin/stats')

export const adminListUsers = (q: string, offset = 0) =>
  api.get<AdminUserPage>('/admin/users', { params: { q: q || undefined, offset, limit: 25 } })

export const adminBan = (id: string) => api.post<AdminUser>(`/admin/users/${id}/ban`)
export const adminUnban = (id: string) => api.post<AdminUser>(`/admin/users/${id}/unban`)
export const adminPromote = (id: string) => api.post<AdminUser>(`/admin/users/${id}/promote`)
export const adminDemote = (id: string) => api.post<AdminUser>(`/admin/users/${id}/demote`)
export const adminVerify = (id: string) => api.post<AdminUser>(`/admin/users/${id}/verify`)
export const adminDeleteUser = (id: string) => api.delete(`/admin/users/${id}`)

export const adminListPosts = (q: string, before?: string) =>
  api.get<PostPage>('/admin/posts', { params: { q: q || undefined, before, limit: 25 } })
export const adminDeletePost = (id: string) => api.delete(`/admin/posts/${id}`)

export const adminListReports = (status: 'open' | 'resolved' | 'dismissed', before?: string) =>
  api.get<ReportPage>('/admin/reports', { params: { status, before, limit: 25 } })
export const adminResolveReport = (id: string) => api.post(`/admin/reports/${id}/resolve`)
export const adminDismissReport = (id: string) => api.post(`/admin/reports/${id}/dismiss`)

export const createReport = (targetType: ReportTarget, targetId: string, reason: string) =>
  api.post('/reports', { target_type: targetType, target_id: targetId, reason })
