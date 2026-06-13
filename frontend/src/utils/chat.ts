import { getAuthToken } from './api'

export type ChatEvent =
  | { type: 'ready'; conversation_id: number }
  | { type: 'typing' }
  | { type: 'token'; delta: string }
  | { type: 'done' }
  | { type: 'error'; detail: string }

// Server closes with this code when the connection's token is invalid/expired.
// Reconnecting won't help until the user re-authenticates, so we stop.
const WS_UNAUTHORIZED = 4401

type Handlers = {
  onEvent: (e: ChatEvent) => void
  onOpen?: () => void
  onClose?: () => void
}

/** Build the WebSocket URL, deriving ws/wss + host from the current page.
 *  The auth token is NOT placed in the URL (query strings leak into access logs,
 *  proxies, and browser history); it travels in the Sec-WebSocket-Protocol
 *  header instead — see `connect()`. */
function wsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/api/chat/ws`
}

/** Thin WebSocket client for the chat stream with basic auto-reconnect. */
export class ChatSocket {
  private ws: WebSocket | null = null
  private handlers: Handlers
  private closedByUser = false
  private retries = 0

  constructor(handlers: Handlers) {
    this.handlers = handlers
  }

  connect() {
    this.closedByUser = false
    // Send the bearer token as a WebSocket subprotocol ("bearer", "<token>")
    // rather than in the URL. Subprotocols ride in the Sec-WebSocket-Protocol
    // header, which is not written to access logs or browser history.
    const token = getAuthToken() ?? ''
    const ws = new WebSocket(wsUrl(), ['bearer', token])
    this.ws = ws

    ws.onopen = () => {
      this.retries = 0 // healthy connection resets the backoff
      this.handlers.onOpen?.()
    }
    ws.onmessage = (ev) => {
      try {
        this.handlers.onEvent(JSON.parse(ev.data) as ChatEvent)
      } catch {
        /* ignore malformed frames */
      }
    }
    ws.onclose = (ev) => {
      this.handlers.onClose?.()
      // Don't reconnect if the user closed us, or the server rejected auth —
      // retrying with the same bad token just hammers the server every cycle.
      if (this.closedByUser || ev.code === WS_UNAUTHORIZED) return
      // Exponential backoff with jitter, capped at 30s (network blip, restart).
      const delay = Math.min(2000 * 2 ** this.retries, 30000)
      const jittered = delay * (0.5 + Math.random() * 0.5)
      this.retries += 1
      setTimeout(() => this.connect(), jittered)
    }
  }

  send(text: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ text }))
    }
  }

  close() {
    this.closedByUser = true
    this.ws?.close()
  }
}

/** Split an assistant reply into separate text bubbles on the `---` delimiter. */
export function splitBubbles(text: string): string[] {
  const parts = text
    .split('---')
    .map((p) => p.trim())
    .filter(Boolean)
  return parts.length ? parts : [text.trim()]
}
