import { ArrowLeft } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { PostFeed } from './PostFeed'
import { useHashtagFeed } from './useFeed'

export function HashtagPage() {
  const { tag = '' } = useParams()
  const navigate = useNavigate()
  const feed = useHashtagFeed(tag)
  const posts = (feed.data?.pages ?? []).flatMap((p) => p.posts)

  return (
    <div className="mx-auto flex h-full w-full max-w-2xl flex-col border-x border-border">
      <header className="sticky top-0 z-10 flex items-center gap-4 border-b border-border bg-bg/80 px-4 py-3 backdrop-blur">
        <button
          onClick={() => navigate(-1)}
          className="flex h-9 w-9 items-center justify-center rounded-full text-muted transition hover:bg-cardhover hover:text-text"
        >
          <ArrowLeft size={18} />
        </button>
        <h1 className="truncate text-lg font-semibold">#{tag}</h1>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <PostFeed
          posts={posts}
          isLoading={feed.isLoading}
          hasMore={Boolean(feed.hasNextPage)}
          loadingMore={feed.isFetchingNextPage}
          onLoadMore={feed.fetchNextPage}
          emptyText={`No posts with #${tag} yet.`}
        />
      </div>
    </div>
  )
}
