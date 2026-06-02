import { motion } from 'framer-motion'
import { Flag, X } from 'lucide-react'
import { useState } from 'react'

import { createReport } from '@/api/admin'
import type { ReportTarget } from '@/api/types'
import { Button } from '@/components/Button'
import { apiError } from '@/lib/error'

interface Props {
  targetType: ReportTarget
  targetId: string
  label: string
  onClose: () => void
}

export function ReportDialog({ targetType, targetId, label, onClose }: Props) {
  const [reason, setReason] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  async function submit() {
    setBusy(true)
    setError('')
    try {
      await createReport(targetType, targetId, reason.trim())
      setDone(true)
      setTimeout(onClose, 900)
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
      onClick={(e) => {
        e.stopPropagation()
        onClose()
      }}
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 10 }}
        transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm rounded-3xl border border-border bg-elev p-6 shadow-soft"
      >
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-semibold">
            <Flag size={16} className="text-danger" /> Report {label}
          </h2>
          <button onClick={onClose} className="text-muted transition hover:text-text">
            <X size={18} />
          </button>
        </div>

        {done ? (
          <p className="py-6 text-center text-sm text-online">Thanks — our moderators will review it.</p>
        ) : (
          <>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              maxLength={280}
              rows={3}
              autoFocus
              placeholder="What's wrong? (optional)"
              className="w-full resize-none rounded-xl border border-border bg-card px-4 py-3 text-sm outline-none focus:border-violet/50"
            />
            {error && <p className="mt-2 text-sm text-danger">{error}</p>}
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="ghost" type="button" onClick={onClose}>
                Cancel
              </Button>
              <Button onClick={submit} loading={busy}>
                Submit report
              </Button>
            </div>
          </>
        )}
      </motion.div>
    </motion.div>
  )
}
