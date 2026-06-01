import { useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { X } from 'lucide-react'
import { useState } from 'react'
import TextareaAutosize from 'react-textarea-autosize'

import { editPost } from '@/api/posts'
import type { Post } from '@/api/types'
import { Button } from '@/components/Button'
import { apiError } from '@/lib/error'
import { patchAllPosts } from './postCache'

export function EditPostDialog({ post, onClose }: { post: Post; onClose: () => void }) {
  const qc = useQueryClient()
  const [text, setText] = useState(post.text ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const hasAttachments = post.attachments.length > 0
  const trimmed = text.trim()
  const canSave = (trimmed.length > 0 || hasAttachments) && trimmed !== (post.text ?? '')

  async function onSave() {
    setBusy(true)
    setError('')
    try {
      const { data } = await editPost(post.id, trimmed || null)
      patchAllPosts(qc, post.id, (p) => ({ ...p, text: data.text, edited_at: data.edited_at }))
      onClose()
    } catch (err) {
      setError(apiError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 10 }}
        transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-3xl border border-border bg-elev p-6 shadow-soft"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold">Edit post</h2>
          <button onClick={onClose} className="text-muted transition hover:text-text">
            <X size={18} />
          </button>
        </div>

        <TextareaAutosize
          value={text}
          onChange={(e) => setText(e.target.value)}
          minRows={3}
          maxRows={12}
          maxLength={2000}
          autoFocus
          className="w-full resize-none rounded-xl border border-border bg-card px-4 py-3 text-sm text-text outline-none focus:border-violet/50"
        />

        {error && <p className="mt-2 text-sm text-danger">{error}</p>}

        <div className="mt-5 flex justify-end gap-2">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={onSave} loading={busy} disabled={!canSave}>
            Save
          </Button>
        </div>
      </motion.div>
    </motion.div>
  )
}
