import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Check, Loader2, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import {
  acceptFollowRequest,
  listFollowRequests,
  rejectFollowRequest,
} from '@/api/follows'
import { Avatar } from '@/components/Avatar'
import { useAuth } from '@/store/auth'

export function FollowRequests({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const meId = useAuth((s) => s.user?.id)

  const { data, isLoading } = useQuery({
    queryKey: ['followRequests'],
    queryFn: () => listFollowRequests().then((r) => r.data),
  })

  function afterAction() {
    qc.invalidateQueries({ queryKey: ['followRequests'] })
    if (meId) qc.invalidateQueries({ queryKey: ['user', meId] })
  }

  const accept = useMutation({
    mutationFn: (id: string) => acceptFollowRequest(id),
    onSuccess: afterAction,
  })
  const reject = useMutation({
    mutationFn: (id: string) => rejectFollowRequest(id),
    onSuccess: afterAction,
  })

  const requests = data ?? []

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
        className="max-h-[80vh] w-full max-w-sm overflow-y-auto rounded-3xl border border-border bg-elev p-6 shadow-soft"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-semibold">Follow requests</h2>
          <button onClick={onClose} className="text-muted transition hover:text-text">
            <X size={18} />
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-8 text-faint">
            <Loader2 size={20} className="animate-spin" />
          </div>
        ) : requests.length === 0 ? (
          <p className="py-8 text-center text-sm text-faint">No pending requests.</p>
        ) : (
          <ul className="space-y-1">
            {requests.map((u) => (
              <li key={u.id} className="flex items-center gap-3 rounded-xl px-1 py-1.5">
                <button
                  onClick={() => {
                    onClose()
                    navigate(`/u/${u.id}`)
                  }}
                  className="flex min-w-0 flex-1 items-center gap-3 text-left"
                >
                  <Avatar name={u.display_name} src={u.avatar_url} userId={u.id} size={40} />
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold">{u.display_name}</span>
                    <span className="block truncate text-xs text-faint">@{u.username}</span>
                  </span>
                </button>
                <button
                  onClick={() => accept.mutate(u.id)}
                  disabled={accept.isPending || reject.isPending}
                  aria-label={`Accept ${u.username}`}
                  className="flex h-9 w-9 items-center justify-center rounded-full bg-accent text-accentink transition hover:brightness-105 disabled:opacity-40"
                >
                  <Check size={17} />
                </button>
                <button
                  onClick={() => reject.mutate(u.id)}
                  disabled={accept.isPending || reject.isPending}
                  aria-label={`Reject ${u.username}`}
                  className="flex h-9 w-9 items-center justify-center rounded-full border border-border text-muted transition hover:border-danger hover:text-danger disabled:opacity-40"
                >
                  <X size={17} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </motion.div>
    </motion.div>
  )
}
