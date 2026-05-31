import { useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Check, Search, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { createDm, createGroup, searchUsers } from '@/api/chats'
import type { UserPublic } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { Button } from '@/components/Button'
import { apiError } from '@/lib/error'

export function NewChatDialog({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [results, setResults] = useState<UserPublic[]>([])
  const [selected, setSelected] = useState<Record<string, UserPublic>>({})
  const [title, setTitle] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const t = setTimeout(async () => {
      const term = q.trim()
      if (!term) {
        setResults([])
        return
      }
      try {
        const { data } = await searchUsers(term)
        setResults(data)
      } catch {
        setResults([])
      }
    }, 250)
    return () => clearTimeout(t)
  }, [q])

  const selectedList = Object.values(selected)
  const isGroup = selectedList.length > 1

  function toggle(user: UserPublic) {
    setSelected((s) => {
      const next = { ...s }
      if (next[user.id]) delete next[user.id]
      else next[user.id] = user
      return next
    })
  }

  async function onCreate() {
    if (selectedList.length === 0) return
    setBusy(true)
    setError('')
    try {
      const ids = selectedList.map((u) => u.id)
      const { data } = isGroup
        ? await createGroup(title.trim() || `${selectedList[0].display_name} & ${ids.length - 1} more`, ids)
        : await createDm(ids[0])
      await qc.invalidateQueries({ queryKey: ['chats'] })
      navigate(`/c/${data.id}`)
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
        className="w-full max-w-md overflow-hidden rounded-3xl border border-border bg-elev shadow-soft"
      >
        <div className="flex items-center justify-between px-5 py-4">
          <h2 className="text-base font-semibold">New conversation</h2>
          <button onClick={onClose} className="text-muted transition hover:text-text">
            <X size={18} />
          </button>
        </div>

        <div className="px-5">
          <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3">
            <Search size={16} className="text-faint" />
            <input
              autoFocus
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search people by username…"
              className="w-full bg-transparent py-3 text-sm outline-none placeholder:text-faint"
            />
          </div>
        </div>

        {selectedList.length > 0 && (
          <div className="flex flex-wrap gap-2 px-5 pt-3">
            {selectedList.map((u) => (
              <button
                key={u.id}
                onClick={() => toggle(u)}
                className="flex items-center gap-1.5 rounded-full bg-card py-1 pl-1 pr-2.5 text-xs"
              >
                <Avatar name={u.display_name} src={u.avatar_url} size={20} />
                {u.display_name}
                <X size={12} className="text-faint" />
              </button>
            ))}
          </div>
        )}

        <div className="max-h-64 overflow-y-auto px-2 py-2">
          {results.map((u) => {
            const on = Boolean(selected[u.id])
            return (
              <button
                key={u.id}
                onClick={() => toggle(u)}
                className="flex w-full items-center gap-3 rounded-2xl px-3 py-2 text-left transition hover:bg-cardhover"
              >
                <Avatar name={u.display_name} src={u.avatar_url} size={38} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{u.display_name}</p>
                  <p className="truncate text-xs text-faint">@{u.username}</p>
                </div>
                {on && (
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-accent text-accentink">
                    <Check size={13} />
                  </span>
                )}
              </button>
            )
          })}
          {q.trim() && results.length === 0 && (
            <p className="px-3 py-6 text-center text-sm text-faint">No people found</p>
          )}
        </div>

        {isGroup && (
          <div className="px-5 pb-1">
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Group name (optional)"
              className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm outline-none placeholder:text-faint focus:border-violet/60"
            />
          </div>
        )}

        <div className="flex items-center justify-between gap-3 px-5 py-4">
          <span className="text-xs text-danger">{error}</span>
          <Button onClick={onCreate} loading={busy} disabled={selectedList.length === 0}>
            {isGroup ? 'Create group' : 'Start chat'}
          </Button>
        </div>
      </motion.div>
    </motion.div>
  )
}
