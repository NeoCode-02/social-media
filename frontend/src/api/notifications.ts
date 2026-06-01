import { api } from './client'
import type { NotificationPage } from './types'

export const listNotifications = (before?: string) =>
  api.get<NotificationPage>('/notifications', { params: { before, limit: 30 } })

export const unreadCount = () => api.get<{ count: number }>('/notifications/unread-count')

export const markNotificationsRead = (ids?: string[]) =>
  api.post('/notifications/read', { ids: ids ?? null })
