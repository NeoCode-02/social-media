export interface UserPublic {
  id: string
  username: string
  display_name: string
  avatar_url: string | null
}

export interface UserMe extends UserPublic {
  email: string
  email_verified: boolean
  created_at: string
}

export interface Message {
  id: string
  chat_id: string
  sender_id: string
  type: string
  content: string | null
  reply_to_id: string | null
  created_at: string
  edited_at: string | null
  deleted_at: string | null
  sender: UserPublic
}

export interface ChatMember {
  role: string
  last_read_message_id: string | null
  user: UserPublic
}

export type ChatType = 'dm' | 'group'

export interface Chat {
  id: string
  type: ChatType
  title: string | null
  avatar_url: string | null
  created_at: string
  members: ChatMember[]
  last_message: Message | null
  unread_count: number
}

export interface MessagePage {
  messages: Message[]
  next_cursor: string | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

// Realtime event shapes (server → client)
export type RealtimeEvent =
  | { type: 'message.new' | 'message.edited' | 'message.deleted'; chat_id: string; message: Message }
  | { type: 'typing'; chat_id: string; user_id: string; is_typing: boolean }
  | { type: 'message.read'; chat_id: string; user_id: string; last_read_message_id: string }
  | { type: 'presence'; user_id: string; status: 'online' | 'offline' }
