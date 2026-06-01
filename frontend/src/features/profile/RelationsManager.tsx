import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Loader2, X } from 'lucide-react'

import {
  listBlocked,
  listMuted,
  unblockUser,
  unmuteUser,
} from '@/api/relations'
import type { UserPublic } from '@/api/types'
import { Avatar } from '@/components/Avatar'

function RelationList({
  title,
  queryKey,
  fetcher,
  action,
  actionLabel,
  empty,
}: {
  title: string
  queryKey: string
  fetcher: () => Promise<{ data: UserPublic[] }>
  action: (id: string) => Promise<unknown>
  actionLabel: string
  empty: string
}) {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: [queryKey], queryFn: () => fetcher().then((r) => r.data) })
  const mut = useMutation({
    mutationFn: (id: string) => action(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: [queryKey] }),
  })
  const users = data ?? []

  return (
    <div>
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-faint">{title}</p>
      {isLoading ? (
        <div className="flex justify-center py-4 text-faint">
          <Loader2 size={16} className="animate-spin" />
        </div>
      ) : users.length === 0 ? (
        <p className="py-3 text-sm text-faint">{empty}</p>
      ) : (
        <ul className="space-y-1">
          {users.map((u) => (
            <li key={u.id} className="flex items-center gap-3 py-1.5">
              <Avatar name={u.display_name} src={u.avatar_url} userId={u.id} size={36} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{u.display_name}</p>
                <p className="truncate text-xs text-faint">@{u.username}</p>
              </div>
              <button
                onClick={() => mut.mutate(u.id)}
                disabled={mut.isPending}
                className="rounded-full border border-border px-3 py-1 text-xs font-semibold transition hover:bg-cardhover disabled:opacity-50"
              >
                {actionLabel}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function RelationsManager({ onClose }: { onClose: () => void }) {
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
        className="max-h-[80vh] w-full max-w-sm space-y-5 overflow-y-auto rounded-3xl border border-border bg-elev p-6 shadow-soft"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">Blocked &amp; muted</h2>
          <button onClick={onClose} className="text-muted transition hover:text-text">
            <X size={18} />
          </button>
        </div>

        <RelationList
          title="Blocked"
          queryKey="blocked"
          fetcher={listBlocked}
          action={unblockUser}
          actionLabel="Unblock"
          empty="You haven't blocked anyone."
        />
        <RelationList
          title="Muted"
          queryKey="muted"
          fetcher={listMuted}
          action={unmuteUser}
          actionLabel="Unmute"
          empty="You haven't muted anyone."
        />
      </motion.div>
    </motion.div>
  )
}
