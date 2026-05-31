import { useQueryClient } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import { FileText, ImageIcon, Mic, Paperclip, Reply, SendHorizontal, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { sendMessage, uploadAttachment, type UploadOpts } from '@/api/chats'
import type { Attachment, Message } from '@/api/types'
import { formatBytes, isImage, isVideo } from '@/lib/utils'
import { wsClient } from '@/realtime/ws'
import { VoiceRecorder } from './VoiceRecorder'

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
  const [menuOpen, setMenuOpen] = useState(false)
  const [recording, setRecording] = useState(false)
  const mediaRef = useRef<HTMLInputElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const typingRef = useRef(false)
  const stopTimer = useRef<number | undefined>(undefined)

  function appendMessage(data: Message) {
    qc.setQueryData<Message[]>(['messages', chatId], (old) => {
      if (!old) return [data]
      if (old.some((m) => m.id === data.id)) return old
      return [...old, data]
    })
    qc.invalidateQueries({ queryKey: ['chats'] })
  }

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

  async function onPickFile(e: React.ChangeEvent<HTMLInputElement>, opts: UploadOpts = {}) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setUploading(true)
    try {
      const { data } = await uploadAttachment(chatId, file, opts)
      setPending(data)
    } finally {
      setUploading(false)
    }
  }

  async function onVoiceSend(file: File, durationMs: number) {
    setRecording(false)
    setSending(true)
    try {
      const { data: att } = await uploadAttachment(chatId, file, { isVoice: true, durationMs })
      const { data } = await sendMessage(chatId, undefined, [att.id])
      appendMessage(data)
    } finally {
      setSending(false)
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
      appendMessage(data)
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
          ) : pending && isImage(pending.mime) && !pending.as_file ? (
            <img
              src={pending.thumbnail_url}
              alt={pending.name}
              className="h-10 w-10 rounded-lg object-cover"
            />
          ) : pending && isVideo(pending.mime) && !pending.as_file ? (
            <video src={pending.url} className="h-10 w-10 rounded-lg object-cover" />
          ) : (
            <FileText size={18} className="text-muted" />
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

      <input
        ref={mediaRef}
        type="file"
        accept="image/*,video/*"
        className="hidden"
        onChange={(e) => onPickFile(e)}
      />
      <input ref={fileRef} type="file" className="hidden" onChange={(e) => onPickFile(e, { asFile: true })} />

      {recording ? (
        <VoiceRecorder onSend={onVoiceSend} onCancel={() => setRecording(false)} />
      ) : (
        <form onSubmit={onSubmit} className="flex items-center gap-2">
          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => setMenuOpen((v) => !v)}
              title="Attach"
              className="flex h-10 w-10 items-center justify-center rounded-full text-faint transition hover:bg-cardhover hover:text-muted"
            >
              <Paperclip size={18} />
            </button>
            <AnimatePresence>
              {menuOpen && (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} />
                  <motion.div
                    initial={{ opacity: 0, y: 6, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 6, scale: 0.96 }}
                    transition={{ duration: 0.16, ease: [0.22, 1, 0.36, 1] }}
                    className="absolute bottom-12 left-0 z-20 w-44 overflow-hidden rounded-2xl border border-border bg-elev p-1.5 shadow-soft"
                  >
                    <button
                      type="button"
                      onClick={() => {
                        setMenuOpen(false)
                        mediaRef.current?.click()
                      }}
                      className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm transition hover:bg-cardhover"
                    >
                      <ImageIcon size={16} className="text-accent" /> Photo or video
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setMenuOpen(false)
                        fileRef.current?.click()
                      }}
                      className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm transition hover:bg-cardhover"
                    >
                      <FileText size={16} className="text-violet" /> File
                    </button>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>

          <input
            value={text}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Write a message…"
            className="min-w-0 flex-1 rounded-full border border-border bg-card px-4 py-3 text-sm outline-none placeholder:text-faint focus:border-violet/50"
          />

          {text.trim() || pending ? (
            <button
              type="submit"
              disabled={sending}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-accentink transition hover:brightness-105 active:scale-95 disabled:opacity-40"
            >
              <SendHorizontal size={18} />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setRecording(true)}
              title="Record voice message"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-accentink transition hover:brightness-105 active:scale-95"
            >
              <Mic size={18} />
            </button>
          )}
        </form>
      )}
    </div>
  )
}
