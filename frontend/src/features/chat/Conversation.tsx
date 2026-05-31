import { useQuery } from '@tanstack/react-query'
import { AnimatePresence } from 'framer-motion'
import { useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'

import { getChat, markRead } from '@/api/chats'
import type { Message } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { FullScreenLoader } from '@/components/FullScreenLoader'
import { chatFace, formatDayLabel } from '@/lib/utils'
import { useAuth } from '@/store/auth'
import { useRealtimeStore } from '@/store/realtime'
import { MessageBubble } from './MessageBubble'
import { MessageInput } from './MessageInput'
import { TypingIndicator } from './TypingIndicator'
import { useMessages } from './useMessages'

type Row =
  | { kind: 'day'; key: string; label: string }
  | { kind: 'msg'; key: string; message: Message; mine: boolean; showSender: boolean }

export function Conversation() {
  const { chatId = '' } = useParams()
  const me = useAuth((s) => s.user)
  const { data: chat } = useQuery({
    queryKey: ['chat', chatId],
    queryFn: async () => (await getChat(chatId)).data,
    enabled: Boolean(chatId),
  })
  const { messages, isLoading, loadOlder, loadingOlder, hasMore } = useMessages(chatId)

  const face = chat ? chatFace(chat, me?.id) : null
  const online = useRealtimeStore((s) => (face?.userId ? s.online[face.userId] : false))
  const typingIds = useRealtimeStore((s) => s.typing[chatId] ?? [])
  const someoneTyping = typingIds.some((id) => id !== me?.id)

  const scrollRef = useRef<HTMLDivElement>(null)
  const lastIdRef = useRef<string | undefined>(undefined)

  useEffect(() => {
    const last = messages[messages.length - 1]
    if (!last || last.id === lastIdRef.current) return
    lastIdRef.current = last.id
    requestAnimationFrame(() => {
      const el = scrollRef.current
      if (el) el.scrollTop = el.scrollHeight
    })
  }, [messages])

  useEffect(() => {
    const last = messages[messages.length - 1]
    if (last && last.sender_id !== me?.id) markRead(chatId, last.id).catch(() => {})
  }, [messages, chatId, me?.id])

  if (!chat || !face) return <FullScreenLoader />

  const rows: Row[] = []
  let lastDay = ''
  let prevSender: string | undefined
  for (const m of messages) {
    const day = formatDayLabel(m.created_at)
    if (day !== lastDay) {
      rows.push({ kind: 'day', key: `day-${m.id}`, label: day })
      lastDay = day
      prevSender = undefined
    }
    const mine = m.sender_id === me?.id
    rows.push({ kind: 'msg', key: m.id, message: m, mine, showSender: !mine && prevSender !== m.sender_id })
    prevSender = m.sender_id
  }

  const subtitle = someoneTyping
    ? 'typing…'
    : chat.type === 'group'
      ? `${chat.members.length} members`
      : online
        ? 'Online'
        : 'Offline'

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-border px-5 py-3">
        <Avatar name={face.name} src={face.url} userId={face.userId} showPresence={chat.type === 'dm'} size={40} />
        <div className="min-w-0">
          <h2 className="truncate text-sm font-semibold">{face.name}</h2>
          <p className="text-xs text-muted">{subtitle}</p>
        </div>
      </header>

      <div ref={scrollRef} className="min-h-0 flex-1 space-y-1.5 overflow-y-auto px-5 py-4">
        {hasMore && messages.length > 0 && (
          <div className="flex justify-center pb-2">
            <button
              onClick={loadOlder}
              disabled={loadingOlder}
              className="rounded-full bg-card px-4 py-1.5 text-xs text-muted transition hover:bg-cardhover"
            >
              {loadingOlder ? 'Loading…' : 'Load earlier messages'}
            </button>
          </div>
        )}

        {isLoading ? (
          <FullScreenLoader />
        ) : messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-faint">
            No messages yet — say hello 👋
          </div>
        ) : (
          rows.map((row) =>
            row.kind === 'day' ? (
              <div key={row.key} className="flex justify-center py-3">
                <span className="rounded-full bg-card px-3 py-1 text-[11px] font-medium text-muted">
                  {row.label}
                </span>
              </div>
            ) : (
              <MessageBubble
                key={row.key}
                message={row.message}
                mine={row.mine}
                showSender={row.showSender}
              />
            ),
          )
        )}

        <AnimatePresence>
          {someoneTyping && <TypingIndicator label={chat.type === 'group' ? 'someone is typing' : undefined} />}
        </AnimatePresence>
      </div>

      <MessageInput chatId={chatId} />
    </div>
  )
}
