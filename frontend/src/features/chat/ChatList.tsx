import { MessageSquareDashed } from 'lucide-react'

import { useAuth } from '@/store/auth'
import { ChatListItem } from './ChatListItem'
import { useChats } from './useChats'

export function ChatList() {
  const { data: chats, isLoading } = useChats()
  const meId = useAuth((s) => s.user?.id)

  if (isLoading) {
    return (
      <div className="space-y-2 px-3 py-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 rounded-2xl px-3 py-2.5">
            <div className="h-11 w-11 shrink-0 animate-pulse rounded-full bg-card" />
            <div className="flex-1 space-y-2">
              <div className="h-3 w-1/2 animate-pulse rounded bg-card" />
              <div className="h-2.5 w-3/4 animate-pulse rounded bg-card" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (!chats || chats.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 px-6 py-12 text-center text-muted">
        <MessageSquareDashed size={28} className="text-faint" />
        <p className="text-sm">No conversations yet</p>
        <p className="text-xs text-faint">Start a new chat to say hello.</p>
      </div>
    )
  }

  return (
    <div className="space-y-1 px-2 py-2">
      {chats.map((chat) => (
        <ChatListItem key={chat.id} chat={chat} meId={meId} />
      ))}
    </div>
  )
}
