import { useState, useRef, useEffect } from 'react'
import { sendChat } from '../api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  time: string
}

const SUGGESTIONS = [
  '🔍 What alerts were detected today?',
  '🛡️ Is my system safe right now?',
  '🌐 What is a port scan attack?',
  '⚠️ Explain the latest High severity alert',
  '🔴 What should I do about a Critical alert?',
]

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    content: 'Hello! I am your XEDR AI security assistant, powered by Llama 3.3 70B. I have full context of your system\'s recent alerts and can explain threats, answer security questions, and guide you through any incident. What would you like to know?',
    time: new Date().toLocaleTimeString(),
  }])
  const [input,   setInput]   = useState('')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<any[]>([])
  const bottomRef             = useRef<HTMLDivElement>(null)
  const inputRef              = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(text?: string) {
    const msg = (text ?? input).trim()
    if (!msg || loading) return
    setInput('')

    const userMsg: Message = {
      role: 'user', content: msg,
      time: new Date().toLocaleTimeString(),
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const data = await sendChat(msg, history)
      setHistory(data.history)
      setMessages(prev => [...prev, {
        role: 'assistant', content: data.reply,
        time: new Date().toLocaleTimeString(),
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I could not reach the AI backend. Make sure api.py is running.',
        time: new Date().toLocaleTimeString(),
      }])
    }
    setLoading(false)
    inputRef.current?.focus()
  }

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100vh', padding: '28px',
    }}>

      {/* Header */}
      <div style={{ marginBottom: '20px', animation: 'fadeIn 0.4s ease' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px', height: '40px', borderRadius: '12px',
            background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '18px', boxShadow: '0 0 16px rgba(14,165,233,0.35)',
          }}>🤖</div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9' }}>
              XEDR Security Assistant
            </h1>
            <p style={{ fontSize: '12px', color: '#475569', marginTop: '2px' }}>
              Llama 3.3 70B · Context-aware · Real-time alerts
            </p>
          </div>
          <div style={{
            marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px',
            background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)',
            borderRadius: '20px', padding: '5px 12px',
          }}>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%',
                          background: '#22c55e', animation: 'pulse 2s infinite' }}/>
            <span style={{ fontSize: '11px', color: '#22c55e', fontWeight: 600 }}>Online</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column',
        gap: '14px', paddingRight: '4px', marginBottom: '16px',
      }}>
        {messages.map((m, i) => (
          <div key={i} style={{
            display: 'flex',
            justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
            animation: 'fadeIn 0.3s ease',
          }}>
            {/* Avatar for assistant */}
            {m.role === 'assistant' && (
              <div style={{
                width: '30px', height: '30px', borderRadius: '8px',
                background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '13px', flexShrink: 0, marginRight: '10px', marginTop: '2px',
              }}>🤖</div>
            )}

            <div style={{ maxWidth: '72%' }}>
              <div style={{
                padding: '12px 16px', borderRadius: '16px', fontSize: '13px',
                lineHeight: 1.7, position: 'relative',
                background: m.role === 'user'
                  ? 'linear-gradient(135deg, #0ea5e9, #6366f1)'
                  : 'rgba(13,20,32,0.9)',
                color: m.role === 'user' ? 'white' : '#cbd5e1',
                border: m.role === 'user'
                  ? 'none'
                  : '1px solid rgba(56,189,248,0.1)',
                borderBottomRightRadius: m.role === 'user' ? '4px' : '16px',
                borderBottomLeftRadius:  m.role === 'user' ? '16px' : '4px',
                boxShadow: m.role === 'user'
                  ? '0 4px 16px rgba(14,165,233,0.25)'
                  : '0 2px 8px rgba(0,0,0,0.3)',
              }}>
                {m.content}
              </div>
              <p style={{
                fontSize: '10px', color: '#334155', marginTop: '4px',
                textAlign: m.role === 'user' ? 'right' : 'left',
                paddingLeft: m.role === 'assistant' ? '4px' : 0,
                paddingRight: m.role === 'user' ? '4px' : 0,
              }}>
                {m.time}
              </p>
            </div>

            {/* Avatar for user */}
            {m.role === 'user' && (
              <div style={{
                width: '30px', height: '30px', borderRadius: '8px',
                background: 'rgba(56,189,248,0.15)',
                border: '1px solid rgba(56,189,248,0.2)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '13px', flexShrink: 0, marginLeft: '10px', marginTop: '2px',
              }}>👤</div>
            )}
          </div>
        ))}

        {/* Typing indicator */}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px',
                        animation: 'fadeIn 0.3s ease' }}>
            <div style={{
              width: '30px', height: '30px', borderRadius: '8px',
              background: 'linear-gradient(135deg, #0ea5e9, #6366f1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '13px',
            }}>🤖</div>
            <div style={{
              padding: '12px 16px', borderRadius: '16px', borderBottomLeftRadius: '4px',
              background: 'rgba(13,20,32,0.9)', border: '1px solid rgba(56,189,248,0.1)',
              display: 'flex', alignItems: 'center', gap: '4px',
            }}>
              {[0, 150, 300].map(delay => (
                <div key={delay} style={{
                  width: '7px', height: '7px', borderRadius: '50%',
                  background: '#38bdf8', animation: `pulse 1.2s ease ${delay}ms infinite`,
                }}/>
              ))}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggestion chips */}
      {messages.length === 1 && (
        <div style={{
          display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '14px',
          animation: 'fadeIn 0.5s ease 0.3s both',
        }}>
          {SUGGESTIONS.map(s => (
            <button key={s} onClick={() => handleSend(s)} style={{
              fontSize: '12px', padding: '7px 14px', borderRadius: '20px',
              background: 'rgba(14,165,233,0.07)',
              border: '1px solid rgba(56,189,248,0.15)',
              color: '#94a3b8', cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(14,165,233,0.15)'
              ;(e.currentTarget as HTMLElement).style.color = '#38bdf8'
              ;(e.currentTarget as HTMLElement).style.borderColor = 'rgba(56,189,248,0.35)'
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(14,165,233,0.07)'
              ;(e.currentTarget as HTMLElement).style.color = '#94a3b8'
              ;(e.currentTarget as HTMLElement).style.borderColor = 'rgba(56,189,248,0.15)'
            }}>
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input bar */}
      <div style={{
        display: 'flex', gap: '10px', alignItems: 'center',
        background: 'rgba(13,20,32,0.9)',
        border: '1px solid rgba(56,189,248,0.15)',
        borderRadius: '16px', padding: '8px 8px 8px 16px',
        animation: 'fadeIn 0.5s ease 0.2s both',
        transition: 'border-color 0.2s',
      }}
      onFocusCapture={e => (e.currentTarget as HTMLElement).style.borderColor = 'rgba(14,165,233,0.4)'}
      onBlurCapture={e  => (e.currentTarget as HTMLElement).style.borderColor = 'rgba(56,189,248,0.15)'}>

        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Ask anything about your system's security..."
          style={{
            flex: 1, background: 'none', border: 'none', outline: 'none',
            fontSize: '13px', color: '#e2e8f0',
          }}
        />

        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          style={{
            width: '38px', height: '38px', borderRadius: '10px', border: 'none',
            cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
            background: loading || !input.trim()
              ? 'rgba(56,189,248,0.08)'
              : 'linear-gradient(135deg, #0ea5e9, #6366f1)',
            color: loading || !input.trim() ? '#334155' : 'white',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s ease', flexShrink: 0,
            boxShadow: !loading && input.trim()
              ? '0 0 12px rgba(14,165,233,0.35)' : 'none',
          }}>
          <svg style={{ width: '16px', height: '16px' }} fill="none"
               stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
          </svg>
        </button>
      </div>
    </div>
  )
}
