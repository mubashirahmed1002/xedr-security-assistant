import { useState } from 'react'
import Dashboard from './components/Dashboard'
import ChatPanel from './components/ChatPanel'
import AlertDetail from './components/AlertDetail'

export type Page = 'dashboard' | 'chat' | 'alerts'

const NAV = [
  {
    id: 'dashboard', label: 'Dashboard',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    id: 'alerts', label: 'Alerts',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    ),
  },
  {
    id: 'chat', label: 'AI Chat',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
      </svg>
    ),
  },
]

export default function App() {
  const [page, setPage]           = useState<Page>('dashboard')
  const [selectedAlert, setAlert] = useState<any>(null)
  const [hovered, setHovered]     = useState<string | null>(null)

  return (
    <div className="min-h-screen flex" style={{ background: '#080c14', color: '#e2e8f0' }}>

      {/* ── Sidebar ── */}
      <aside style={{
        width: '72px',
        background: 'linear-gradient(180deg, #0d1420 0%, #0a1018 100%)',
        borderRight: '1px solid rgba(56,189,248,0.08)',
        position: 'fixed', height: '100vh', zIndex: 50,
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        padding: '20px 0', gap: '8px',
      }}>

        {/* Logo */}
        <div style={{
          width: '40px', height: '40px', borderRadius: '12px', marginBottom: '20px',
          background: 'linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 20px rgba(14,165,233,0.4)',
          fontWeight: 800, fontSize: '14px', color: 'white', letterSpacing: '-1px',
        }}>XE</div>

        {NAV.map(n => {
          const active = page === n.id
          const hover  = hovered === n.id
          return (
            <div key={n.id} style={{ position: 'relative', width: '100%',
                                     display: 'flex', justifyContent: 'center' }}>
              <button
                onClick={() => { setPage(n.id as Page); if (n.id !== 'alerts') setAlert(null) }}
                onMouseEnter={() => setHovered(n.id)}
                onMouseLeave={() => setHovered(null)}
                title={n.label}
                style={{
                  width: '44px', height: '44px', borderRadius: '12px', border: 'none',
                  cursor: 'pointer', transition: 'all 0.2s ease',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: active
                    ? 'linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)'
                    : hover ? 'rgba(14,165,233,0.12)' : 'transparent',
                  color: active ? 'white' : hover ? '#38bdf8' : '#64748b',
                  boxShadow: active ? '0 0 16px rgba(14,165,233,0.35)' : 'none',
                  transform: hover && !active ? 'scale(1.08)' : 'scale(1)',
                }}>
                {n.icon}
              </button>

              {/* Active indicator */}
              {active && (
                <div style={{
                  position: 'absolute', right: 0, top: '50%',
                  transform: 'translateY(-50%)',
                  width: '3px', height: '24px', borderRadius: '2px 0 0 2px',
                  background: 'linear-gradient(180deg, #0ea5e9, #6366f1)',
                }}/>
              )}

              {/* Tooltip */}
              {hover && (
                <div style={{
                  position: 'absolute', left: '60px', top: '50%',
                  transform: 'translateY(-50%)',
                  background: '#1e293b', color: '#e2e8f0',
                  padding: '6px 10px', borderRadius: '8px', fontSize: '12px',
                  fontWeight: 500, whiteSpace: 'nowrap', pointerEvents: 'none',
                  border: '1px solid rgba(56,189,248,0.15)',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
                  zIndex: 100,
                }}>{n.label}</div>
              )}
            </div>
          )
        })}

        {/* Bottom status dot */}
        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column',
                      alignItems: 'center', gap: '4px' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%',
                        background: '#22c55e',
                        boxShadow: '0 0 8px rgba(34,197,94,0.6)',
                        animation: 'pulse 2s infinite' }}/>
          <span style={{ fontSize: '9px', color: '#22c55e', fontWeight: 600,
                         letterSpacing: '0.05em' }}>LIVE</span>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main style={{ marginLeft: '72px', flex: 1, overflow: 'auto', minHeight: '100vh' }}>
        {page === 'dashboard' && (
          <Dashboard onAlertClick={(a) => { setAlert(a); setPage('alerts') }} />
        )}
        {page === 'alerts' && (
          <AlertDetail alert={selectedAlert} onBack={() => setAlert(null)} />
        )}
        {page === 'chat' && <ChatPanel />}
      </main>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(0.85); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideIn {
          from { opacity: 0; transform: translateX(-8px); }
          to   { opacity: 1; transform: translateX(0); }
        }
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 8px rgba(14,165,233,0.3); }
          50%       { box-shadow: 0 0 20px rgba(14,165,233,0.6); }
        }
        @keyframes scan {
          0%   { transform: translateY(0); opacity: 0.6; }
          100% { transform: translateY(100%); opacity: 0; }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(56,189,248,0.2); border-radius: 4px; }
      `}</style>
    </div>
  )
}
