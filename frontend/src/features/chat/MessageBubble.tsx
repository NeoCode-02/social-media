import { motion } from 'framer-motion'
import { Check, CheckCheck } from 'lucide-react'

import type { Message } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { cn, formatTime } from '@/lib/utils'

interface Props {
  message: Message
  mine: boolean
  showSender: boolean
  status?: 'sent' | 'read'
}

export function MessageBubble({ message, mine, showSender, status }: Props) {
  const deleted = Boolean(message.deleted_at)

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
      className={cn('flex gap-2', mine ? 'justify-end' : 'justify-start')}
    >
      {!mine && (
        <div className="w-8 shrink-0 self-end">
          {showSender && <Avatar name={message.sender.display_name} src={message.sender.avatar_url} size={32} />}
        </div>
      )}

      <div className={cn('max-w-[68%]', mine ? 'items-end' : 'items-start')}>
        {!mine && showSender && (
          <span className="mb-1 ml-1 block text-xs font-medium text-muted">
            {message.sender.display_name}
          </span>
        )}
        <div
          className={cn(
            'rounded-2xl px-3.5 py-2 text-sm leading-relaxed shadow-soft',
            mine
              ? 'rounded-br-md bg-accent text-accentink'
              : 'rounded-bl-md bg-card text-text',
          )}
        >
          {deleted ? (
            <span className={cn('italic', mine ? 'text-accentink/70' : 'text-faint')}>
              This message was deleted
            </span>
          ) : (
            <span className="whitespace-pre-wrap break-words">{message.content}</span>
          )}
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
        </div>
      </div>
    </motion.div>
  )
}
