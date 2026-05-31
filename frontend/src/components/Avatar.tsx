import { avatarColor, cn, initials } from '@/lib/utils'
import { useRealtimeStore } from '@/store/realtime'

interface AvatarProps {
  name: string
  src?: string | null
  userId?: string
  showPresence?: boolean
  size?: number
  className?: string
}

export function Avatar({ name, src, userId, showPresence, size = 40, className }: AvatarProps) {
  const online = useRealtimeStore((s) => (userId ? s.online[userId] : false))

  return (
    <div className={cn('relative shrink-0', className)} style={{ width: size, height: size }}>
      {src ? (
        <img
          src={src}
          alt={name}
          className="h-full w-full rounded-full object-cover"
          draggable={false}
        />
      ) : (
        <div
          className="flex h-full w-full items-center justify-center rounded-full font-semibold text-white"
          style={{ background: avatarColor(name), fontSize: size * 0.4 }}
        >
          {initials(name)}
        </div>
      )}
      {showPresence && userId && (
        <span
          className={cn(
            'absolute bottom-0 right-0 block rounded-full ring-2 ring-elev transition-colors',
            online ? 'bg-online' : 'bg-faint',
          )}
          style={{ width: size * 0.28, height: size * 0.28 }}
        >
          {online && (
            <span className="absolute inset-0 animate-ping rounded-full bg-online opacity-60" />
          )}
        </span>
      )}
    </div>
  )
}
