import { useQueryClient } from '@tanstack/react-query'
import { Home, LogOut, MessagesSquare } from 'lucide-react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

import { logout } from '@/api/auth'
import { Avatar } from '@/components/Avatar'
import { useRealtime } from '@/realtime/useRealtime'
import { wsClient } from '@/realtime/ws'
import { useAuth } from '@/store/auth'
import { cn } from '@/lib/utils'

export function AppShell() {
  useRealtime()
  const me = useAuth((s) => s.user)
  const clear = useAuth((s) => s.clear)
  const qc = useQueryClient()
  const navigate = useNavigate()
  const { pathname } = useLocation()

  const feedActive = pathname.startsWith('/feed') || pathname.startsWith('/post')
  const chatActive = pathname.startsWith('/messages') || pathname.startsWith('/c/')
  const meActive = pathname === `/u/${me?.id}`

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
      <nav className="flex w-[68px] shrink-0 flex-col items-center gap-2 border-r border-border bg-elev py-4">
        <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-2xl bg-accent text-accentink">
          <MessagesSquare size={20} />
        </div>

        <RailButton label="Home" active={feedActive} onClick={() => navigate('/feed')}>
          <Home size={22} />
        </RailButton>
        <RailButton label="Messages" active={chatActive} onClick={() => navigate('/messages')}>
          <MessagesSquare size={22} />
        </RailButton>

        <div className="mt-auto flex flex-col items-center gap-3">
          <button
            onClick={() => me && navigate(`/u/${me.id}`)}
            title="Your profile"
            className={cn('rounded-full ring-2 transition', meActive ? 'ring-accent' : 'ring-transparent hover:ring-border')}
          >
            <Avatar name={me?.display_name ?? '?'} src={me?.avatar_url} size={38} />
          </button>
          <button
            onClick={onLogout}
            title="Sign out"
            className="flex h-10 w-10 items-center justify-center rounded-2xl text-muted transition hover:bg-cardhover hover:text-danger"
          >
            <LogOut size={20} />
          </button>
        </div>
      </nav>

      <main className="min-w-0 flex-1 bg-bg">
        <Outlet />
      </main>
    </div>
  )
}

function RailButton({
  label,
  active,
  onClick,
  children,
}: {
  label: string
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={cn(
        'flex h-12 w-12 items-center justify-center rounded-2xl transition',
        active ? 'bg-accent/15 text-accent' : 'text-muted hover:bg-cardhover hover:text-text',
      )}
    >
      {children}
    </button>
  )
}
