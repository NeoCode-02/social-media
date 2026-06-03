import { Mic, Pause, Play } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'

import { cn, formatDuration } from '@/lib/utils'

interface Props {
  src: string
  mine: boolean
  /** Voice note → compact mic styling; otherwise a labelled audio file row. */
  voice?: boolean
  name?: string
  durationMs?: number | null
}

const BARS = 28

/**
 * Tiny deterministic pseudo-waveform. Real PCM would need a worker + decode;
 * this gives every voice note a consistent visual identity so two notes
 * never look identical (which a flat line would). Seeded by the URL so the
 * same recording always shows the same shape.
 */
function sparklineHeights(src: string, bars: number): number[] {
  let seed = 0
  for (let i = 0; i < src.length; i++) seed = (seed * 31 + src.charCodeAt(i)) | 0
  const out: number[] = []
  for (let i = 0; i < bars; i++) {
    // Mulberry32-like single-step
    seed = (seed + 0x6d2b79f5) | 0
    let t = seed
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    const r = ((t ^ (t >>> 14)) >>> 0) / 0xffffffff
    // Shape: stronger in the middle, taper at edges (typical voice energy).
    const bell = 1 - Math.abs((i - bars / 2) / (bars / 2))
    out.push(0.25 + 0.75 * r * (0.4 + 0.6 * bell))
  }
  return out
}

export function AudioPlayer({ src, mine, voice = false, name, durationMs }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0) // 0..1
  const [elapsedMs, setElapsedMs] = useState(0)
  const [totalMs, setTotalMs] = useState(durationMs ?? 0)

  const heights = useMemo(() => sparklineHeights(src, BARS), [src])

  useEffect(() => {
    const a = audioRef.current
    if (!a) return
    const onTime = () => {
      setElapsedMs(a.currentTime * 1000)
      if (a.duration && Number.isFinite(a.duration)) setProgress(a.currentTime / a.duration)
    }
    const onMeta = () => {
      if (a.duration && Number.isFinite(a.duration)) setTotalMs(a.duration * 1000)
    }
    const onEnd = () => {
      setPlaying(false)
      setProgress(0)
      setElapsedMs(0)
    }
    a.addEventListener('timeupdate', onTime)
    a.addEventListener('loadedmetadata', onMeta)
    a.addEventListener('ended', onEnd)
    return () => {
      a.removeEventListener('timeupdate', onTime)
      a.removeEventListener('loadedmetadata', onMeta)
      a.removeEventListener('ended', onEnd)
    }
  }, [])

  function toggle() {
    const a = audioRef.current
    if (!a) return
    if (a.paused) {
      a.play()
      setPlaying(true)
    } else {
      a.pause()
      setPlaying(false)
    }
  }

  function seek(e: React.MouseEvent<HTMLDivElement>) {
    const a = audioRef.current
    if (!a || !a.duration || !Number.isFinite(a.duration)) return
    const rect = e.currentTarget.getBoundingClientRect()
    const ratio = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width))
    a.currentTime = ratio * a.duration
  }

  const fillStyle = mine
    ? { background: 'var(--color-accentink)' }
    : { background: 'var(--color-accent)' }
  const dimStyle = mine
    ? { background: 'color-mix(in oklab, var(--color-accentink) 28%, transparent)' }
    : { background: 'var(--color-border)' }
  const timeLabel = formatDuration(elapsedMs || totalMs)
  const playheadIdx = Math.min(BARS - 1, Math.floor(progress * BARS))

  return (
    <div className={cn('flex items-center gap-3', voice ? 'min-w-[180px]' : 'min-w-[220px]')}>
      <audio ref={audioRef} src={src} preload="metadata" className="hidden" />
      <button
        onClick={toggle}
        className={cn(
          'flex h-9 w-9 shrink-0 items-center justify-center rounded-full transition active:scale-95',
          mine ? 'bg-accentink/20 text-accentink' : 'bg-accent/15 text-accent',
        )}
        title={playing ? 'Pause' : 'Play'}
      >
        {playing ? <Pause size={16} /> : <Play size={16} className="translate-x-[1px]" />}
      </button>
      <div className="min-w-0 flex-1">
        {!voice && name && <p className="mb-1 truncate text-xs font-medium">{name}</p>}
        <div className="flex items-center gap-2">
          {voice && <Mic size={13} className="shrink-0 opacity-60" />}
          <div
            onClick={seek}
            className="relative flex h-6 flex-1 cursor-pointer items-center"
            title={`${Math.round(progress * 100)}%`}
          >
            {heights.map((h, i) => (
              <span
                key={i}
                className="mx-[1px] flex-1 rounded-sm transition-colors"
                style={{
                  height: `${Math.max(18, h * 100)}%`,
                  ...(i <= playheadIdx ? fillStyle : dimStyle),
                }}
              />
            ))}
          </div>
          <span className="shrink-0 text-[10px] tabular-nums opacity-70">{timeLabel}</span>
        </div>
      </div>
    </div>
  )
}
