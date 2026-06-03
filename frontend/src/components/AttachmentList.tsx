import { X } from 'lucide-react'

import type { Attachment } from '@/api/types'
import { isImage, isVideo } from '@/lib/utils'

interface Props {
  attachments: Attachment[]
  onRemove: (id: string) => void
  /** Render as a wrapping grid (feed) vs an inline bubble (chat). */
  variant?: 'grid' | 'inline'
  className?: string
}

function Thumbnail({ a, onRemove }: { a: Attachment; onRemove: () => void }) {
  const label = a.name.split('.').pop()?.toUpperCase()
  const showImage = isImage(a.mime) && a.thumbnail_url
  const showVideo = isVideo(a.mime) && a.url
  return (
    <div className="relative">
      {showImage ? (
        <img
          src={a.thumbnail_url ?? a.url}
          alt={a.name}
          className="h-20 w-20 rounded-xl object-cover"
        />
      ) : showVideo ? (
        <video src={a.url} className="h-20 w-20 rounded-xl object-cover" />
      ) : (
        <div className="flex h-20 w-20 items-center justify-center rounded-xl bg-card text-[10px] text-faint">
          {label}
        </div>
      )}
      <button
        onClick={onRemove}
        aria-label={`Remove ${a.name}`}
        className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-black/70 text-white"
      >
        <X size={12} />
      </button>
    </div>
  )
}

/**
 * Shared thumbnail strip used by both the post composer and the chat
 * message input. Identical UX, single source of truth.
 */
export function AttachmentList({
  attachments,
  onRemove,
  variant = 'grid',
  className = '',
}: Props) {
  if (attachments.length === 0) return null
  return (
    <div
      className={
        variant === 'grid'
          ? `mb-2 flex flex-wrap gap-2 ${className}`
          : `flex gap-2 ${className}`
      }
    >
      {attachments.map((a) => (
        <Thumbnail key={a.id} a={a} onRemove={() => onRemove(a.id)} />
      ))}
    </div>
  )
}
