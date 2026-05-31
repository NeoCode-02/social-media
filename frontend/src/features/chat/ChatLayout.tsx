import { AnimatePresence } from 'framer-motion'
import { MessagesSquare, Plus } from 'lucide-react'
import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import { ChatList } from './ChatList'
import { NewChatDialog } from './NewChatDialog'

export function ChatLayout() {
  const [newOpen, setNewOpen] = useState(false)

  return (
    <div className="flex h-full">
      <aside className="flex w-80 shrink-0 flex-col border-r border-border bg-elev">
        <header className="flex items-center justify-between px-4 pb-2 pt-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent text-accentink">
              <MessagesSquare size={17} />
            </div>
            <span className="font-semibold tracking-tight">Messages</span>
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
