import type { RealtimeEvent } from '@/api/types'

type Handler = (event: RealtimeEvent) => void

/** Singleton WebSocket client with token auth + exponential-backoff reconnect. */
class WSClient {
  private ws: WebSocket | null = null
  private handlers = new Set<Handler>()
  private token: string | null = null
  private retry = 0
  private closedByUser = false

  connect(token: string): void {
    this.token = token
    this.closedByUser = false
    if (this.ws && this.ws.readyState <= WebSocket.OPEN) return
    this.open()
  }

  private open(): void {
    if (!this.token || this.closedByUser) return
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    this.ws = new WebSocket(`${proto}://${location.host}/ws?token=${this.token}`)

    this.ws.onopen = () => {
      this.retry = 0
    }
    this.ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as RealtimeEvent
        this.handlers.forEach((h) => h(event))
      } catch {
        /* ignore malformed frames */
      }
    }
    this.ws.onclose = () => {
      if (this.closedByUser) return
      const delay = Math.min(1000 * 2 ** this.retry, 15000)
      this.retry += 1
      setTimeout(() => this.open(), delay)
    }
    this.ws.onerror = () => this.ws?.close()
  }

  send(payload: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload))
    }
  }

  on(handler: Handler): () => void {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  close(): void {
    this.closedByUser = true
    this.ws?.close()
    this.ws = null
  }
}

export const wsClient = new WSClient()
