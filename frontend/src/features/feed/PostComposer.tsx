import { ImageIcon, Loader2, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { createPost, uploadPostAttachment } from '@/api/posts'
import type { Attachment, Post } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { apiError } from '@/lib/error'
import { isImage, isVideo } from '@/lib/utils'
import { useAuth } from '@/store/auth'

const MAX_ATTACHMENTS = 4
const MAX_UPLOAD_BYTES = 100 * 1024 * 1024

interface Props {
  parentId?: string
  placeholder?: string
  autoFocus?: boolean
  onPosted?: (post: Post) => void
}

export function PostComposer({ parentId, placeholder, autoFocus, onPosted }: Props) {
  const me = useAuth((s) => s.user)
  const [text, setText] = useState('')
  const [attachments, setAttachments] = useState<Attachment[]>([])
  const [uploading, setUploading] = useState(false)
  const [posting, setPosting] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

  async function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setError('')
    if (file.size > MAX_UPLOAD_BYTES) {
      setError(`"${file.name}" is too large (max 100MB)`)
      return
    }
    setUploading(true)
    try {
      const { data } = await uploadPostAttachment(file)
      setAttachments((a) => [...a, data])
    } catch (err) {
      setError(apiError(err))
    } finally {
      setUploading(false)
    }
  }

  async function submit() {
    const body = text.trim()
    if ((!body && attachments.length === 0) || posting) return
    setPosting(true)
    setError('')
    try {
      const { data } = await createPost({
        text: body || null,
        attachment_ids: attachments.length ? attachments.map((a) => a.id) : undefined,
        parent_id: parentId,
      })
      setText('')
      setAttachments([])
      onPosted?.(data)
    } catch (err) {
      setError(apiError(err))
    } finally {
      setPosting(false)
    }
  }

  const canPost = (text.trim() || attachments.length > 0) && !posting && !uploading

  return (
    <div className="flex gap-3 px-4 py-3">
      <Avatar name={me?.display_name ?? '?'} src={me?.avatar_url} size={40} />
      <div className="min-w-0 flex-1">
        <textarea
          autoFocus={autoFocus}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit()
          }}
          rows={parentId ? 2 : 3}
          maxLength={2000}
          placeholder={placeholder ?? "What's happening?"}
          className="w-full resize-none bg-transparent text-[15px] outline-none placeholder:text-faint"
        />

        {attachments.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2">
            {attachments.map((a) => (
              <div key={a.id} className="relative">
                {isImage(a.mime) ? (
                  <img src={a.thumbnail_url} alt={a.name} className="h-20 w-20 rounded-xl object-cover" />
                ) : isVideo(a.mime) ? (
                  <video src={a.url} className="h-20 w-20 rounded-xl object-cover" />
                ) : (
                  <div className="flex h-20 w-20 items-center justify-center rounded-xl bg-card text-[10px] text-faint">
                    {a.name.split('.').pop()?.toUpperCase()}
                  </div>
                )}
                <button
                  onClick={() => setAttachments((list) => list.filter((x) => x.id !== a.id))}
                  className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-black/70 text-white"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}

        {error && <p className="mb-2 text-xs text-danger">{error}</p>}

        <div className="flex items-center justify-between border-t border-border pt-2">
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={attachments.length >= MAX_ATTACHMENTS || uploading}
            className="flex h-9 w-9 items-center justify-center rounded-full text-accent transition hover:bg-accent/10 disabled:opacity-40"
            title="Add photo or video"
          >
            {uploading ? <Loader2 size={18} className="animate-spin" /> : <ImageIcon size={18} />}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*,video/*"
            className="hidden"
            onChange={onPick}
          />
          <button
            onClick={submit}
            disabled={!canPost}
            className="rounded-full bg-accent px-5 py-2 text-sm font-semibold text-accentink transition hover:brightness-105 active:scale-95 disabled:opacity-40"
          >
            {parentId ? 'Reply' : 'Post'}
          </button>
        </div>
      </div>
    </div>
  )
}
