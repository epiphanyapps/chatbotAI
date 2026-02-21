import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { useFingerprint } from '../utils/fingerprint'

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login } = useAuth()
  const { visitorId, loading: fpLoading } = useFingerprint()
  const [status, setStatus] = useState<'verifying' | 'success' | 'error'>('verifying')
  const [error, setError] = useState('')

  useEffect(() => {
    const verifyToken = async () => {
      if (fpLoading) return

      const token = searchParams.get('token')
      if (!token) {
        setError('No verification token found')
        setStatus('error')
        return
      }

      try {
        const data = await api(`/auth/verify?token=${encodeURIComponent(token)}&fingerprint=${visitorId || ''}`)
        login(data.access_token)
        setStatus('success')
        // Redirect to age gate after short delay
        setTimeout(() => navigate('/age-gate'), 1000)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Verification failed')
        setStatus('error')
      }
    }

    verifyToken()
  }, [searchParams, visitorId, fpLoading, login, navigate])

  if (status === 'verifying') {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <h1>Verifying your email...</h1>
        <p>Please wait.</p>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div style={{ textAlign: 'center', marginTop: 100 }}>
        <h1>Email verified!</h1>
        <p>Redirecting you...</p>
      </div>
    )
  }

  return (
    <div style={{ textAlign: 'center', marginTop: 100 }}>
      <h1>Verification failed</h1>
      <p style={{ color: 'red' }}>{error}</p>
      <a href="/login">Try again</a>
    </div>
  )
}
