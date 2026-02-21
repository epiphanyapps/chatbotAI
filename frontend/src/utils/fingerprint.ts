import { useEffect, useState } from 'react'
import FingerprintJS from '@fingerprintjs/fingerprintjs'

export function useFingerprint() {
  const [visitorId, setVisitorId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadFingerprint = async () => {
      try {
        const fp = await FingerprintJS.load()
        const result = await fp.get()
        setVisitorId(result.visitorId)
      } catch (error) {
        console.error('Fingerprint error:', error)
        // Fallback: generate random ID (less accurate but functional)
        setVisitorId(crypto.randomUUID())
      } finally {
        setLoading(false)
      }
    }
    loadFingerprint()
  }, [])

  return { visitorId, loading }
}
