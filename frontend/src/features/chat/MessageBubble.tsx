import { useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Check, CheckCheck, Pencil, Reply, Trash2, X } from 'lucide-react'
import { useState } from 'react'

import { deleteMessage, editMessage } from '@/api/chats'
import type { Message } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { cn, formatTime } from '@/lib/utils'
import { MessageAttachments } from './MessageAttachments'

interface Props {
  message: Message
  mine: boolean
  showSender: boolean
  status?: 'sent' | 'read'
  chatId: string
  onReply?: (m: Message) => void
  onOpenProfile?: (userId: string) => void
  replyToMessage?: Message | null
}

export function MessageBubble({
  message,
  mine,
  showSender,
  status,
  chatId,
  onReply,
  onOpenProfile,
  replyToMessage,
}: Props) {
  const qc = useQueryClient()
  const deleted = Boolean(message.deleted_at)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(message.content ?? '')
  const [busy, setBusy] = useState(false)

  const replace = (m: Message) =>
    qc.setQueryData<Message[]>(['messages', chatId], (old) =>
      old?.map((x) => (x.id === m.id ? m : x)),
    )

  async function saveEdit() {
    const next = draft.trim()
    if (!next || next === message.content) {
      setEditing(false)
      return
    }
    setBusy(true)
    try {
      const { data } = await editMessage(message.id, next)
      replace(data)
      setEditing(false)
    } finally {
      setBusy(false)
    }
  }

  async function onDelete() {
    setBusy(true)
    try {
      const { data } = await deleteMessage(message.id)
      replace(data)
    } finally {
      setBusy(false)
    }
  }

  const canEditText = mine && !deleted && Boolean(message.content)

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
      className={cn('group flex gap-2', mine ? 'justify-end' : 'justify-start')}
    >
      {!mine && (
        <div className="w-8 shrink-0 self-end">
          {showSender && (
            <button onClick={() => onOpenProfile?.(message.sender.id)} title={message.sender.display_name}>
              <Avatar name={message.sender.display_name} src={message.sender.avatar_url} size={32} />
            </button>
          )}
        </div>
      )}

      <div className={cn('flex max-w-[68%] items-end gap-1', mine ? 'flex-row' : 'flex-row-reverse')}>
        {!deleted && !editing && (
          <div className="flex shrink-0 items-center gap-0.5 opacity-0 transition group-hover:opacity-100">
            {mine && canEditText && (
              <button
                onClick={() => {
                  setDraft(message.content ?? '')
                  setEditing(true)
                }}
                className="flex h-7 w-7 items-center justify-center rounded-full text-faint hover:bg-cardhover hover:text-text"
                title="Edit"
              >
                <Pencil size={13} />
              </button>
            )}
            <button
              onClick={() => onReply?.(message)}
              className="flex h-7 w-7 items-center justify-center rounded-full text-faint hover:bg-cardhover hover:text-text"
              title="Reply"
            >
              <Reply size={13} />
            </button>
            {mine && (
              <button
                onClick={onDelete}
                disabled={busy}
                className="flex h-7 w-7 items-center justify-center rounded-full text-faint hover:bg-cardhover hover:text-danger"
                title="Delete"
              >
                <Trash2 size={13} />
              </button>
            )}
          </div>
        )}

        <div className="min-w-0">
          {!mine && showSender && (
            <button
              onClick={() => onOpenProfile?.(message.sender.id)}
              className="mb-1 ml-1 block text-xs font-medium text-muted transition hover:text-text"
            >
              {message.sender.display_name}
            </button>
          )}
          <div
            className={cn(
              'rounded-2xl px-3.5 py-2 text-sm leading-relaxed shadow-soft',
              mine ? 'rounded-br-md bg-accent text-accentink' : 'rounded-bl-md bg-card text-text',
            )}
          >
            {replyToMessage && (
              <div
                className={cn(
                  'mb-2 border-l-2 py-1 pl-2 text-[11px]',
                  mine ? 'border-accentink/30 bg-black/5' : 'border-accent/40 bg-accent/5',
                )}
              >
                <p className="font-semibold opacity-70">{replyToMessage.sender.display_name}</p>
                <p className="truncate opacity-60">
                  {replyToMessage.content || (replyToMessage.attachments.length ? 'Media' : '')}
                </p>
              </div>
            )}
            {editing ? (
              <div className="flex items-center gap-2">
                <input
                  autoFocus
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') saveEdit()
                    if (e.key === 'Escape') setEditing(false)
                  }}
                  className="w-56 rounded-lg bg-black/10 px-2 py-1 text-sm outline-none"
                />
                <button onClick={saveEdit} disabled={busy} title="Save">
                  <Check size={16} />
                </button>
                <button onClick={() => setEditing(false)} title="Cancel">
                  <X size={16} />
                </button>
              </div>
            ) : deleted ? (
              <span className={cn('italic', mine ? 'text-accentink/70' : 'text-faint')}>
                This message was deleted
              </span>
            ) : (
              <>
                {message.attachments.length > 0 && (
                  <div className="mb-1">
                    <MessageAttachments
                      attachments={message.attachments}
                      mine={mine}
                      chatId={chatId}
                    />
                  </div>
                )}
                {message.content && (
                  <span className="whitespace-pre-wrap break-words">{message.content}</span>
                )}
              </>
            )}
            {!editing && (
              <span
                className={cn(
                  'ml-2 inline-flex translate-y-0.5 items-center gap-0.5 text-[10px]',
                  mine ? 'text-accentink/70' : 'text-faint',
                )}
              >
                {message.edited_at && !deleted ? 'edited · ' : ''}
                {formatTime(message.created_at)}
                {mine &&
                  !deleted &&
                  status &&
                  (status === 'read' ? <CheckCheck size={13} /> : <Check size={13} />)}
              </span>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
