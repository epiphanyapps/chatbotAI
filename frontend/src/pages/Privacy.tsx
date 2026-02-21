import { Link } from 'react-router-dom'

export default function Privacy() {
  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: 20 }}>
      <Link to="/" style={{ display: 'block', marginBottom: 20 }}>&larr; Back</Link>

      <h1>Privacy Policy</h1>
      <p><em>Last updated: {new Date().toISOString().split('T')[0]}</em></p>

      <h2>1. Information We Collect</h2>

      <h3>1.1 Information You Provide</h3>
      <ul>
        <li><strong>Email address:</strong> Used for authentication and account recovery</li>
        <li><strong>Age verification:</strong> Confirmation that you are 18+</li>
        <li><strong>Chat messages:</strong> Conversations with AI personalities</li>
        <li><strong>Payment information:</strong> Processed securely through Stripe</li>
      </ul>

      <h3>1.2 Information Collected Automatically</h3>
      <ul>
        <li><strong>Device fingerprint:</strong> Browser-based identifier to prevent trial abuse</li>
        <li><strong>IP address:</strong> Logged for security and age verification audit</li>
        <li><strong>User agent:</strong> Browser information for security logging</li>
      </ul>

      <h2>2. How We Use Your Information</h2>
      <ul>
        <li>Provide and maintain the Service</li>
        <li>Process payments and subscriptions</li>
        <li>Prevent fraud and trial abuse</li>
        <li>Comply with legal age verification requirements</li>
        <li>Improve the AI and user experience</li>
      </ul>

      <h2>3. Data Retention</h2>
      <ul>
        <li><strong>Account data:</strong> Retained while account is active</li>
        <li><strong>Chat history:</strong> Retained while account is active; deleted upon account deletion</li>
        <li><strong>Age verification audit:</strong> Retained for legal compliance (minimum 7 years)</li>
        <li><strong>Payment records:</strong> Retained as required by law</li>
      </ul>

      <h2>4. Data Sharing</h2>
      <p>We do NOT sell your personal information. We share data only with:</p>
      <ul>
        <li><strong>Stripe:</strong> For payment processing</li>
        <li><strong>Resend:</strong> For transactional emails</li>
        <li><strong>Law enforcement:</strong> When required by law</li>
      </ul>

      <h2>5. Your Rights (GDPR/CCPA)</h2>
      <p>You have the right to:</p>
      <ul>
        <li><strong>Access:</strong> Request a copy of your data</li>
        <li><strong>Rectification:</strong> Correct inaccurate data</li>
        <li><strong>Deletion:</strong> Request deletion of your account and data</li>
        <li><strong>Portability:</strong> Receive your data in a portable format</li>
        <li><strong>Opt-out:</strong> Cancel subscription at any time</li>
      </ul>
      <p>
        To exercise these rights, contact: privacy@intimateai.chat
      </p>

      <h2>6. Security</h2>
      <p>
        We implement industry-standard security measures including:
      </p>
      <ul>
        <li>HTTPS encryption for all communications</li>
        <li>Secure password hashing (not applicable - passwordless auth)</li>
        <li>JWT tokens with expiration</li>
        <li>HttpOnly cookies for session tokens</li>
      </ul>

      <h2>7. Cookies</h2>
      <p>
        We use essential cookies for authentication. We do not use tracking or
        advertising cookies. The device fingerprint is used solely for trial abuse
        prevention after you consent.
      </p>

      <h2>8. Age Verification</h2>
      <p>
        We collect age verification confirmations to comply with adult content laws.
        This includes logging the confirmation, timestamp, IP address, and device
        information. This data is retained for legal compliance purposes.
      </p>

      <h2>9. International Transfers</h2>
      <p>
        Your data may be processed in the United States. By using the Service, you
        consent to this transfer.
      </p>

      <h2>10. Children's Privacy</h2>
      <p>
        This Service is NOT intended for anyone under 18. We do not knowingly collect
        data from minors. If we discover such data, we will delete it immediately.
      </p>

      <h2>11. Changes to This Policy</h2>
      <p>
        We may update this Privacy Policy. We will notify you of material changes via
        email or in-app notification.
      </p>

      <h2>12. Contact Us</h2>
      <p>
        For privacy inquiries: privacy@intimateai.chat<br/>
        For general support: support@intimateai.chat
      </p>
    </div>
  )
}
