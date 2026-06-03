import { useState } from 'react'

import { createPost, uploadPostAttachment } from '@/api/posts'
import type { Attachment, Post } from '@/api/types'
import { AttachmentList } from '@/components/AttachmentList'
import { AttachmentPicker } from '@/components/AttachmentPicker'
import { Avatar } from '@/components/Avatar'
import { apiError } from '@/lib/error'
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

  async function onPick(file: File) {
    setError('')
    if (attachments.length >= MAX_ATTACHMENTS) {
      setError(`You can attach up to ${MAX_ATTACHMENTS} items per post.`)
      return
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setError(`"${file.name}" is too large (max 100MB)`)
      return
    }
    setUploading(true)
    try {
      const { data } = await uploadPostAttachment(file)
      setAttachments((a) => {
        if (a.length >= MAX_ATTACHMENTS) {
          setError(`You can attach up to ${MAX_ATTACHMENTS} items per post.`)
          return a
        }
        return [...a, data]
      })
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

        <AttachmentList
          attachments={attachments}
          onRemove={(id) => setAttachments((list) => list.filter((a) => a.id !== id))}
        />

        {error && <p className="mb-2 text-xs text-danger">{error}</p>}

        <div className="flex items-center justify-between border-t border-border pt-2">
          <AttachmentPicker
            disabled={attachments.length >= MAX_ATTACHMENTS}
            uploading={uploading}
            onPick={onPick}
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
