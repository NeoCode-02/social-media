import { NavLink } from 'react-router-dom'

import type { Chat } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { chatFace, cn, formatTime } from '@/lib/utils'

export function ChatListItem({ chat, meId }: { chat: Chat; meId?: string }) {
  const face = chatFace(chat, meId)
  const last = chat.last_message
  const preview = last?.deleted_at
    ? 'Message deleted'
    : last
      ? `${last.sender_id === meId ? 'You: ' : ''}${last.content ?? ''}`
      : 'No messages yet'

  return (
    <NavLink
      to={`/c/${chat.id}`}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-2xl px-3 py-2.5 transition-colors',
          isActive ? 'bg-card' : 'hover:bg-cardhover',
        )
      }
    >
      <Avatar
        name={face.name}
        src={face.url}
        userId={face.userId}
        showPresence={chat.type === 'dm'}
        size={44}
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate text-sm font-semibold text-text">{face.name}</span>
          {last && <span className="shrink-0 text-[11px] text-faint">{formatTime(last.created_at)}</span>}
        </div>
        <div className="flex items-center justify-between gap-2">
          <span className={cn('truncate text-xs', last?.deleted_at ? 'italic text-faint' : 'text-muted')}>
            {preview}
          </span>
          {chat.unread_count > 0 && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-accent px-1.5 text-[11px] font-bold text-accentink">
              {chat.unread_count}
            </span>
          )}
        </div>
      </div>
    </NavLink>
  )
}
