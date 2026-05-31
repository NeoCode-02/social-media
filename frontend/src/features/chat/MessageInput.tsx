import { useQueryClient } from '@tanstack/react-query'
import { Paperclip, Reply, SendHorizontal, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { sendMessage, uploadAttachment } from '@/api/chats'
import type { Attachment, Message } from '@/api/types'
import { formatBytes, isImage } from '@/lib/utils'
import { wsClient } from '@/realtime/ws'

interface Props {
  chatId: string
  replyTo?: Message | null
  onCancelReply?: () => void
}

export function MessageInput({ chatId, replyTo, onCancelReply }: Props) {
  const qc = useQueryClient()
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)
  const [pending, setPending] = useState<Attachment | null>(null)
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
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

  async function onPickFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setUploading(true)
    try {
      const { data } = await uploadAttachment(chatId, file)
      setPending(data)
    } finally {
      setUploading(false)
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const content = text.trim()
    if ((!content && !pending) || sending) return
    setSending(true)
    signalStop()
    try {
      const { data } = await sendMessage(
        chatId,
        content,
        pending ? [pending.id] : undefined,
        replyTo?.id,
      )
      onCancelReply?.()
      qc.setQueryData<Message[]>(['messages', chatId], (old) => {
        if (!old) return [data]
        if (old.some((m) => m.id === data.id)) return old
        return [...old, data]
      })
      qc.invalidateQueries({ queryKey: ['chats'] })
      setText('')
      setPending(null)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="border-t border-border px-4 py-3">
      {replyTo && (
        <div className="mb-2 flex items-center gap-3 rounded-2xl bg-accent/5 px-3 py-2 text-xs">
          <Reply size={14} className="text-accent" />
          <div className="min-w-0 flex-1">
            <p className="font-semibold text-accent">Replying to {replyTo.sender.display_name}</p>
            <p className="truncate text-faint">
              {replyTo.content || (replyTo.attachments.length ? 'Media' : '')}
            </p>
          </div>
          <button onClick={onCancelReply} className="text-faint hover:text-text">
            <X size={16} />
          </button>
        </div>
      )}

      {(pending || uploading) && (
        <div className="mb-2 flex items-center gap-3 rounded-2xl bg-card px-3 py-2">
          {uploading ? (
            <span className="h-9 w-9 animate-spin rounded-full border-2 border-border border-t-accent" />
          ) : pending && isImage(pending.mime) ? (
            <img
              src={pending.thumbnail_url}
              alt={pending.name}
              className="h-10 w-10 rounded-lg object-cover"
            />
          ) : (
            <Paperclip size={18} className="text-muted" />
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium">
              {uploading ? 'Uploading…' : pending?.name}
            </p>
            {pending && <p className="text-[11px] text-faint">{formatBytes(pending.size)}</p>}
          </div>
          {pending && (
            <button onClick={() => setPending(null)} className="text-faint hover:text-text">
              <X size={16} />
            </button>
          )}
        </div>
      )}

      <form onSubmit={onSubmit} className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          title="Attach a file"
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-faint transition hover:bg-cardhover hover:text-muted"
        >
          <Paperclip size={18} />
        </button>
        <input ref={fileRef} type="file" className="hidden" onChange={onPickFile} />
        <input
          value={text}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Write a message…"
          className="min-w-0 flex-1 rounded-full border border-border bg-card px-4 py-3 text-sm outline-none placeholder:text-faint focus:border-violet/50"
        />
        <button
          type="submit"
          disabled={(!text.trim() && !pending) || sending}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-accentink transition hover:brightness-105 active:scale-95 disabled:opacity-40"
        >
          <SendHorizontal size={18} />
        </button>
      </form>
    </div>
  )
}
