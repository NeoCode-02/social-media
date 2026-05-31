import { useQueryClient } from '@tanstack/react-query'

import type { Post } from '@/api/types'
import { PostComposer } from './PostComposer'
import { PostFeed } from './PostFeed'
import { prependToTimeline } from './postCache'
import { useTimeline } from './useFeed'

export function FeedPage() {
  const qc = useQueryClient()
  const q = useTimeline()
  const posts = (q.data?.pages ?? []).flatMap((p) => p.posts)

  function onPosted(post: Post) {
    prependToTimeline(qc, post)
    qc.invalidateQueries({ queryKey: ['user'] }) // refresh own posts_count
  }

  return (
    <div className="mx-auto flex h-full w-full max-w-2xl flex-col border-x border-border">
      <header className="sticky top-0 z-10 border-b border-border bg-bg/80 px-4 py-3 backdrop-blur">
        <h1 className="text-lg font-semibold">Home</h1>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="border-b border-border">
          <PostComposer onPosted={onPosted} />
        </div>
        <PostFeed
          posts={posts}
          isLoading={q.isLoading}
          hasMore={Boolean(q.hasNextPage)}
          loadingMore={q.isFetchingNextPage}
          onLoadMore={q.fetchNextPage}
          emptyText="Your timeline is empty. Follow people or write the first post!"
        />
      </div>
    </div>
  )
}
