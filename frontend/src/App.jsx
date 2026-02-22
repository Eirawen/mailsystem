import { useMemo, useState } from 'react'
import { getAnalytics, getEmail, postBulk, postSend } from './api'

const tabs = ['send', 'bulk', 'lookup', 'analytics']

function pretty(value) {
  return JSON.stringify(value, null, 2)
}

export default function App() {
  const [activeTab, setActiveTab] = useState('send')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const [sendForm, setSendForm] = useState({
    tenant_id: 'tenant-1',
    recipient_email: 'alice@example.com',
    recipient_name: 'Alice',
    template_id: 'tpl-1',
    variables: '{"name":"Alice"}',
    metadata: '{"source":"dashboard"}',
    provider_hint: 'mock',
    idempotency_key: `send-${Date.now()}`,
    send_at: ''
  })

  const [bulkForm, setBulkForm] = useState({
    tenant_id: 'tenant-1',
    template_id: 'tpl-1',
    recipients: 'a@example.com,b@example.com',
    shared_variables: '{"name":"friend"}',
    per_recipient_variables: '{}',
    metadata: '{"source":"dashboard"}',
    provider_hint: 'mock',
    batch_size: 100,
    idempotency_key: `bulk-${Date.now()}`,
    send_at: ''
  })

  const [lookupForm, setLookupForm] = useState({
    tenant_id: 'tenant-1',
    email_id: ''
  })

  const [analyticsForm, setAnalyticsForm] = useState({
    tenant_id: 'tenant-1',
    from: '',
    to: '',
    group_by: 'day',
    template_id: ''
  })

  const activeTitle = useMemo(() => {
    if (activeTab === 'send') return 'Transactional Send'
    if (activeTab === 'bulk') return 'Bulk Send'
    if (activeTab === 'lookup') return 'Lookup Email Status'
    return 'Analytics'
  }, [activeTab])

  function resetFeedback() {
    setError('')
    setResult(null)
  }

  function safeJson(text, fieldName) {
    try {
      return text ? JSON.parse(text) : {}
    } catch {
      throw new Error(`${fieldName} must be valid JSON`)
    }
  }

  async function run(action) {
    setLoading(true)
    resetFeedback()
    try {
      const data = await action()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  async function onSendSubmit(e) {
    e.preventDefault()
    await run(async () => {
      const payload = {
        tenant_id: sendForm.tenant_id,
        recipient: {
          email: sendForm.recipient_email,
          name: sendForm.recipient_name || null
        },
        template_id: sendForm.template_id,
        variables: safeJson(sendForm.variables, 'variables'),
        metadata: safeJson(sendForm.metadata, 'metadata'),
        provider_hint: sendForm.provider_hint || null,
        idempotency_key: sendForm.idempotency_key,
        send_at: sendForm.send_at || null
      }
      return postSend(payload)
    })
  }

  async function onBulkSubmit(e) {
    e.preventDefault()
    await run(async () => {
      const recipients = bulkForm.recipients
        .split(',')
        .map((email) => email.trim())
        .filter(Boolean)
        .map((email) => ({ email }))

      if (!recipients.length) {
        throw new Error('Add at least one recipient email')
      }

      const payload = {
        tenant_id: bulkForm.tenant_id,
        template_id: bulkForm.template_id,
        recipients,
        shared_variables: safeJson(bulkForm.shared_variables, 'shared_variables'),
        per_recipient_variables: safeJson(bulkForm.per_recipient_variables, 'per_recipient_variables'),
        metadata: safeJson(bulkForm.metadata, 'metadata'),
        batch_size: Number(bulkForm.batch_size),
        provider_hint: bulkForm.provider_hint || null,
        idempotency_key: bulkForm.idempotency_key,
        send_at: bulkForm.send_at || null
      }
      return postBulk(payload)
    })
  }

  async function onLookupSubmit(e) {
    e.preventDefault()
    await run(async () => getEmail(lookupForm.email_id, lookupForm.tenant_id))
  }

  async function onAnalyticsSubmit(e) {
    e.preventDefault()
    await run(async () =>
      getAnalytics({
        tenantId: analyticsForm.tenant_id,
        from: analyticsForm.from || null,
        to: analyticsForm.to || null,
        groupBy: analyticsForm.group_by,
        templateId: analyticsForm.template_id || null
      })
    )
  }

  return (
    <div className="app-shell">
      <div className="aurora" />
      <header className="topbar">
        <h1>Mail System Console</h1>
        <p>React dashboard for sending, tracking, and analyzing email traffic.</p>
      </header>

      <nav className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={activeTab === tab ? 'tab active' : 'tab'}
            onClick={() => {
              setActiveTab(tab)
              resetFeedback()
            }}
            type="button"
          >
            {tab}
          </button>
        ))}
      </nav>

      <main className="panel">
        <h2>{activeTitle}</h2>

        {activeTab === 'send' && (
          <form className="form-grid" onSubmit={onSendSubmit}>
            <label>Tenant ID<input value={sendForm.tenant_id} onChange={(e) => setSendForm({ ...sendForm, tenant_id: e.target.value })} /></label>
            <label>Recipient Email<input value={sendForm.recipient_email} onChange={(e) => setSendForm({ ...sendForm, recipient_email: e.target.value })} /></label>
            <label>Recipient Name<input value={sendForm.recipient_name} onChange={(e) => setSendForm({ ...sendForm, recipient_name: e.target.value })} /></label>
            <label>Template ID<input value={sendForm.template_id} onChange={(e) => setSendForm({ ...sendForm, template_id: e.target.value })} /></label>
            <label>Provider Hint<input value={sendForm.provider_hint} onChange={(e) => setSendForm({ ...sendForm, provider_hint: e.target.value })} /></label>
            <label>Idempotency Key<input value={sendForm.idempotency_key} onChange={(e) => setSendForm({ ...sendForm, idempotency_key: e.target.value })} /></label>
            <label>Send At (ISO datetime)<input value={sendForm.send_at} onChange={(e) => setSendForm({ ...sendForm, send_at: e.target.value })} placeholder="2026-02-22T17:00:00Z" /></label>
            <label className="full">Variables JSON<textarea rows="5" value={sendForm.variables} onChange={(e) => setSendForm({ ...sendForm, variables: e.target.value })} /></label>
            <label className="full">Metadata JSON<textarea rows="4" value={sendForm.metadata} onChange={(e) => setSendForm({ ...sendForm, metadata: e.target.value })} /></label>
            <button className="cta" disabled={loading} type="submit">{loading ? 'Sending...' : 'Send Email'}</button>
          </form>
        )}

        {activeTab === 'bulk' && (
          <form className="form-grid" onSubmit={onBulkSubmit}>
            <label>Tenant ID<input value={bulkForm.tenant_id} onChange={(e) => setBulkForm({ ...bulkForm, tenant_id: e.target.value })} /></label>
            <label>Template ID<input value={bulkForm.template_id} onChange={(e) => setBulkForm({ ...bulkForm, template_id: e.target.value })} /></label>
            <label>Provider Hint<input value={bulkForm.provider_hint} onChange={(e) => setBulkForm({ ...bulkForm, provider_hint: e.target.value })} /></label>
            <label>Batch Size<input type="number" value={bulkForm.batch_size} onChange={(e) => setBulkForm({ ...bulkForm, batch_size: e.target.value })} /></label>
            <label>Idempotency Key<input value={bulkForm.idempotency_key} onChange={(e) => setBulkForm({ ...bulkForm, idempotency_key: e.target.value })} /></label>
            <label>Send At (ISO datetime)<input value={bulkForm.send_at} onChange={(e) => setBulkForm({ ...bulkForm, send_at: e.target.value })} placeholder="2026-02-22T18:00:00Z" /></label>
            <label className="full">Recipients (comma-separated emails)<textarea rows="3" value={bulkForm.recipients} onChange={(e) => setBulkForm({ ...bulkForm, recipients: e.target.value })} /></label>
            <label className="full">Shared Variables JSON<textarea rows="4" value={bulkForm.shared_variables} onChange={(e) => setBulkForm({ ...bulkForm, shared_variables: e.target.value })} /></label>
            <label className="full">Per Recipient Variables JSON<textarea rows="4" value={bulkForm.per_recipient_variables} onChange={(e) => setBulkForm({ ...bulkForm, per_recipient_variables: e.target.value })} /></label>
            <label className="full">Metadata JSON<textarea rows="4" value={bulkForm.metadata} onChange={(e) => setBulkForm({ ...bulkForm, metadata: e.target.value })} /></label>
            <button className="cta" disabled={loading} type="submit">{loading ? 'Queueing...' : 'Queue Bulk Send'}</button>
          </form>
        )}

        {activeTab === 'lookup' && (
          <form className="form-grid" onSubmit={onLookupSubmit}>
            <label>Tenant ID<input value={lookupForm.tenant_id} onChange={(e) => setLookupForm({ ...lookupForm, tenant_id: e.target.value })} /></label>
            <label>Email ID<input value={lookupForm.email_id} onChange={(e) => setLookupForm({ ...lookupForm, email_id: e.target.value })} /></label>
            <button className="cta" disabled={loading} type="submit">{loading ? 'Loading...' : 'Lookup Email'}</button>
          </form>
        )}

        {activeTab === 'analytics' && (
          <form className="form-grid" onSubmit={onAnalyticsSubmit}>
            <label>Tenant ID<input value={analyticsForm.tenant_id} onChange={(e) => setAnalyticsForm({ ...analyticsForm, tenant_id: e.target.value })} /></label>
            <label>From (ISO datetime)<input value={analyticsForm.from} onChange={(e) => setAnalyticsForm({ ...analyticsForm, from: e.target.value })} /></label>
            <label>To (ISO datetime)<input value={analyticsForm.to} onChange={(e) => setAnalyticsForm({ ...analyticsForm, to: e.target.value })} /></label>
            <label>Group By
              <select value={analyticsForm.group_by} onChange={(e) => setAnalyticsForm({ ...analyticsForm, group_by: e.target.value })}>
                <option value="day">day</option>
                <option value="hour">hour</option>
              </select>
            </label>
            <label>Template ID (optional)<input value={analyticsForm.template_id} onChange={(e) => setAnalyticsForm({ ...analyticsForm, template_id: e.target.value })} /></label>
            <button className="cta" disabled={loading} type="submit">{loading ? 'Loading...' : 'Fetch Analytics'}</button>
          </form>
        )}

        {error && <div className="error">{error}</div>}
        {result && (
          <section className="result">
            <h3>Response</h3>
            <pre>{pretty(result)}</pre>
          </section>
        )}
      </main>
    </div>
  )
}
