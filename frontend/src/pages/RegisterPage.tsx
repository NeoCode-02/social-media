import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { registerUser } from '@/api/auth'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { AuthShell } from '@/features/auth/AuthShell'
import { apiError } from '@/lib/error'

export function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ display_name: '', username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await registerUser(form)
      navigate('/verify', { state: { email: form.email } })
    } catch (err) {
      setError(apiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Join Pulse and start chatting in seconds."
      footer={
        <>
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-violet hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Display name"
          required
          value={form.display_name}
          onChange={set('display_name')}
          placeholder="Ada Lovelace"
        />
        <Input
          label="Username"
          required
          value={form.username}
          onChange={set('username')}
          placeholder="ada"
          hint="3–32 chars: letters, numbers, underscore"
        />
        <Input
          label="Email"
          type="email"
          required
          value={form.email}
          onChange={set('email')}
          placeholder="you@example.com"
        />
        <Input
          label="Password"
          type="password"
          required
          value={form.password}
          onChange={set('password')}
          placeholder="At least 8 characters"
        />
        {error && <p className="text-sm text-danger">{error}</p>}
        <Button type="submit" loading={loading} className="w-full">
          Create account
        </Button>
      </form>
    </AuthShell>
  )
}
