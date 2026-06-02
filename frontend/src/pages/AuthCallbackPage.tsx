import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import { establishSession } from '@/api/session'
import { FullScreenLoader } from '@/components/FullScreenLoader'

export function AuthCallbackPage() {
  const navigate = useNavigate()

  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.slice(1))
    const token = params.get('access_token')
    // Strip the token from the URL so it doesn't linger in history / Referer.
    window.history.replaceState(null, '', window.location.pathname)
    if (!token) {
      navigate('/login', { replace: true })
      return
    }
    establishSession(token)
      .then(() => navigate('/', { replace: true }))
      .catch(() => navigate('/login', { replace: true }))
  }, [navigate])

  return <FullScreenLoader label="Signing you in…" />
}
