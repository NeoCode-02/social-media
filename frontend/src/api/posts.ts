import { api } from './client'
import type { Attachment, Post, PostPage } from './types'
import type { UploadOpts } from './chats'

export interface PostCreate {
  text?: string | null
  attachment_ids?: string[]
  parent_id?: string
  repost_of_id?: string
}

export const listTimeline = (before?: string) =>
  api.get<PostPage>('/posts', { params: { before, limit: 20 } })

export const globalFeed = (before?: string) =>
  api.get<PostPage>('/posts/global', { params: { before, limit: 20 } })

export const getPost = (id: string) => api.get<Post>(`/posts/${id}`)

export const createPost = (body: PostCreate) => api.post<Post>('/posts', body)

export const deletePost = (id: string) => api.delete<Post>(`/posts/${id}`)

export const listReplies = (id: string, after?: string) =>
  api.get<PostPage>(`/posts/${id}/replies`, { params: { after, limit: 30 } })

export const likePost = (id: string) => api.post(`/posts/${id}/like`)
export const unlikePost = (id: string) => api.delete(`/posts/${id}/like`)
export const repostPost = (id: string) => api.post(`/posts/${id}/repost`)
export const unrepostPost = (id: string) => api.delete(`/posts/${id}/repost`)

export const userFeed = (userId: string, before?: string) =>
  api.get<PostPage>(`/users/${userId}/posts`, { params: { before, limit: 20 } })

export const uploadPostAttachment = (file: File, opts: UploadOpts = {}) => {
  const form = new FormData()
  form.append('file', file)
  if (opts.asFile) form.append('as_file', 'true')
  if (opts.isVoice) form.append('is_voice', 'true')
  if (opts.durationMs != null) form.append('duration_ms', String(Math.round(opts.durationMs)))
  return api.post<Attachment>('/posts/attachments', form)
}

export const postAttachmentDownloadUrl = (attachmentId: string) =>
  api.get<{ url: string }>(`/posts/attachments/${attachmentId}/download-url`)
