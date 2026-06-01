import { useQueryClient } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import { Camera, Lock, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { updateMe, uploadAvatar, type ProfileUpdate } from '@/api/users'
import { Avatar } from '@/components/Avatar'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { apiError } from '@/lib/error'
import { cn } from '@/lib/utils'
import { useAuth } from '@/store/auth'
import { AvatarCropper } from './AvatarCropper'

export function ProfileDialog({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const user = useAuth((s) => s.user)
  const setUser = useAuth((s) => s.setUser)
  const fileRef = useRef<HTMLInputElement>(null)

  const [name, setName] = useState(user?.display_name ?? '')
  const [bio, setBio] = useState(user?.bio ?? '')
  const [location, setLocation] = useState(user?.location ?? '')
  const [website, setWebsite] = useState(user?.website ?? '')
  const [isPrivate, setIsPrivate] = useState(user?.is_private ?? false)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(user?.avatar_url ?? null)
  const [cropSrc, setCropSrc] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    setCropSrc(URL.createObjectURL(f))
  }

  function onCropped(cropped: File) {
    setFile(cropped)
    if (preview && preview.startsWith('blob:')) {
      URL.revokeObjectURL(preview)
    }
    setPreview(URL.createObjectURL(cropped))
    if (cropSrc) {
      URL.revokeObjectURL(cropSrc)
      setCropSrc(null)
    }
  }

  async function onSave() {
    if (!user) return
    setBusy(true)
    setError('')
    try {
      let updated = user
      if (file) updated = (await uploadAvatar(file)).data

      const patch: ProfileUpdate = {}
      const dn = name.trim()
      if (dn && dn !== user.display_name) patch.display_name = dn
      const nb = bio.trim() || null
      if (nb !== (user.bio ?? null)) patch.bio = nb
      const nl = location.trim() || null
      if (nl !== (user.location ?? null)) patch.location = nl
      const nw = website.trim() || null
      if (nw !== (user.website ?? null)) patch.website = nw
      if (isPrivate !== (user.is_private ?? false)) patch.is_private = isPrivate

      if (Object.keys(patch).length) {
        updated = (await updateMe(patch)).data
      }

      setUser(updated)
      await Promise.all([
        qc.invalidateQueries({ queryKey: ['user', user.id] }),
        qc.invalidateQueries({ queryKey: ['chats'] }),
      ])

      if (preview && preview.startsWith('blob:')) URL.revokeObjectURL(preview)
      onClose()
    } catch (err) {
      setError(apiError(err))
    } finally {
      setBusy(false)
    }
  }

  const handleClose = () => {
    if (cropSrc) URL.revokeObjectURL(cropSrc)
    if (preview && preview.startsWith('blob:')) URL.revokeObjectURL(preview)
    onClose()
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={handleClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 10 }}
        transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
        onClick={(e) => e.stopPropagation()}
        className="max-h-[90vh] w-full max-w-sm overflow-y-auto rounded-3xl border border-border bg-elev p-6 shadow-soft"
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-base font-semibold">Edit profile</h2>
          <button onClick={handleClose} className="text-muted transition hover:text-text">
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

        <div className="space-y-3">
          <Input label="Display name" value={name} onChange={(e) => setName(e.target.value)} maxLength={64} />
          <label className="block">
            <span className="mb-1.5 block text-xs font-medium text-muted">Bio</span>
            <textarea
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              maxLength={280}
              rows={3}
              placeholder="Tell people about yourself"
              className="w-full resize-none rounded-xl border border-border bg-card px-4 py-3 text-sm text-text placeholder:text-faint transition focus:border-violet/60 focus:outline-none focus:ring-2 focus:ring-violet/30"
            />
            <span className="mt-1 block text-right text-[11px] text-faint">{bio.length}/280</span>
          </label>
          <Input
            label="Location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            maxLength={64}
            placeholder="City, country"
          />
          <Input
            label="Website"
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
            maxLength={255}
            placeholder="https://…"
          />

          <button
            type="button"
            onClick={() => setIsPrivate((v) => !v)}
            className="flex w-full items-center gap-3 rounded-xl border border-border bg-card px-4 py-3 text-left transition hover:bg-cardhover"
          >
            <Lock size={16} className="shrink-0 text-muted" />
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-medium">Private account</span>
              <span className="block text-[11px] text-faint">
                New followers must be approved before they can see your posts.
              </span>
            </span>
            <span
              className={cn(
                'relative h-6 w-10 shrink-0 rounded-full transition',
                isPrivate ? 'bg-accent' : 'bg-border',
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all',
                  isPrivate ? 'left-[18px]' : 'left-0.5',
                )}
              />
            </span>
          </button>
        </div>

        <p className="mt-3 text-xs text-faint">@{user?.username} · {user?.email}</p>

        {error && <p className="mt-3 text-sm text-danger">{error}</p>}

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="ghost" type="button" onClick={handleClose}>
            Cancel
          </Button>
          <Button onClick={onSave} loading={busy}>
            Save changes
          </Button>
        </div>
      </motion.div>

      <AnimatePresence>
        {cropSrc && (
          <AvatarCropper
            src={cropSrc}
            onCancel={() => {
              URL.revokeObjectURL(cropSrc)
              setCropSrc(null)
            }}
            onDone={onCropped}
          />
        )}
      </AnimatePresence>
    </motion.div>
  )
}
