import { useEffect, useRef, useState, useCallback } from 'react'
import { apiWithAuth } from '../utils/api'
import { useAuth } from '../context/AuthContext'
import { ChatSocket, splitBubbles, ChatEvent } from '../utils/chat'

interface ChatMessage {
  role: 'user' | 'assistant'
  bubbles: string[]
}

export default function Chat() {
  const { logout } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState('') // live assistant buffer
  const [typing, setTyping] = useState(false)
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)

  const socketRef = useRef<ChatSocket | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const streamRef = useRef('')

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  // Load transcript on mount so reconnects show full history.
  useEffect(() => {
    apiWithAuth('/chat/history')
      .then((data) => {
        const loaded: ChatMessage[] = (data.messages ?? []).map((m: any) => ({
          role: m.role,
          bubbles: m.bubbles ?? [m.content],
        }))
        setMessages(loaded)
      })
      .catch(() => {})
  }, [])

  // Open the WebSocket once.
  useEffect(() => {
    const handleEvent = (e: ChatEvent) => {
      if (e.type === 'ready') {
        setConnected(true)
      } else if (e.type === 'typing') {
        setTyping(true)
      } else if (e.type === 'token') {
        setTyping(false)
        streamRef.current += e.delta
        setStreaming(streamRef.current)
      } else if (e.type === 'done') {
        const finalText = streamRef.current
        streamRef.current = ''
        setStreaming('')
        setTyping(false)
        if (finalText.trim()) {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', bubbles: splitBubbles(finalText) },
          ])
        }
      }
    }

    const socket = new ChatSocket({
      onEvent: handleEvent,
      onClose: () => setConnected(false),
    })
    socket.connect()
    socketRef.current = socket
    return () => socket.close()
  }, [])

  useEffect(scrollToBottom, [messages, streaming, typing, scrollToBottom])

  const send = () => {
    const text = input.trim()
    if (!text || !connected) return
    setMessages((prev) => [...prev, { role: 'user', bubbles: [text] }])
    socketRef.current?.send(text)
    setInput('')
    setTyping(true)
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div style={styles.shell}>
      <header style={styles.header}>
        <div style={styles.headerName}>
          <span style={styles.avatar}>S</span>
          <div>
            <div style={{ fontWeight: 600 }}>Sophia</div>
            <div style={styles.status}>{connected ? 'online' : 'connecting…'}</div>
          </div>
        </div>
        <button onClick={logout} style={styles.logout}>Log out</button>
      </header>

      <div style={styles.thread}>
        {messages.length === 0 && (
          <div style={styles.empty}>Say hi to Sophia…</div>
        )}
        {messages.map((m, i) => (
          <MessageRow key={i} role={m.role} bubbles={m.bubbles} />
        ))}
        {streaming && (
          <MessageRow role="assistant" bubbles={splitBubbles(streaming)} />
        )}
        {typing && <TypingBubble />}
        <div ref={bottomRef} />
      </div>

      <div style={styles.composer}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Message Sophia…"
          rows={1}
          style={styles.input}
        />
        <button onClick={send} disabled={!connected || !input.trim()} style={styles.send}>
          Send
        </button>
      </div>
    </div>
  )
}

function MessageRow({ role, bubbles }: { role: 'user' | 'assistant'; bubbles: string[] }) {
  const isUser = role === 'user'
  return (
    <div style={{ ...styles.row, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <div style={styles.bubbleGroup}>
        {bubbles.map((b, i) => (
          <div key={i} style={isUser ? styles.bubbleUser : styles.bubbleHer}>
            {b}
          </div>
        ))}
      </div>
    </div>
  )
}

function TypingBubble() {
  return (
    <div style={{ ...styles.row, justifyContent: 'flex-start' }}>
      <div style={{ ...styles.bubbleHer, ...styles.typing }}>
        <span style={styles.dot} />
        <span style={{ ...styles.dot, animationDelay: '0.2s' }} />
        <span style={{ ...styles.dot, animationDelay: '0.4s' }} />
      </div>
    </div>
  )
}

const PINK = '#e0457b'
const styles: Record<string, React.CSSProperties> = {
  shell: {
    display: 'flex',
    flexDirection: 'column',
    height: '100dvh',
    maxWidth: 640,
    margin: '0 auto',
    background: '#15131a',
    color: '#f2eef5',
    fontFamily: 'system-ui, -apple-system, sans-serif',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    borderBottom: '1px solid #2a2632',
    background: '#1c1922',
  },
  headerName: { display: 'flex', alignItems: 'center', gap: 12 },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: '50%',
    background: PINK,
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    fontSize: 18,
  },
  status: { fontSize: 12, color: '#9b8fae' },
  logout: {
    background: 'transparent',
    color: '#9b8fae',
    border: '1px solid #3a3444',
    borderRadius: 8,
    padding: '6px 12px',
    cursor: 'pointer',
    fontSize: 13,
  },
  thread: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  empty: { textAlign: 'center', color: '#6c6379', marginTop: 40 },
  row: { display: 'flex' },
  bubbleGroup: { display: 'flex', flexDirection: 'column', gap: 4, maxWidth: '78%' },
  bubbleHer: {
    background: '#2a2533',
    color: '#f2eef5',
    padding: '10px 14px',
    borderRadius: '18px 18px 18px 4px',
    fontSize: 15,
    lineHeight: 1.4,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  bubbleUser: {
    background: PINK,
    color: '#fff',
    padding: '10px 14px',
    borderRadius: '18px 18px 4px 18px',
    fontSize: 15,
    lineHeight: 1.4,
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  },
  typing: { display: 'flex', gap: 4, alignItems: 'center' },
  dot: {
    width: 7,
    height: 7,
    borderRadius: '50%',
    background: '#9b8fae',
    display: 'inline-block',
    animation: 'chat-blink 1.2s infinite both',
  },
  composer: {
    display: 'flex',
    gap: 8,
    padding: 12,
    borderTop: '1px solid #2a2632',
    background: '#1c1922',
  },
  input: {
    flex: 1,
    resize: 'none',
    background: '#15131a',
    color: '#f2eef5',
    border: '1px solid #3a3444',
    borderRadius: 20,
    padding: '10px 16px',
    fontSize: 15,
    fontFamily: 'inherit',
    outline: 'none',
  },
  send: {
    background: PINK,
    color: '#fff',
    border: 'none',
    borderRadius: 20,
    padding: '0 20px',
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
  },
}
