import { Loader2 } from 'lucide-react'
import { useEffect, useRef } from 'react'

import type { Post } from '@/api/types'
import { PostCard } from './PostCard'

interface Props {
  posts: Post[]
  isLoading: boolean
  hasMore: boolean
  loadingMore: boolean
  onLoadMore: () => void
  emptyText?: string
}

export function PostFeed({ posts, isLoading, hasMore, loadingMore, onLoadMore, emptyText }: Props) {
  const sentinel = useRef<HTMLDivElement>(null)

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
      <div className="px-4 py-16 text-center text-sm text-faint">
        {emptyText ?? 'Nothing here yet.'}
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
