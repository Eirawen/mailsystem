const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function parseResponse(response) {
  const text = await response.text()
  let body = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = text
  }

  if (!response.ok) {
    const detail = body?.detail || body || `HTTP ${response.status}`
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  return body
}

export async function postSend(payload) {
  const response = await fetch(`${API_BASE}/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  return parseResponse(response)
}

export async function postBulk(payload) {
  const response = await fetch(`${API_BASE}/send/bulk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  return parseResponse(response)
}

export async function getEmail(emailId, tenantId) {
  const query = new URLSearchParams({ tenant_id: tenantId })
  const response = await fetch(`${API_BASE}/emails/${encodeURIComponent(emailId)}?${query}`)
  return parseResponse(response)
}

export async function getAnalytics({ tenantId, from, to, groupBy, templateId }) {
  const query = new URLSearchParams({
    tenant_id: tenantId,
    group_by: groupBy
  })
  if (from) query.set('from', from)
  if (to) query.set('to', to)
  if (templateId) query.set('template_id', templateId)

  const response = await fetch(`${API_BASE}/analytics?${query.toString()}`)
  return parseResponse(response)
}
