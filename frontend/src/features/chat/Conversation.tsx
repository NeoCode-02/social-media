import { useQuery, useQueryClient } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import { ArrowDown } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'

import { getChat, markRead } from '@/api/chats'
import type { Chat, Message } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { FullScreenLoader } from '@/components/FullScreenLoader'
import { ProfileView } from '@/features/profile/ProfileView'
import { chatFace, formatDayLabel } from '@/lib/utils'
import { useAuth } from '@/store/auth'
import { useRealtimeStore } from '@/store/realtime'
import { MessageBubble } from './MessageBubble'
import { MessageInput } from './MessageInput'
import { TypingIndicator } from './TypingIndicator'
import { useMessages } from './useMessages'

type Row =
  | { kind: 'day'; key: string; label: string }
  | {
      kind: 'msg'
      key: string
      message: Message
      mine: boolean
      showSender: boolean
      status?: 'sent' | 'read'
    }

export function Conversation() {
  const { chatId = '' } = useParams()
  const me = useAuth((s) => s.user)
  const qc = useQueryClient()
  const { data: chat } = useQuery({
    queryKey: ['chat', chatId],
    queryFn: async () => (await getChat(chatId)).data,
    enabled: Boolean(chatId),
  })
  const { messages, isLoading, loadOlder, loadingOlder, hasMore } = useMessages(chatId)

  const face = chat ? chatFace(chat, me?.id) : null
  const online = useRealtimeStore((s) => (face?.userId ? s.online[face.userId] : false))
  // Select the stored reference (stable); default outside the selector so we
  // never return a fresh [] each render (would loop useSyncExternalStore).
  const typingIds = useRealtimeStore((s) => s.typing[chatId])
  const someoneTyping = (typingIds ?? []).some((id) => id !== me?.id)

  const [replyingTo, setReplyingTo] = useState<Message | null>(null)
  const [profileUserId, setProfileUserId] = useState<string | null>(null)

  const scrollRef = useRef<HTMLDivElement>(null)
  const lastIdRef = useRef<string | undefined>(undefined)
  const nearBottomRef = useRef(true)
  const [showJump, setShowJump] = useState(false)

  function onScroll(e: React.UIEvent<HTMLDivElement>) {
    const el = e.currentTarget
    const distance = el.scrollHeight - el.scrollTop - el.clientHeight
    nearBottomRef.current = distance < 120
    setShowJump(distance >= 120)
  }

  function scrollToBottom() {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
    setShowJump(false)
  }

  useEffect(() => {
    const last = messages[messages.length - 1]
    if (!last || last.id === lastIdRef.current) return
    const wasInitial = lastIdRef.current === undefined
    lastIdRef.current = last.id
    // Jump to newest on load / own send / when already near the bottom — but
    // don't yank the viewport while the user is reading older history.
    if (wasInitial || nearBottomRef.current || last.sender_id === me?.id) {
      requestAnimationFrame(() => {
        const el = scrollRef.current
        if (el) el.scrollTop = el.scrollHeight
      })
    }
  }, [messages, me?.id])

  useEffect(() => {
    // Clear this chat's sidebar unread badge immediately.
    qc.setQueryData<Chat[]>(['chats'], (chats) =>
      chats?.map((c) => (c.id === chatId ? { ...c, unread_count: 0 } : c)),
    )
    const last = messages[messages.length - 1]
    if (last && last.sender_id !== me?.id) {
      markRead(chatId, last.id)
        .then(() => qc.invalidateQueries({ queryKey: ['chats'] }))
        .catch(() => {})
    }
  }, [messages, chatId, me?.id, qc])

  if (!chat || !face) return <FullScreenLoader />

  // How far the *other* participants have read (all must have read for a tick).
  const otherReads = chat.members
    .filter((m) => m.user.id !== me?.id)
    .map((m) => m.last_read_message_id)
  const readUpTo =
    otherReads.length > 0 && otherReads.every(Boolean)
      ? (otherReads as string[]).reduce((a, b) => (a < b ? a : b))
      : undefined

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
    rows.push({
      kind: 'msg',
      key: m.id,
      message: m,
      mine,
      showSender: !mine && prevSender !== m.sender_id,
      status: mine ? (readUpTo && m.id <= readUpTo ? 'read' : 'sent') : undefined,
    })
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
    <div className="relative flex h-full flex-col">
      <header className="flex items-center gap-3 border-b border-border px-5 py-3">
        <button
          onClick={() => face.userId && setProfileUserId(face.userId)}
          disabled={!face.userId}
          className="flex min-w-0 items-center gap-3 rounded-2xl text-left transition enabled:hover:opacity-80 disabled:cursor-default"
        >
          <Avatar name={face.name} src={face.url} userId={face.userId} showPresence={chat.type === 'dm'} size={40} />
          <div className="min-w-0">
            <h2 className="truncate text-sm font-semibold">{face.name}</h2>
            <p className="text-xs text-muted">{subtitle}</p>
          </div>
        </button>
      </header>

      <div
        ref={scrollRef}
        onScroll={onScroll}
        className="min-h-0 flex-1 space-y-1.5 overflow-y-auto px-5 py-4"
      >
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
                status={row.status}
                chatId={chatId}
                onReply={setReplyingTo}
                onOpenProfile={setProfileUserId}
                replyToMessage={
                  row.message.reply_to_id
                    ? messages.find((m) => m.id === row.message.reply_to_id)
                    : null
                }
              />
            ),
          )
        )}

        <AnimatePresence>
          {someoneTyping && <TypingIndicator label={chat.type === 'group' ? 'someone is typing' : undefined} />}
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {showJump && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={scrollToBottom}
            className="absolute bottom-20 right-6 z-10 flex h-10 w-10 items-center justify-center rounded-full border border-border bg-card shadow-soft transition hover:bg-cardhover"
            title="Jump to latest"
          >
            <ArrowDown size={18} />
          </motion.button>
        )}
      </AnimatePresence>

      <MessageInput
        chatId={chatId}
        replyTo={replyingTo}
        onCancelReply={() => setReplyingTo(null)}
      />

      <AnimatePresence>
        {profileUserId && (
          <ProfileView userId={profileUserId} onClose={() => setProfileUserId(null)} />
        )}
      </AnimatePresence>
    </div>
  )
}
