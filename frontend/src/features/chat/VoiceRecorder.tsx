import { Send, Trash2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { formatDuration } from '@/lib/utils'

interface Props {
  onSend: (file: File, durationMs: number) => void
  onCancel: () => void
}

function pickMime(): string {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg']
  for (const m of candidates) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(m)) return m
  }
  return ''
}

export function VoiceRecorder({ onSend, onCancel }: Props) {
  const [elapsed, setElapsed] = useState(0)
  const [error, setError] = useState('')
  const recorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const startedRef = useRef(0)
  const sendOnStopRef = useRef(false)

  useEffect(() => {
    let timer: number | undefined
    let cancelled = false

    async function start() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream
        const mime = pickMime()
        const rec = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined)
        recorderRef.current = rec
        chunksRef.current = []
        rec.ondataavailable = (e) => e.data.size > 0 && chunksRef.current.push(e.data)
        rec.onstop = () => {
          stream.getTracks().forEach((t) => t.stop())
          if (!sendOnStopRef.current) return
          const type = rec.mimeType || mime || 'audio/webm'
          const blob = new Blob(chunksRef.current, { type })
          const ext = type.includes('mp4') ? 'm4a' : type.includes('ogg') ? 'ogg' : 'webm'
          const file = new File([blob], `voice-${Date.now()}.${ext}`, { type })
          onSend(file, Date.now() - startedRef.current)
        }
        startedRef.current = Date.now()
        rec.start()
        timer = window.setInterval(() => setElapsed(Date.now() - startedRef.current), 200)
      } catch {
        setError('Microphone access denied')
      }
    }

    start()
    return () => {
      cancelled = true
      clearInterval(timer)
      streamRef.current?.getTracks().forEach((t) => t.stop())
    }
  }, [onSend])

  function stop(send: boolean) {
    sendOnStopRef.current = send
    const rec = recorderRef.current
    if (rec && rec.state !== 'inactive') rec.stop()
    if (!send) onCancel()
  }

  if (error) {
    return (
      <div className="flex items-center justify-between rounded-full border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
        {error}
        <button onClick={onCancel} className="text-faint hover:text-text">
          <Trash2 size={16} />
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3 rounded-full border border-border bg-card px-4 py-2">
      <button
        type="button"
        onClick={() => stop(false)}
        title="Cancel recording"
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-faint transition hover:bg-cardhover hover:text-danger"
      >
        <Trash2 size={18} />
      </button>
      <span className="flex h-2.5 w-2.5 shrink-0 rounded-full bg-danger">
        <span className="h-full w-full animate-ping rounded-full bg-danger" />
      </span>
      <span className="flex-1 text-sm tabular-nums text-muted">
        Recording… {formatDuration(elapsed)}
      </span>
      <button
        type="button"
        onClick={() => stop(true)}
        title="Send voice message"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-accentink transition hover:brightness-105 active:scale-95"
      >
        <Send size={18} />
      </button>
    </div>
  )
}
