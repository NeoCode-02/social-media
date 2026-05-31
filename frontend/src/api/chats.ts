import { api } from './client'
import type { Attachment, Chat, Message, MessagePage, UserPublic } from './types'

export const listChats = () => api.get<Chat[]>('/chats')

export const getChat = (id: string) => api.get<Chat>(`/chats/${id}`)

export const createDm = (userId: string) =>
  api.post<Chat>('/chats', { type: 'dm', user_id: userId })

export const createGroup = (title: string, memberIds: string[]) =>
  api.post<Chat>('/chats', { type: 'group', title, member_ids: memberIds })

export const listMessages = (chatId: string, before?: string) =>
  api.get<MessagePage>(`/chats/${chatId}/messages`, { params: { before, limit: 30 } })

export const sendMessage = (
  chatId: string,
  content?: string,
  attachmentIds?: string[],
  replyToId?: string,
) =>
  api.post<Message>(`/chats/${chatId}/messages`, {
    content: content || null,
    attachment_ids: attachmentIds,
    reply_to_id: replyToId,
  })

export interface UploadOpts {
  asFile?: boolean
  isVoice?: boolean
  durationMs?: number
}

export const uploadAttachment = (chatId: string, file: File, opts: UploadOpts = {}) => {
  const form = new FormData()
  form.append('file', file)
  if (opts.asFile) form.append('as_file', 'true')
  if (opts.isVoice) form.append('is_voice', 'true')
  if (opts.durationMs != null) form.append('duration_ms', String(Math.round(opts.durationMs)))
  return api.post<Attachment>(`/chats/${chatId}/attachments`, form)
}

export const getAttachmentDownloadUrl = (chatId: string, attachmentId: string) =>
  api.get<{ url: string }>(`/chats/${chatId}/attachments/${attachmentId}/download-url`)

export const markRead = (chatId: string, lastReadMessageId: string) =>
  api.post(`/chats/${chatId}/read`, { last_read_message_id: lastReadMessageId })

export const editMessage = (id: string, content: string) =>
  api.patch<Message>(`/messages/${id}`, { content })

export const deleteMessage = (id: string) => api.delete<Message>(`/messages/${id}`)

export const searchUsers = (q: string) =>
  api.get<UserPublic[]>('/users/search', { params: { q } })
