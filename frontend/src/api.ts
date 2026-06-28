const BASE = 'http://localhost:8000'

export async function fetchStats() {
  const r = await fetch(`${BASE}/api/stats`)
  return r.json()
}

export async function fetchAlerts(limit = 50) {
  const r = await fetch(`${BASE}/api/alerts?limit=${limit}`)
  return r.json()
}

export async function fetchTimeline() {
  const r = await fetch(`${BASE}/api/timeline`)
  return r.json()
}

export async function fetchProcesses() {
  const r = await fetch(`${BASE}/api/processes`)
  return r.json()
}

export async function explainAlert(id: number) {
  const r = await fetch(`${BASE}/api/alerts/${id}/explain`)
  return r.json()
}

export async function sendChat(message: string, history: any[]) {
  const r = await fetch(`${BASE}/api/chat`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ message, history }),
  })
  return r.json()
}

export function createAlertSocket(onMessage: (data: any) => void) {
  const ws = new WebSocket('ws://localhost:8000/ws/alerts')
  ws.onmessage = (e) => onMessage(JSON.parse(e.data))
  ws.onerror   = (e) => console.error('[WS] Error:', e)
  return ws
}