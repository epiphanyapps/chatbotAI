import { getAuthToken } from './api'

export type ChatEvent =
  | { type: 'ready'; conversation_id: number }
  | { type: 'typing' }
  | { type: 'token'; delta: string }
  | { type: 'done' }

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

    ws.onopen = () => this.handlers.onOpen?.()
    ws.onmessage = (ev) => {
      try {
        this.handlers.onEvent(JSON.parse(ev.data) as ChatEvent)
      } catch {
        /* ignore malformed frames */
      }
    }
    ws.onclose = () => {
      this.handlers.onClose?.()
      if (!this.closedByUser) {
        // Reconnect after a short backoff (e.g. token refresh, network blip).
        setTimeout(() => this.connect(), 2000)
      }
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
