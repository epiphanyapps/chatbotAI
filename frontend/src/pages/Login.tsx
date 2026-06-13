import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../utils/api'
import { useFingerprint } from '../utils/fingerprint'

export default function Login() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'sent' | 'error'>('idle')
  const [error, setError] = useState('')
  const { visitorId } = useFingerprint()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')
    setError('')

    try {
      await api('/auth/magic-link', {
        method: 'POST',
        body: JSON.stringify({
          email,
          fingerprint: visitorId
        })
      })
      setStatus('sent')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send login link')
      setStatus('error')
    }
  }

  if (status === 'sent') {
    return (
      <div style={{ maxWidth: 400, margin: '100px auto', padding: 20, textAlign: 'center' }}>
        <h1>Check your email</h1>
        <p>We sent a login link to <strong>{email}</strong></p>
        <p>The link expires in 15 minutes.</p>
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 400, margin: '100px auto', padding: 20 }}>
      <h1>Sign in to IntimateAI</h1>
      <p>Enter your email to receive a magic link.</p>

      <form onSubmit={handleSubmit}>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="your@email.com"
          required
          style={{ width: '100%', padding: 10, marginBottom: 10, fontSize: 16 }}
        />

        <button
          type="submit"
          disabled={status === 'loading'}
          style={{ width: '100%', padding: 10, fontSize: 16, cursor: 'pointer' }}
        >
          {status === 'loading' ? 'Sending...' : 'Send login link'}
        </button>

        {error && <p style={{ color: 'red', marginTop: 10 }}>{error}</p>}
      </form>

      <p style={{ marginTop: 20, fontSize: 14, color: '#666' }}>
        By continuing, you agree to our{' '}
        <Link to="/terms">Terms of Service</Link> and{' '}
        <Link to="/privacy">Privacy Policy</Link>.
      </p>
    </div>
  )
}
