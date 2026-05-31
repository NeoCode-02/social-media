import { AnimatePresence } from 'framer-motion'
import { Download, FileText } from 'lucide-react'
import { useState } from 'react'

import { postAttachmentDownloadUrl } from '@/api/posts'
import type { Attachment } from '@/api/types'
import { Lightbox } from '@/components/Lightbox'
import { AudioPlayer } from '@/features/chat/AudioPlayer'
import { formatBytes, isAudio, isImage, isVideo } from '@/lib/utils'

async function download(att: Attachment) {
  const { data } = await postAttachmentDownloadUrl(att.id)
  const a = document.createElement('a')
  a.href = data.url
  a.download = att.name
  a.rel = 'noreferrer'
  document.body.appendChild(a)
  a.click()
  a.remove()
}

export function PostAttachments({ attachments }: { attachments: Attachment[] }) {
  const [lightbox, setLightbox] = useState<Attachment | null>(null)
  const images = attachments.filter((a) => isImage(a.mime) && !a.as_file)
  const grid = images.length > 1

  return (
    <div className="mt-2 space-y-2">
      {attachments.map((a) => {
        if (isImage(a.mime) && !a.as_file) {
          return (
            <button
              key={a.id}
              onClick={(e) => {
                e.stopPropagation()
                setLightbox(a)
              }}
              className={grid ? 'inline-block w-[calc(50%-4px)] align-top' : 'block'}
            >
              <img
                src={a.thumbnail_url}
                alt={a.name}
                className="max-h-96 w-full cursor-zoom-in rounded-2xl border border-border object-cover"
              />
            </button>
          )
        }
        if (isVideo(a.mime) && !a.as_file) {
          return (
            <video
              key={a.id}
              src={a.url}
              controls
              preload="metadata"
              onClick={(e) => e.stopPropagation()}
              className="max-h-96 w-full rounded-2xl border border-border"
            />
          )
        }
        if (isAudio(a.mime) && !a.as_file) {
          return (
            <div
              key={a.id}
              onClick={(e) => e.stopPropagation()}
              className="rounded-2xl border border-border bg-card px-3 py-2"
            >
              <AudioPlayer
                src={a.url}
                mine={false}
                voice={a.is_voice}
                name={a.is_voice ? undefined : a.name}
                durationMs={a.duration_ms}
              />
            </div>
          )
        }
        return (
          <button
            key={a.id}
            onClick={(e) => {
              e.stopPropagation()
              download(a)
            }}
            className="flex w-full items-center gap-2.5 rounded-2xl border border-border bg-card px-3 py-2.5 text-left transition hover:bg-cardhover"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent/15">
              <FileText size={18} className="text-accent" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-xs font-medium">{a.name}</span>
              <span className="block text-[10px] text-faint">{formatBytes(a.size)}</span>
            </span>
            <Download size={16} className="shrink-0 text-faint" />
          </button>
        )
      })}

      <AnimatePresence>
        {lightbox && (
          <Lightbox
            src={lightbox.url}
            name={lightbox.name}
            onClose={() => setLightbox(null)}
            onDownload={() => download(lightbox)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
