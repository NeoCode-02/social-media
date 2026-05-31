import { Mic, Pause, Play } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { cn, formatDuration } from '@/lib/utils'

interface Props {
  src: string
  mine: boolean
  /** Voice note → compact mic styling; otherwise a labelled audio file row. */
  voice?: boolean
  name?: string
  durationMs?: number | null
}

export function AudioPlayer({ src, mine, voice = false, name, durationMs }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0) // 0..1
  const [elapsedMs, setElapsedMs] = useState(0)
  const [totalMs, setTotalMs] = useState(durationMs ?? 0)

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

  const fill = mine ? 'bg-accentink' : 'bg-accent'
  const track = mine ? 'bg-accentink/25' : 'bg-border'
  const timeLabel = formatDuration(elapsedMs || totalMs)

  return (
    <div className={cn('flex items-center gap-3', voice ? 'min-w-[180px]' : 'min-w-[200px]')}>
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
            className={cn('h-1.5 flex-1 cursor-pointer overflow-hidden rounded-full', track)}
          >
            <div className={cn('h-full rounded-full', fill)} style={{ width: `${progress * 100}%` }} />
          </div>
          <span className="shrink-0 text-[10px] tabular-nums opacity-70">{timeLabel}</span>
        </div>
      </div>
    </div>
  )
}
