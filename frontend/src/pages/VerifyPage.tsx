import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { resendCode, verifyEmail } from '@/api/auth'
import { establishSession } from '@/api/session'
import { Button } from '@/components/Button'
import { Input } from '@/components/Input'
import { AuthShell } from '@/features/auth/AuthShell'
import { apiError } from '@/lib/error'

export function VerifyPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const initialEmail = (location.state as { email?: string } | null)?.email ?? ''

  const [email, setEmail] = useState(initialEmail)
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await verifyEmail(email, code)
      await establishSession(data.access_token)
      navigate('/')
    } catch (err) {
      setError(apiError(err))
    } finally {
      setLoading(false)
    }
  }

  async function onResend() {
    setError('')
    setNote('')
    try {
      await resendCode(email)
      setNote('A new code is on its way.')
    } catch (err) {
      setError(apiError(err))
    }
  }

  return (
    <AuthShell
      title="Verify your email"
      subtitle="Enter the 6-digit code we sent you."
      footer={
        <Link to="/login" className="font-medium text-violet hover:underline">
          Back to sign in
        </Link>
      }
    >
      <form onSubmit={onSubmit} className="space-y-4">
        {!initialEmail && (
          <Input
            label="Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        )}
        <Input
          label="Verification code"
          inputMode="numeric"
          pattern="\d{6}"
          maxLength={6}
          required
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
          placeholder="000000"
          className="text-center text-lg tracking-[0.5em]"
        />
        {error && <p className="text-sm text-danger">{error}</p>}
        {note && <p className="text-sm text-online">{note}</p>}
        <Button type="submit" loading={loading} className="w-full">
          Verify & continue
        </Button>
      </form>

      <button
        type="button"
        onClick={onResend}
        className="mt-4 w-full text-center text-xs text-muted transition hover:text-text"
      >
        Didn’t get it? Resend code
      </button>
    </AuthShell>
  )
}
