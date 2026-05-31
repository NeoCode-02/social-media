import { useQueryClient } from '@tanstack/react-query'
import { Paperclip, SendHorizontal } from 'lucide-react'
import { useRef, useState } from 'react'

import { sendMessage } from '@/api/chats'
import type { Message } from '@/api/types'
import { wsClient } from '@/realtime/ws'

export function MessageInput({ chatId }: { chatId: string }) {
  const qc = useQueryClient()
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const typingRef = useRef(false)
  const stopTimer = useRef<number | undefined>(undefined)

  function signalStop() {
    if (typingRef.current) {
      typingRef.current = false
      wsClient.send({ type: 'typing.stop', chat_id: chatId })
    }
    clearTimeout(stopTimer.current)
  }

  function onChange(value: string) {
    setText(value)
    if (!typingRef.current) {
      typingRef.current = true
      wsClient.send({ type: 'typing.start', chat_id: chatId })
    }
    clearTimeout(stopTimer.current)
    stopTimer.current = window.setTimeout(signalStop, 1800)
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const content = text.trim()
    if (!content || sending) return
    setSending(true)
    signalStop()
    try {
      const { data } = await sendMessage(chatId, content)
      qc.setQueryData<Message[]>(['messages', chatId], (old) => {
        if (!old) return [data]
        if (old.some((m) => m.id === data.id)) return old
        return [...old, data]
      })
      qc.invalidateQueries({ queryKey: ['chats'] })
      setText('')
    } finally {
      setSending(false)
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex items-center gap-2 border-t border-border px-4 py-3">
      <button
        type="button"
        title="Attach (coming soon)"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-faint transition hover:bg-cardhover hover:text-muted"
      >
        <Paperclip size={18} />
      </button>
      <input
        value={text}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Write a message…"
        className="min-w-0 flex-1 rounded-full border border-border bg-card px-4 py-3 text-sm outline-none placeholder:text-faint focus:border-violet/50"
      />
      <button
        type="submit"
        disabled={!text.trim() || sending}
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-accentink transition hover:brightness-105 active:scale-95 disabled:opacity-40"
      >
        <SendHorizontal size={18} />
      </button>
    </form>
  )
}
