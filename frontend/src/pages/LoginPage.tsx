import { type AxiosError } from 'axios'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { googleLoginUrl, login } from '@/api/auth'
import { establishSession } from '@/api/session'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { AuthShell } from '@/features/auth/AuthShell'
import { apiError } from '@/lib/error'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await login(email, password)
      await establishSession(data.access_token)
      navigate('/')
    } catch (err) {
      if ((err as AxiosError).response?.status === 403) {
        navigate('/verify', { state: { email } })
        return
      }
      setError(apiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to continue to your conversations."
      footer={
        <>
          New here?{' '}
          <Link to="/register" className="font-medium text-violet hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />
        {error && <p className="text-sm text-danger">{error}</p>}
        <Button type="submit" loading={loading} className="w-full">
          Sign in
        </Button>
      </form>

      <div className="my-5 flex items-center gap-3 text-xs text-faint">
        <span className="h-px flex-1 bg-border" />
        or
        <span className="h-px flex-1 bg-border" />
      </div>

      <a href={googleLoginUrl}>
        <Button variant="subtle" className="w-full" type="button">
          Continue with Google
        </Button>
      </a>
    </AuthShell>
  )
}
