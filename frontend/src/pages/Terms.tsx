import { Link } from 'react-router-dom'

export default function Terms() {
  return (
    <div style={{ maxWidth: 800, margin: '40px auto', padding: 20 }}>
      <Link to="/" style={{ display: 'block', marginBottom: 20 }}>&larr; Back</Link>

      <h1>Terms of Service</h1>
      <p><em>Last updated: {new Date().toISOString().split('T')[0]}</em></p>

      <h2>1. Acceptance of Terms</h2>
      <p>
        By accessing or using IntimateAI ("Service"), you agree to be bound by these
        Terms of Service. If you do not agree, do not use the Service.
      </p>

      <h2>2. Age Requirement</h2>
      <p>
        <strong>You must be at least 18 years old to use this Service.</strong> By using
        IntimateAI, you represent and warrant that you are at least 18 years of age and
        that viewing adult content is legal in your jurisdiction.
      </p>

      <h2>3. Adult Content</h2>
      <p>
        IntimateAI contains sexually explicit material intended for adults only. The
        Service provides AI-generated conversations that may include explicit sexual
        content. You acknowledge that:
      </p>
      <ul>
        <li>All content is AI-generated and fictional</li>
        <li>AI personalities are not real people</li>
        <li>You access this content voluntarily</li>
        <li>You will not share content with minors</li>
      </ul>

      <h2>4. Prohibited Uses</h2>
      <p>You agree NOT to:</p>
      <ul>
        <li>Use the Service if you are under 18 years old</li>
        <li>Share account access with anyone</li>
        <li>Attempt to bypass age verification</li>
        <li>Use the Service for any illegal purpose</li>
        <li>Redistribute or publicly share generated content</li>
        <li>Attempt to extract or reverse-engineer the AI system</li>
      </ul>

      <h2>5. Subscriptions and Payments</h2>
      <p>
        IntimateAI offers a subscription service at $29.99/month. New users receive a
        2-hour free trial. Subscriptions automatically renew unless cancelled. You may
        cancel at any time through your account settings.
      </p>

      <h2>6. Free Trial</h2>
      <p>
        Each user is entitled to one 2-hour free trial. Attempting to obtain multiple
        trials (e.g., using different email addresses or devices) is prohibited and may
        result in account termination.
      </p>

      <h2>7. Content and AI Disclaimers</h2>
      <p>
        The AI generates content based on patterns and is not a real person. We do not
        guarantee that content will meet your expectations. AI responses may sometimes
        be unexpected or nonsensical.
      </p>

      <h2>8. Privacy</h2>
      <p>
        Your use of the Service is also governed by our <Link to="/privacy">Privacy Policy</Link>.
      </p>

      <h2>9. Termination</h2>
      <p>
        We may terminate or suspend your account at any time for violations of these
        Terms. Upon termination, your right to use the Service ceases immediately.
      </p>

      <h2>10. Limitation of Liability</h2>
      <p>
        IntimateAI is provided "as is" without warranties. We are not liable for any
        damages arising from your use of the Service.
      </p>

      <h2>11. Changes to Terms</h2>
      <p>
        We may modify these Terms at any time. Continued use after changes constitutes
        acceptance of the new Terms.
      </p>

      <h2>12. Contact</h2>
      <p>
        For questions about these Terms, contact: support@intimateai.chat
      </p>
    </div>
  )
}
