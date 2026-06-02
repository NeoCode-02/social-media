export interface UserPublic {
  id: string
  username: string
  display_name: string
  avatar_url: string | null
}

export type FollowState = 'none' | 'pending' | 'accepted'

export interface UserProfile extends UserPublic {
  bio: string | null
  location: string | null
  website: string | null
  created_at: string
  last_seen: string | null
  is_private: boolean
  followers_count: number
  following_count: number
  posts_count: number
  is_following: boolean
  follow_state: FollowState
  can_view_posts: boolean
  is_blocked: boolean
  is_muted: boolean
}

export interface UserMe extends UserProfile {
  email: string
  email_verified: boolean
  is_admin: boolean
  pending_requests: number
}

export interface AdminStats {
  total_users: number
  total_posts: number
  new_users_today: number
  new_posts_today: number
  banned_users: number
  private_accounts: number
  admins: number
  open_reports: number
}

export interface AdminUser {
  id: string
  username: string
  display_name: string
  email: string
  avatar_url: string | null
  email_verified: boolean
  is_admin: boolean
  is_banned: boolean
  is_private: boolean
  created_at: string
}

export interface AdminUserPage {
  users: AdminUser[]
  next_cursor: string | null
}

export type ReportTarget = 'post' | 'user'

export interface Report {
  id: string
  target_type: ReportTarget
  reason: string
  status: 'open' | 'resolved' | 'dismissed'
  created_at: string
  reporter: UserPublic
  post: Post | null
  target_user: UserPublic | null
}

export interface ReportPage {
  reports: Report[]
  next_cursor: string | null
}

export interface Attachment {
  id: string
  url: string
  thumbnail_url: string
  mime: string
  name: string
  size: number
  width: number | null
  height: number | null
  duration_ms: number | null
  as_file: boolean
  is_voice: boolean
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
  attachments: Attachment[]
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

export interface Post {
  id: string
  author: UserPublic
  text: string | null
  parent_id: string | null
  created_at: string
  edited_at: string | null
  deleted_at: string | null
  attachments: Attachment[]
  reply_count: number
  repost_count: number
  like_count: number
  view_count: number
  liked_by_me: boolean
  reposted_by_me: boolean
  repost_of: Post | null
  reply_to: Post | null
}

export interface PostPage {
  posts: Post[]
  next_cursor: string | null
}

export type NotificationType =
  | 'like'
  | 'reply'
  | 'follow'
  | 'follow_request'
  | 'follow_accept'
  | 'mention'

export interface Notification {
  id: string
  type: NotificationType
  actor: UserPublic
  post_id: string | null
  post_preview: string | null
  read: boolean
  created_at: string
}

export interface NotificationPage {
  notifications: Notification[]
  next_cursor: string | null
  unread_count: number
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
  | { type: 'post.new'; post: Post }
  | { type: 'notification.new'; notification: Notification }
