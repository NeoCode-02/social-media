import { AnimatePresence } from 'framer-motion'
import { Download, FileText } from 'lucide-react'
import { useState } from 'react'

import { getAttachmentDownloadUrl } from '@/api/chats'
import type { Attachment } from '@/api/types'
import { Lightbox } from '@/components/Lightbox'
import { cn, formatBytes, isAudio, isImage, isVideo } from '@/lib/utils'
import { AudioPlayer } from './AudioPlayer'

interface Props {
  attachments: Attachment[]
  mine: boolean
  chatId: string
}

async function triggerDownload(chatId: string, att: Attachment) {
  const { data } = await getAttachmentDownloadUrl(chatId, att.id)
  const a = document.createElement('a')
  a.href = data.url
  a.download = att.name
  a.rel = 'noreferrer'
  document.body.appendChild(a)
  a.click()
  a.remove()
}

export function MessageAttachments({ attachments, mine, chatId }: Props) {
  const [lightbox, setLightbox] = useState<Attachment | null>(null)

  return (
    <div className="space-y-1.5">
      {attachments.map((a) => {
        const inlineImage = isImage(a.mime) && !a.as_file
        const inlineVideo = isVideo(a.mime) && !a.as_file
        const inlineAudio = isAudio(a.mime) && !a.as_file

        if (inlineImage) {
          return (
            <button key={a.id} onClick={() => setLightbox(a)} className="block">
              <img
                src={a.thumbnail_url}
                alt={a.name}
                className="max-h-64 w-auto max-w-full cursor-zoom-in rounded-xl object-cover"
              />
            </button>
          )
        }

        if (inlineVideo) {
          return (
            <video
              key={a.id}
              src={a.url}
              controls
              preload="metadata"
              className="max-h-64 w-auto max-w-full rounded-xl"
            />
          )
        }

        if (inlineAudio) {
          return (
            <div
              key={a.id}
              className={cn('rounded-xl px-3 py-2', mine ? 'bg-black/10' : 'bg-black/20')}
            >
              <AudioPlayer
                src={a.url}
                mine={mine}
                voice={a.is_voice}
                name={a.is_voice ? undefined : a.name}
                durationMs={a.duration_ms}
              />
            </div>
          )
        }

        // Everything else (docs, archives, images-as-file) → downloadable card.
        return (
          <button
            key={a.id}
            onClick={() => triggerDownload(chatId, a)}
            className={cn(
              'flex w-full items-center gap-2.5 rounded-xl px-2.5 py-2 text-left transition',
              mine ? 'bg-black/10 hover:bg-black/20' : 'bg-black/20 hover:bg-black/30',
            )}
            title={`Download ${a.name}`}
          >
            <span
              className={cn(
                'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg',
                mine ? 'bg-accentink/15' : 'bg-accent/15',
              )}
            >
              <FileText size={18} />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-xs font-medium">{a.name}</span>
              <span className="block text-[10px] opacity-70">{formatBytes(a.size)}</span>
            </span>
            <Download size={16} className="shrink-0 opacity-60" />
          </button>
        )
      })}

      <AnimatePresence>
        {lightbox && (
          <Lightbox
            src={lightbox.url}
            name={lightbox.name}
            onClose={() => setLightbox(null)}
            onDownload={() => triggerDownload(chatId, lightbox)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
