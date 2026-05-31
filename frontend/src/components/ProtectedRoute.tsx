import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '@/store/auth'
import { FullScreenLoader } from './FullScreenLoader'

export function ProtectedRoute() {
  const status = useAuth((s) => s.status)
  if (status === 'loading') return <FullScreenLoader label="Loading…" />
  if (status === 'guest') return <Navigate to="/login" replace />
  return <Outlet />
}
