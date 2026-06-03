import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AnimatePresence, motion } from 'framer-motion'
import { Ban, Flag, MoreHorizontal, Undo2, Volume2, VolumeX } from 'lucide-react'
import { useState } from 'react'

import { blockUser, muteUser, unblockUser, unmuteUser } from '@/api/relations'
import type { UserProfile } from '@/api/types'
import { ReportDialog } from '@/components/ReportDialog'

interface Toast {
  message: string
  undo: () => void
}

export function UserMenu({ profile }: { profile: UserProfile }) {
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [reporting, setReporting] = useState(false)
  const [toast, setToast] = useState<Toast | null>(null)

  function refresh() {
    qc.invalidateQueries({ queryKey: ['user', profile.id] })
    qc.invalidateQueries({ queryKey: ['userFeed', profile.id] })
    qc.invalidateQueries({ queryKey: ['timeline'] })
    qc.invalidateQueries({ queryKey: ['globalFeed'] })
  }

  function flash(message: string, undo: () => void) {
    setOpen(false)
    setToast({ message, undo })
    window.setTimeout(() => setToast((t) => (t?.undo === undo ? null : t)), 5000)
  }

  const block = useMutation({
    mutationFn: () => (profile.is_blocked ? unblockUser(profile.id) : blockUser(profile.id)),
    onSuccess: () => {
      refresh()
      flash(
        profile.is_blocked ? `Unblocked @${profile.username}` : `Blocked @${profile.username}`,
        () => block.mutate(),
      )
    },
  })
  const mute = useMutation({
    mutationFn: () => (profile.is_muted ? unmuteUser(profile.id) : muteUser(profile.id)),
    onSuccess: () => {
      refresh()
      flash(
        profile.is_muted ? `Unmuted @${profile.username}` : `Muted @${profile.username}`,
        () => mute.mutate(),
      )
    },
  })

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-label="More options"
        className="flex h-10 w-10 items-center justify-center rounded-full border border-border transition hover:bg-cardhover"
      >
        <MoreHorizontal size={17} />
      </button>
      {open && <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 6, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.96 }}
            transition={{ duration: 0.15, ease: [0.22, 1, 0.36, 1] }}
            className="absolute right-0 top-12 z-20 w-44 overflow-hidden rounded-2xl border border-border bg-elev p-1.5 shadow-soft"
          >
            <button
              onClick={() => {
                setOpen(false)
                setReporting(true)
              }}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm transition hover:bg-cardhover"
            >
              <Flag size={16} /> Report
            </button>
            <button
              onClick={() => mute.mutate()}
              disabled={mute.isPending}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm transition hover:bg-cardhover disabled:opacity-50"
            >
              {profile.is_muted ? <Volume2 size={16} /> : <VolumeX size={16} />}
              {profile.is_muted ? 'Unmute' : 'Mute'}
            </button>
            <button
              onClick={() => block.mutate()}
              disabled={block.isPending}
              className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm text-danger transition hover:bg-danger/10 disabled:opacity-50"
            >
              <Ban size={16} />
              {profile.is_blocked ? 'Unblock' : 'Block'}
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {reporting && (
          <ReportDialog
            targetType="user"
            targetId={profile.id}
            label={`@${profile.username}`}
            onClose={() => setReporting(false)}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            className="fixed bottom-6 left-1/2 z-[70] flex -translate-x-1/2 items-center gap-3 rounded-full border border-border bg-elev px-4 py-2.5 text-sm shadow-soft"
            role="status"
          >
            <span>{toast.message}</span>
            <button
              onClick={() => {
                toast.undo()
                setToast(null)
              }}
              className="flex items-center gap-1 font-semibold text-accent hover:underline"
            >
              <Undo2 size={14} /> Undo
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
