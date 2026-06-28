import { useState } from 'react'
import { explainAlert } from '../api'

const SEV: Record<string, { colour: string; bg: string; border: string }> = {
  Critical: { colour: '#a855f7', bg: 'rgba(168,85,247,0.1)',  border: 'rgba(168,85,247,0.25)' },
  High:     { colour: '#ef4444', bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.25)'  },
  Medium:   { colour: '#f59e0b', bg: 'rgba(245,158,11,0.1)',  border: 'rgba(245,158,11,0.25)' },
  Low:      { colour: '#38bdf8', bg: 'rgba(56,189,248,0.1)',  border: 'rgba(56,189,248,0.25)' },
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div style={{
      background: 'rgba(15,25,35,0.7)', borderRadius: '10px', padding: '12px 14px',
      border: '1px solid rgba(56,189,248,0.07)',
    }}>
      <p style={{ fontSize: '10px', color: '#475569', textTransform: 'uppercase',
                  letterSpacing: '0.08em', fontWeight: 600, marginBottom: '6px' }}>
        {label}
      </p>
      <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.6,
                  wordBreak: 'break-all' }}>
        {value || '—'}
      </p>
    </div>
  )
}

export default function AlertDetail({
  alert, onBack,
}: { alert: any; onBack: () => void }) {
  const [explanation, setExplanation] = useState(alert?.explained || '')
  const [loading,     setLoading]     = useState(false)

  async function handleExplain() {
    if (!alert) return
    setLoading(true)
    const data = await explainAlert(alert.id)
    setExplanation(data.explanation)
    setLoading(false)
  }

  if (!alert) return (
    <div style={{ padding: '28px' }}>
      <h1 style={{ fontSize: '22px', fontWeight: 700, color: '#f1f5f9', marginBottom: '8px' }}>
        Alert Detail
      </h1>
      <p style={{ fontSize: '14px', color: '#475569' }}>
        Click any alert from the dashboard to inspect it here.
      </p>
    </div>
  )

  const s = SEV[alert.severity] ?? SEV.Low

  return (
    <div style={{ padding: '28px', maxWidth: '760px', animation: 'fadeIn 0.4s ease' }}>

      {/* Back button */}
      <button onClick={onBack} style={{
        display: 'flex', alignItems: 'center', gap: '6px',
        background: 'none', border: 'none', cursor: 'pointer',
        color: '#475569', fontSize: '13px', marginBottom: '20px',
        padding: '6px 10px', borderRadius: '8px',
        transition: 'color 0.15s, background 0.15s',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLElement).style.color = '#38bdf8'
        ;(e.currentTarget as HTMLElement).style.background = 'rgba(56,189,248,0.08)'
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.color = '#475569'
        ;(e.currentTarget as HTMLElement).style.background = 'none'
      }}>
        <svg style={{ width: '14px', height: '14px' }} fill="none"
             stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7"/>
        </svg>
        Back to Dashboard
      </button>

      <div style={{
        background: 'linear-gradient(135deg, #0d1420 0%, #0f1923 100%)',
        border: `1px solid ${s.border}`,
        borderRadius: '20px', padding: '24px',
        boxShadow: `0 0 40px ${s.colour}10`,
        display: 'flex', flexDirection: 'column', gap: '16px',
      }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start',
                      justifyContent: 'space-between', gap: '12px' }}>
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9' }}>
              {alert.alert_type}
            </h2>
            <p style={{ fontSize: '12px', color: '#475569', marginTop: '4px' }}>
              Detected at {new Date(alert.timestamp).toLocaleString()} · Alert #{alert.id}
            </p>
          </div>
          <div style={{
            padding: '6px 14px', borderRadius: '20px', fontSize: '12px',
            fontWeight: 700, color: s.colour, background: s.bg, border: `1px solid ${s.border}`,
            whiteSpace: 'nowrap', flexShrink: 0,
          }}>
            {alert.severity}
          </div>
        </div>

        {/* Risk score bar */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between',
                        fontSize: '12px', marginBottom: '8px' }}>
            <span style={{ color: '#64748b', fontWeight: 600,
                           textTransform: 'uppercase', letterSpacing: '0.06em',
                           fontSize: '10px' }}>
              Risk Score
            </span>
            <span style={{ color: s.colour, fontWeight: 700 }}>
              {alert.risk_score} / 100
            </span>
          </div>
          <div style={{ height: '6px', borderRadius: '3px',
                        background: 'rgba(56,189,248,0.08)', overflow: 'hidden' }}>
            <div style={{
              height: '100%', borderRadius: '3px',
              background: `linear-gradient(90deg, ${s.colour}80, ${s.colour})`,
              width: `${alert.risk_score}%`,
              boxShadow: `0 0 8px ${s.colour}60`,
              transition: 'width 1s ease',
            }}/>
          </div>
        </div>

        {/* Info grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
          <InfoBlock label="Process"    value={alert.process} />
          <InfoBlock label="Alert Type" value={alert.alert_type} />
        </div>

        <InfoBlock label="Description" value={alert.description} />

        {/* Evidence */}
        <div style={{
          background: 'rgba(15,25,35,0.7)', borderRadius: '10px', padding: '12px 14px',
          border: '1px solid rgba(56,189,248,0.07)',
        }}>
          <p style={{ fontSize: '10px', color: '#475569', textTransform: 'uppercase',
                      letterSpacing: '0.08em', fontWeight: 600, marginBottom: '8px' }}>
            Raw Evidence
          </p>
          <pre style={{
            fontSize: '11px', color: '#64748b', lineHeight: 1.7,
            overflow: 'auto', fontFamily: 'monospace', whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}>
            {alert.evidence}
          </pre>
        </div>

        {/* AI Explanation */}
        <div style={{
          background: explanation
            ? 'linear-gradient(135deg, rgba(14,165,233,0.05), rgba(99,102,241,0.05))'
            : 'rgba(15,25,35,0.7)',
          borderRadius: '12px', padding: '16px',
          border: explanation
            ? '1px solid rgba(14,165,233,0.2)'
            : '1px solid rgba(56,189,248,0.07)',
          transition: 'all 0.3s ease',
        }}>
          <div style={{ display: 'flex', alignItems: 'center',
                        justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '16px' }}>🤖</span>
              <p style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8',
                          textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                AI Analysis
              </p>
            </div>
            <button onClick={handleExplain} disabled={loading} style={{
              padding: '7px 16px', borderRadius: '20px', border: 'none',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '12px', fontWeight: 600,
              background: loading
                ? 'rgba(56,189,248,0.1)'
                : 'linear-gradient(135deg, #0ea5e9, #6366f1)',
              color: loading ? '#475569' : 'white',
              transition: 'all 0.2s ease',
              opacity: loading ? 0.6 : 1,
            }}>
              {loading ? '⚡ Analysing...' : explanation ? '🔄 Re-analyse' : '✨ Explain with AI'}
            </button>
          </div>

          {explanation ? (
            <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.75 }}>
              {explanation}
            </p>
          ) : (
            <p style={{ fontSize: '13px', color: '#475569', fontStyle: 'italic' }}>
              Click "Explain with AI" to get a plain-English breakdown of this alert —
              what happened, why it's suspicious, and what to do.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
