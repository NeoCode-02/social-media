import { useQueryClient } from '@tanstack/react-query'
import { AnimatePresence } from 'framer-motion'
import { LogOut, MessagesSquare, Plus } from 'lucide-react'
import { useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'

import { logout } from '@/api/auth'
import { Avatar } from '@/components/Avatar'
import { useRealtime } from '@/realtime/useRealtime'
import { wsClient } from '@/realtime/ws'
import { useAuth } from '@/store/auth'
import { ChatList } from './ChatList'
import { NewChatDialog } from './NewChatDialog'

export function ChatLayout() {
  useRealtime()
  const me = useAuth((s) => s.user)
  const clear = useAuth((s) => s.clear)
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [newOpen, setNewOpen] = useState(false)

  async function onLogout() {
    try {
      await logout()
    } catch {
      /* ignore */
    }
    wsClient.close()
    qc.clear()
    clear()
    navigate('/login')
  }

  return (
    <div className="flex h-full">
      <aside className="flex w-80 shrink-0 flex-col border-r border-border bg-elev">
        <header className="flex items-center justify-between px-4 pb-2 pt-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent text-accentink">
              <MessagesSquare size={17} />
            </div>
            <span className="font-semibold tracking-tight">Pulse</span>
          </div>
          <button
            onClick={() => setNewOpen(true)}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-card text-text transition hover:bg-cardhover active:scale-95"
            title="New chat"
          >
            <Plus size={18} />
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto">
          <ChatList />
        </div>

        <footer className="flex items-center gap-3 border-t border-border px-4 py-3">
          <Avatar name={me?.display_name ?? '?'} src={me?.avatar_url} size={38} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{me?.display_name}</p>
            <p className="truncate text-xs text-faint">@{me?.username}</p>
          </div>
          <button
            onClick={onLogout}
            className="flex h-9 w-9 items-center justify-center rounded-full text-muted transition hover:bg-cardhover hover:text-danger"
            title="Sign out"
          >
            <LogOut size={17} />
          </button>
        </footer>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col bg-bg">
        <Outlet />
      </main>

      <AnimatePresence>
        {newOpen && <NewChatDialog onClose={() => setNewOpen(false)} />}
      </AnimatePresence>
    </div>
  )
}
