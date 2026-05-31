import type { Chat } from '@/api/types'

export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}

export function initials(name: string): string {
  return (
    name
      .trim()
      .split(/\s+/)
      .map((p) => p[0])
      .slice(0, 2)
      .join('')
      .toUpperCase() || '?'
  )
}

const AVATAR_COLORS = [
  '#7C6CFF',
  '#F4607A',
  '#34D399',
  '#F2B33A',
  '#56B3F0',
  '#C77DFF',
  '#FF8A5B',
]

export function avatarColor(seed: string): string {
  let h = 0
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0
  return AVATAR_COLORS[h % AVATAR_COLORS.length]
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

export function isImage(mime: string): boolean {
  return mime.startsWith('image/')
}

export function formatDayLabel(iso: string): string {
  const d = new Date(iso)
  const today = new Date()
  const yesterday = new Date()
  yesterday.setDate(today.getDate() - 1)
  const sameDay = (a: Date, b: Date) => a.toDateString() === b.toDateString()
  if (sameDay(d, today)) return 'Today'
  if (sameDay(d, yesterday)) return 'Yesterday'
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

export interface ChatFace {
  name: string
  url: string | null
  userId?: string
}

export function chatFace(chat: Chat, meId: string | undefined): ChatFace {
  if (chat.type === 'group') {
    return { name: chat.title ?? 'Group', url: chat.avatar_url }
  }
  const other = chat.members.find((m) => m.user.id !== meId)?.user
  return { name: other?.display_name ?? 'Direct message', url: other?.avatar_url ?? null, userId: other?.id }
}
