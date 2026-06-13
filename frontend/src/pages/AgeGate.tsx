import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiWithAuth } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { useFingerprint } from '../utils/fingerprint'

export default function AgeGate() {
  const navigate = useNavigate()
  const { checkAgeStatus, isAgeVerified } = useAuth()
  const { visitorId } = useFingerprint()
  const [confirmationText, setConfirmationText] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    // If already verified, redirect
    if (isAgeVerified) {
      navigate('/')
      return
    }

    // Fetch confirmation text
    const fetchText = async () => {
      try {
        const data = await apiWithAuth('/legal/age-confirmation-text')
        setConfirmationText(data.text)
      } catch {
        setConfirmationText(
          'I confirm that I am at least 18 years old and legally permitted to access adult content in my jurisdiction.'
        )
      }
      setLoading(false)
    }
    fetchText()
  }, [isAgeVerified, navigate])

  const handleConfirm = async () => {
    setError('')
    try {
      await apiWithAuth('/legal/age-verify', {
        method: 'POST',
        body: JSON.stringify({
          confirmed: true,
          fingerprint: visitorId
        })
      })
      await checkAgeStatus()
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Verification failed')
    }
  }

  const handleDecline = async () => {
    try {
      await apiWithAuth('/legal/age-verify', {
        method: 'POST',
        body: JSON.stringify({
          confirmed: false,
          fingerprint: visitorId
        })
      })
    } catch {
      // Expected to fail with 403
    }
    // Redirect to external site or show message
    window.location.href = 'https://google.com'
  }

  if (loading) {
    return <div style={{ textAlign: 'center', marginTop: 100 }}>Loading...</div>
  }

  return (
    <div style={{
      maxWidth: 500,
      margin: '50px auto',
      padding: 30,
      textAlign: 'center',
      border: '2px solid #333',
      borderRadius: 10,
      backgroundColor: '#f9f9f9'
    }}>
      <h1>Age Verification Required</h1>

      <div style={{
        backgroundColor: '#fff',
        padding: 20,
        margin: '20px 0',
        border: '1px solid #ddd',
        borderRadius: 5
      }}>
        <p style={{ fontWeight: 'bold' }}>{confirmationText}</p>
      </div>

      <p style={{ fontSize: 14, color: '#666', marginBottom: 20 }}>
        This site contains adult content intended for individuals 18 years of age or older.
        By proceeding, you confirm that you meet this requirement and that viewing adult
        content is legal in your jurisdiction.
      </p>

      <div style={{ display: 'flex', gap: 20, justifyContent: 'center' }}>
        <button
          onClick={handleDecline}
          style={{
            padding: '10px 30px',
            fontSize: 16,
            cursor: 'pointer',
            backgroundColor: '#ccc'
          }}
        >
          I am under 18 / Exit
        </button>

        <button
          onClick={handleConfirm}
          style={{
            padding: '10px 30px',
            fontSize: 16,
            cursor: 'pointer',
            backgroundColor: '#4CAF50',
            color: 'white',
            border: 'none'
          }}
        >
          I confirm I am 18+
        </button>
      </div>

      {error && <p style={{ color: 'red', marginTop: 15 }}>{error}</p>}

      <p style={{ marginTop: 30, fontSize: 12, color: '#999' }}>
        By proceeding, you agree to our{' '}
        <Link to="/terms">Terms of Service</Link> and{' '}
        <Link to="/privacy">Privacy Policy</Link>.
      </p>
    </div>
  )
}
