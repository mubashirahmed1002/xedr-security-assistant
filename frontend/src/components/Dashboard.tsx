import { useEffect, useState, useRef } from 'react'
import { fetchStats, fetchAlerts, fetchTimeline, createAlertSocket } from '../api'
import { LineChart, Line, XAxis, YAxis, Tooltip,
         ResponsiveContainer, CartesianGrid, Area, AreaChart } from 'recharts'

const SEV: Record<string, { dot: string; badge: string; glow: string }> = {
  Critical: { dot: '#a855f7', badge: 'rgba(168,85,247,0.15)', glow: 'rgba(168,85,247,0.4)' },
  High:     { dot: '#ef4444', badge: 'rgba(239,68,68,0.15)',  glow: 'rgba(239,68,68,0.4)'  },
  Medium:   { dot: '#f59e0b', badge: 'rgba(245,158,11,0.15)', glow: 'rgba(245,158,11,0.4)' },
  Low:      { dot: '#38bdf8', badge: 'rgba(56,189,248,0.15)', glow: 'rgba(56,189,248,0.4)' },
}

function StatCard({ label, value, colour, icon, delay }:
  { label: string; value: any; colour: string; icon: string; delay: number }) {
  const [displayed, setDisplayed] = useState(0)

  useEffect(() => {
    if (!value || isNaN(Number(value))) return
    const target = Number(value)
    const step   = Math.ceil(target / 30)
    let current  = 0
    const timer  = setInterval(() => {
      current = Math.min(current + step, target)
      setDisplayed(current)
      if (current >= target) clearInterval(timer)
    }, 40)
    return () => clearInterval(timer)
  }, [value])

  return (
    <div style={{
      background: 'linear-gradient(135deg, #0d1420 0%, #0f1923 100%)',
      border: '1px solid rgba(56,189,248,0.1)',
      borderRadius: '16px', padding: '20px',
      animation: `fadeIn 0.5s ease ${delay}ms both`,
      position: 'relative', overflow: 'hidden',
      transition: 'transform 0.2s, border-color 0.2s',
      cursor: 'default',
    }}
    onMouseEnter={e => {
      (e.currentTarget as HTMLElement).style.borderColor = colour + '40'
      ;(e.currentTarget as HTMLElement).style.transform = 'translateY(-2px)'
    }}
    onMouseLeave={e => {
      (e.currentTarget as HTMLElement).style.borderColor = 'rgba(56,189,248,0.1)'
      ;(e.currentTarget as HTMLElement).style.transform = 'translateY(0)'
    }}>
      {/* Background glow */}
      <div style={{
        position: 'absolute', top: '-20px', right: '-20px',
        width: '80px', height: '80px', borderRadius: '50%',
        background: colour, opacity: 0.06, filter: 'blur(20px)',
        pointerEvents: 'none',
      }}/>

      <div style={{ fontSize: '22px', marginBottom: '8px' }}>{icon}</div>
      <div style={{ fontSize: '28px', fontWeight: 700, color: colour, lineHeight: 1 }}>
        {value === null || value === undefined ? '—' : displayed}
      </div>
      <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px',
                    textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
        {label}
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#0d1420', border: '1px solid rgba(56,189,248,0.2)',
      borderRadius: '10px', padding: '10px 14px', fontSize: '12px',
    }}>
      <p style={{ color: '#94a3b8', marginBottom: '6px' }}>{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color, fontWeight: 600 }}>
          {p.dataKey}: {p.value}
        </p>
      ))}
    </div>
  )
}

