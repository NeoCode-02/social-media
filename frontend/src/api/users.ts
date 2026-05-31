import { api } from './client'
import type { UserMe } from './types'

export const updateMe = (body: { display_name?: string }) =>
  api.patch<UserMe>('/users/me', body)

export const uploadAvatar = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<UserMe>('/users/me/avatar', form)
}
