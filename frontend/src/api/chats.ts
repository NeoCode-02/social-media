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

export const uploadAttachment = (chatId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<Attachment>(`/chats/${chatId}/attachments`, form)
}

export const markRead = (chatId: string, lastReadMessageId: string) =>
  api.post(`/chats/${chatId}/read`, { last_read_message_id: lastReadMessageId })

export const editMessage = (id: string, content: string) =>
  api.patch<Message>(`/messages/${id}`, { content })

export const deleteMessage = (id: string) => api.delete<Message>(`/messages/${id}`)

export const searchUsers = (q: string) =>
  api.get<UserPublic[]>('/users/search', { params: { q } })