export default function Dashboard({ onAlertClick }: { onAlertClick: (a: any) => void }) {
  const [stats,    setStats]    = useState<any>(null)
  const [alerts,   setAlerts]   = useState<any[]>([])
  const [timeline, setTimeline] = useState<any[]>([])
  const [live,     setLive]     = useState<any[]>([])
  const [newAlert, setNewAlert] = useState(false)

  useEffect(() => {
    fetchStats().then(setStats)
    fetchAlerts(30).then(setAlerts)
    fetchTimeline().then(setTimeline)

    const ws = createAlertSocket((data) => {
      setLive(prev => [data, ...prev].slice(0, 8))
      setNewAlert(true)
      setTimeout(() => setNewAlert(false), 2000)
      fetchStats().then(setStats)
    })
    return () => ws.close()
  }, [])

  return (
    <div style={{ padding: '28px', minHeight: '100vh' }}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'flex-start',
                    justifyContent: 'space-between', marginBottom: '28px',
                    animation: 'fadeIn 0.4s ease' }}>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#f1f5f9',
                       letterSpacing: '-0.3px' }}>
            Security Overview
          </h1>
          <p style={{ fontSize: '13px', color: '#475569', marginTop: '4px' }}>
            Real-time endpoint threat monitoring — XEDR v1.0
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px',
                      background: 'rgba(34,197,94,0.08)',
                      border: '1px solid rgba(34,197,94,0.2)',
                      borderRadius: '20px', padding: '6px 14px' }}>
          <div style={{ width: '7px', height: '7px', borderRadius: '50%',
                        background: '#22c55e', animation: 'pulse 2s infinite',
                        boxShadow: '0 0 8px rgba(34,197,94,0.6)' }}/>
          <span style={{ fontSize: '12px', color: '#22c55e', fontWeight: 600 }}>
            Monitoring Active
          </span>

          <button
          onClick={async () => {
            const r = await fetch('http://localhost:8000/api/report', { method: 'POST' })
            const blob = await r.blob()
            const url  = URL.createObjectURL(blob)
            const a    = document.createElement('a')
            a.href     = url
            a.download = 'XEDR_Report.pdf'
            a.click()
          }}
          style={{
            padding: '8px 18px', borderRadius: '20px', border: 'none',
            background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
            color: 'white', fontSize: '12px', fontWeight: 600,
            cursor: 'pointer', marginLeft: '12px',
            boxShadow: '0 0 12px rgba(14,165,233,0.3)',
            transition: 'opacity 0.2s',
          }}>
          📄 Export Report
        </button>
        </div>
      </div>

      {/* ── Stat cards ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: '14px', marginBottom: '24px' }}>
        <StatCard label="Total Alerts"  value={stats?.total_alerts}    colour="#38bdf8" icon="🛡️" delay={0}   />
        <StatCard label="Last 24 Hours" value={stats?.alerts_24h}      colour="#f59e0b" icon="⏱️" delay={80}  />
        <StatCard label="Critical"      value={stats?.critical_alerts} colour="#a855f7" icon="🔴" delay={160} />
        <StatCard label="High Severity" value={stats?.high_alerts}     colour="#ef4444" icon="⚠️" delay={240} />
      </div>

      {/* ── Timeline chart ── */}
      <div style={{
        background: 'linear-gradient(135deg, #0d1420 0%, #0f1923 100%)',
        border: '1px solid rgba(56,189,248,0.1)',
        borderRadius: '16px', padding: '20px', marginBottom: '24px',
        animation: 'fadeIn 0.5s ease 0.3s both',
      }}>
        <div style={{ display: 'flex', alignItems: 'center',
                      justifyContent: 'space-between', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8',
                       textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Threat Timeline — Last 24 Hours
          </h2>
          <div style={{ display: 'flex', gap: '16px' }}>
            {[['#ef4444','Total'],['#f97316','High'],['#a855f7','Critical']].map(([c,l]) => (
              <div key={l} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <div style={{ width: '20px', height: '2px', background: c, borderRadius: '1px' }}/>
                <span style={{ fontSize: '11px', color: '#64748b' }}>{l}</span>
              </div>
            ))}
          </div>
        </div>

        {timeline.length === 0 ? (
          <div style={{ height: '160px', display: 'flex', alignItems: 'center',
                        justifyContent: 'center', flexDirection: 'column', gap: '8px' }}>
            <div style={{ fontSize: '24px' }}>📊</div>
            <p style={{ fontSize: '13px', color: '#475569' }}>
              Data builds up as the monitor runs — check back soon
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={timeline}>
              <defs>
                <linearGradient id="gTotal" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(56,189,248,0.05)" />
              <XAxis dataKey="hour" stroke="#334155" tick={{ fontSize: 10, fill: '#475569' }} />
              <YAxis stroke="#334155" tick={{ fontSize: 10, fill: '#475569' }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="total"    stroke="#ef4444"
                    strokeWidth={2} fill="url(#gTotal)" dot={false} />
              <Line type="monotone" dataKey="high"     stroke="#f97316"
                    strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="critical" stroke="#a855f7"
                    strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ── Live feed + Alerts ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '14px' }}>

        {/* Live feed */}
        <div style={{
          background: 'linear-gradient(135deg, #0d1420 0%, #0f1923 100%)',
          border: `1px solid ${newAlert ? 'rgba(239,68,68,0.4)' : 'rgba(56,189,248,0.1)'}`,
          borderRadius: '16px', padding: '18px',
          transition: 'border-color 0.4s ease',
          animation: 'fadeIn 0.5s ease 0.4s both',
        }}>
          <div style={{ display: 'flex', alignItems: 'center',
                        gap: '8px', marginBottom: '14px' }}>
            <div style={{ width: '7px', height: '7px', borderRadius: '50%',
                          background: '#22c55e', animation: 'pulse 2s infinite' }}/>
            <h2 style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8',
                         textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Live Feed
            </h2>
          </div>

          {live.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <div style={{ fontSize: '28px', marginBottom: '8px' }}>👁️</div>
              <p style={{ fontSize: '12px', color: '#475569' }}>
                Watching for threats...
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {live.map((a, i) => {
                const s = SEV[a.severity] ?? SEV.Low
                return (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '10px 12px', borderRadius: '10px',
                    background: s.badge,
                    border: `1px solid ${s.dot}20`,
                    animation: i === 0 ? 'slideIn 0.3s ease' : 'none',
                  }}>
                    <div style={{ width: '7px', height: '7px', borderRadius: '50%',
                                  background: s.dot, flexShrink: 0,
                                  boxShadow: `0 0 6px ${s.glow}` }}/>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <p style={{ fontSize: '11px', color: '#e2e8f0', fontWeight: 600,
                                  overflow: 'hidden', textOverflow: 'ellipsis',
                                  whiteSpace: 'nowrap' }}>
                        {a.alert_type}
                      </p>
                      <p style={{ fontSize: '10px', color: '#64748b', marginTop: '1px' }}>
                        {a.process}
                      </p>
                    </div>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: s.dot,
                                   flexShrink: 0 }}>
                      {a.severity}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Recent alerts table */}
        <div style={{
          background: 'linear-gradient(135deg, #0d1420 0%, #0f1923 100%)',
          border: '1px solid rgba(56,189,248,0.1)',
          borderRadius: '16px', padding: '18px',
          animation: 'fadeIn 0.5s ease 0.5s both',
        }}>
          <h2 style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8',
                       textTransform: 'uppercase', letterSpacing: '0.08em',
                       marginBottom: '14px' }}>
            Recent Alerts
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px',
                        maxHeight: '320px', overflowY: 'auto' }}>
            {alerts.length === 0 ? (
              <p style={{ fontSize: '13px', color: '#475569', textAlign: 'center',
                          padding: '24px 0' }}>No alerts recorded yet</p>
            ) : alerts.map((a, i) => {
              const s = SEV[a.severity] ?? SEV.Low
              return (
                <div key={a.id}
                     onClick={() => onAlertClick(a)}
                     style={{
                       display: 'flex', alignItems: 'center', gap: '12px',
                       padding: '10px 12px', borderRadius: '10px',
                       background: 'rgba(15,25,35,0.6)',
                       border: '1px solid rgba(56,189,248,0.05)',
                       cursor: 'pointer', transition: 'all 0.15s ease',
                       animation: `fadeIn 0.4s ease ${i * 30}ms both`,
                     }}
                     onMouseEnter={e => {
                       (e.currentTarget as HTMLElement).style.background = s.badge
                       ;(e.currentTarget as HTMLElement).style.borderColor = s.dot + '30'
                       ;(e.currentTarget as HTMLElement).style.transform = 'translateX(3px)'
                     }}
                     onMouseLeave={e => {
                       (e.currentTarget as HTMLElement).style.background = 'rgba(15,25,35,0.6)'
                       ;(e.currentTarget as HTMLElement).style.borderColor = 'rgba(56,189,248,0.05)'
                       ;(e.currentTarget as HTMLElement).style.transform = 'translateX(0)'
                     }}>

                  {/* Risk bar */}
                  <div style={{ width: '3px', height: '36px', borderRadius: '2px',
                                background: s.dot, flexShrink: 0,
                                boxShadow: `0 0 6px ${s.glow}` }}/>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: '12px', color: '#e2e8f0', fontWeight: 600,
                                overflow: 'hidden', textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap' }}>
                      {a.alert_type}
                    </p>
                    <p style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                      {a.process} · {new Date(a.timestamp).toLocaleTimeString()}
                    </p>
                  </div>

                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: s.dot }}>
                      {a.severity}
                    </div>
                    <div style={{ fontSize: '10px', color: '#475569', marginTop: '2px' }}>
                      {a.risk_score}/100
                    </div>
                  </div>

                  <svg style={{ width: '14px', height: '14px', color: '#334155',
                                flexShrink: 0 }}
                       fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M9 5l7 7-7 7"/>
                  </svg>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
