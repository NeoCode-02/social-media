import type { RealtimeEvent } from '@/api/types'

type Handler = (event: RealtimeEvent) => void
type GetTicketFn = () => Promise<string | null>

/** Singleton WebSocket client with ticket auth + exponential-backoff reconnect. */
class WSClient {
  private ws: WebSocket | null = null
  private handlers = new Set<Handler>()
  private getTicket: GetTicketFn | null = null
  private retry = 0
  private closedByUser = false
  private connecting = false

  connect(getTicket: GetTicketFn): void {
    this.getTicket = getTicket
    this.closedByUser = false
    if (this.ws && this.ws.readyState <= WebSocket.OPEN) return
    void this.open()
  }

  private async open(): Promise<void> {
    if (!this.getTicket || this.closedByUser || this.connecting) return
    this.connecting = true
    try {
      const ticket = await this.getTicket()
      if (this.closedByUser) return
      if (!ticket) {
        // Transient ticket failure (backend blip / token refresh race) — retry
        // instead of silently giving up, otherwise realtime stays dead forever.
        this.scheduleReconnect()
        return
      }
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      this.ws = new WebSocket(`${proto}://${location.host}/ws?ticket=${ticket}`)

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
      this.ws.onclose = () => this.scheduleReconnect()
      this.ws.onerror = () => this.ws?.close()
    } catch {
      this.scheduleReconnect()
    } finally {
      this.connecting = false
    }
  }

  private scheduleReconnect(): void {
    if (this.closedByUser) return
    const delay = Math.min(1000 * 2 ** this.retry, 15000)
    this.retry += 1
    setTimeout(() => void this.open(), delay)
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
