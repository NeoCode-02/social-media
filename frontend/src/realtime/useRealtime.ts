import { useEffect, useRef } from 'react'

import { useQueryClient } from '@tanstack/react-query'

import { getWsTicket } from '@/api/auth'
import type { Chat, Message } from '@/api/types'
import { prependToTimeline } from '@/features/feed/postCache'
import { useRealtimeStore } from '@/store/realtime'
import { wsClient } from './ws'

function upsert(old: Message[] | undefined, msg: Message): Message[] | undefined {
  if (!old) return old // chat not open → list invalidation handles preview/unread
  const idx = old.findIndex((m) => m.id === msg.id)
  if (idx >= 0) {
    const next = [...old]
    next[idx] = msg
    return next
  }
  return [...old, msg] // UUIDv7 ids are monotonic → stays chronological
}

/** Connects the socket and fans events into the query cache + realtime store. */
export function useRealtime(): void {
  const qc = useQueryClient()
  const setPresence = useRealtimeStore((s) => s.setPresence)
  const setTyping = useRealtimeStore((s) => s.setTyping)
  const timers = useRef<Record<string, number>>({})

  useEffect(() => {
    const activeTimers = timers.current
    wsClient.connect(getWsTicket)

    const off = wsClient.on((ev) => {
      switch (ev.type) {
        case 'message.new':
        case 'message.edited':
        case 'message.deleted':
          qc.setQueryData<Message[]>(['messages', ev.chat_id], (old) => upsert(old, ev.message))
          qc.invalidateQueries({ queryKey: ['chats'] })
          break
        case 'presence':
          setPresence(ev.user_id, ev.status === 'online')
          break
        case 'post.new':
          prependToTimeline(qc, ev.post)
          break
        case 'notification.new':
          qc.invalidateQueries({ queryKey: ['notifications'] })
          break
        case 'typing': {
          setTyping(ev.chat_id, ev.user_id, ev.is_typing)
          const key = `${ev.chat_id}:${ev.user_id}`
          if (timers.current[key]) clearTimeout(timers.current[key])
          if (ev.is_typing) {
            timers.current[key] = window.setTimeout(
              () => setTyping(ev.chat_id, ev.user_id, false),
              4000,
            )
          }
          break
        }
        case 'message.read':
          qc.setQueryData<Chat>(['chat', ev.chat_id], (c) =>
            c
              ? {
                  ...c,
                  members: c.members.map((m) =>
                    m.user.id === ev.user_id
                      ? { ...m, last_read_message_id: ev.last_read_message_id }
                      : m,
                  ),
                }
              : c,
          )
          break
      }
    })
    return () => {
      off()
      Object.values(activeTimers).forEach((t) => clearTimeout(t))
    }
  }, [qc, setPresence, setTyping])
}
