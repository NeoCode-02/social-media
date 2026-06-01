import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AtSign, Bell, Heart, Loader2, MessageCircle, UserPlus } from 'lucide-react'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import { listNotifications, markNotificationsRead } from '@/api/notifications'
import type { Notification, NotificationPage, NotificationType } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { formatRelative } from '@/lib/utils'

const VERB: Record<NotificationType, string> = {
  like: 'liked your post',
  reply: 'replied to your post',
  mention: 'mentioned you',
  follow: 'followed you',
  follow_request: 'requested to follow you',
  follow_accept: 'accepted your follow request',
}

function NotifIcon({ type }: { type: NotificationType }) {
  const cls = 'shrink-0'
  if (type === 'like') return <Heart size={15} className={`${cls} text-danger`} />
  if (type === 'reply') return <MessageCircle size={15} className={`${cls} text-accent`} />
  if (type === 'mention') return <AtSign size={15} className={`${cls} text-violet`} />
  return <UserPlus size={15} className={`${cls} text-online`} />
}

function targetOf(n: Notification): string {
  if (n.post_id && (n.type === 'like' || n.type === 'reply' || n.type === 'mention')) {
    return `/post/${n.post_id}`
  }
  return `/u/${n.actor.id}`
}

export function NotificationsPage() {
  const qc = useQueryClient()
  const navigate = useNavigate()

  const query = useInfiniteQuery({
    queryKey: ['notifications'],
    queryFn: ({ pageParam }) => listNotifications(pageParam).then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last: NotificationPage) => last.next_cursor ?? undefined,
  })

  const markRead = useMutation({
    mutationFn: (ids?: string[]) => markNotificationsRead(ids),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  // Clear the unread badge once the page is opened.
  useEffect(() => {
    markNotificationsRead().then(() =>
      qc.invalidateQueries({ queryKey: ['notifications', 'unread'] }),
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const items = (query.data?.pages ?? []).flatMap((p) => p.notifications)

  return (
    <div className="mx-auto flex h-full w-full max-w-2xl flex-col border-x border-border">
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-bg/80 px-4 py-3 backdrop-blur">
        <h1 className="text-lg font-semibold">Notifications</h1>
        {items.some((n) => !n.read) && (
          <button
            onClick={() => markRead.mutate(undefined)}
            className="text-xs font-semibold text-accent hover:underline"
          >
            Mark all read
          </button>
        )}
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {query.isLoading ? (
          <div className="flex justify-center py-10 text-faint">
            <Loader2 size={20} className="animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center gap-2 px-6 py-20 text-center text-faint">
            <Bell size={26} />
            <p className="text-sm">No notifications yet.</p>
          </div>
        ) : (
          <ul>
            {items.map((n) => (
              <li key={n.id}>
                <button
                  onClick={() => navigate(targetOf(n))}
                  className={`flex w-full items-center gap-3 border-b border-border px-4 py-3 text-left transition hover:bg-card/40 ${
                    n.read ? '' : 'bg-accent/5'
                  }`}
                >
                  <NotifIcon type={n.type} />
                  <Avatar name={n.actor.display_name} src={n.actor.avatar_url} userId={n.actor.id} size={40} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm">
                      <span className="font-semibold">{n.actor.display_name}</span>{' '}
                      <span className="text-muted">{VERB[n.type]}</span>
                    </p>
                    {n.post_preview && (
                      <p className="truncate text-xs text-faint">{n.post_preview}</p>
                    )}
                  </div>
                  <span className="shrink-0 text-xs text-faint">{formatRelative(n.created_at)}</span>
                </button>
              </li>
            ))}
            {query.hasNextPage && (
              <li className="p-3 text-center">
                <button
                  onClick={() => query.fetchNextPage()}
                  disabled={query.isFetchingNextPage}
                  className="text-sm text-accent hover:underline disabled:opacity-50"
                >
                  {query.isFetchingNextPage ? 'Loading…' : 'Load more'}
                </button>
              </li>
            )}
          </ul>
        )}
      </div>
    </div>
  )
}
