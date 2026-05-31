import { useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Camera, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { updateMe, uploadAvatar } from '@/api/users'
import { Avatar } from '@/components/Avatar'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { apiError } from '@/lib/error'
import { useAuth } from '@/store/auth'

export function ProfileDialog({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const user = useAuth((s) => s.user)
  const setUser = useAuth((s) => s.setUser)
  const fileRef = useRef<HTMLInputElement>(null)

  const [name, setName] = useState(user?.display_name ?? '')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(user?.avatar_url ?? null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
  }

  async function onSave() {
    setBusy(true)
    setError('')
    try {
      let updated = user
      if (file) updated = (await uploadAvatar(file)).data
      const trimmed = name.trim()
      if (trimmed && trimmed !== user?.display_name) {
        updated = (await updateMe({ display_name: trimmed })).data
      }
      if (updated) setUser(updated)
      await qc.invalidateQueries({ queryKey: ['chats'] })
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
        className="w-full max-w-sm overflow-hidden rounded-3xl border border-border bg-elev p-6 shadow-soft"
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-base font-semibold">Edit profile</h2>
          <button onClick={onClose} className="text-muted transition hover:text-text">
            <X size={18} />
          </button>
        </div>

        <div className="mb-5 flex justify-center">
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="group relative"
            title="Change photo"
          >
            <Avatar name={name || user?.username || '?'} src={preview} size={84} />
            <span className="absolute inset-0 flex items-center justify-center rounded-full bg-black/40 opacity-0 transition group-hover:opacity-100">
              <Camera size={22} className="text-white" />
            </span>
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            className="hidden"
            onChange={onPick}
          />
        </div>

        <Input label="Display name" value={name} onChange={(e) => setName(e.target.value)} maxLength={64} />
        <p className="mt-2 text-xs text-faint">@{user?.username} · {user?.email}</p>

        {error && <p className="mt-3 text-sm text-danger">{error}</p>}

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="ghost" type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={onSave} loading={busy}>
            Save changes
          </Button>
        </div>
      </motion.div>
    </motion.div>
  )
}
