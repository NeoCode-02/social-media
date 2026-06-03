import { Loader2 } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

import type { Post } from '@/api/types'
import { PostCard } from './PostCard'

interface EmptyAction {
  label: string
  to: string
}

interface Props {
  posts: Post[]
  isLoading: boolean
  hasMore: boolean
  loadingMore: boolean
  onLoadMore: () => void
  emptyText?: string
  emptyAction?: EmptyAction
}

export function PostFeed({
  posts,
  isLoading,
  hasMore,
  loadingMore,
  onLoadMore,
  emptyText,
  emptyAction,
}: Props) {
  const sentinel = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!hasMore) return
    const el = sentinel.current
    if (!el) return
    const io = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loadingMore) onLoadMore()
      },
      { rootMargin: '600px' },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [hasMore, loadingMore, onLoadMore])

  if (isLoading) {
    return (
      <div className="flex justify-center py-10 text-faint">
        <Loader2 size={22} className="animate-spin" />
      </div>
    )
  }

  if (posts.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 px-4 py-16 text-center text-sm text-faint">
        <p>{emptyText ?? 'Nothing here yet.'}</p>
        {emptyAction && (
          <button
            onClick={() => navigate(emptyAction.to)}
            className="rounded-full bg-accent px-4 py-1.5 text-sm font-semibold text-accentink transition hover:brightness-105"
          >
            {emptyAction.label}
          </button>
        )}
      </div>
    )
  }

  return (
    <div>
      {posts.map((p) => (
        <PostCard key={p.id} post={p} />
      ))}
      <div ref={sentinel} />
      {loadingMore && (
        <div className="flex justify-center py-6 text-faint">
          <Loader2 size={20} className="animate-spin" />
        </div>
      )}
    </div>
  )
}
