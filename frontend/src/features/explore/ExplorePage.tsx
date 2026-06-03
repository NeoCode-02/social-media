import { useQuery } from '@tanstack/react-query'
import { Hash, Loader2, Search, TrendingUp, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { searchUsers } from '@/api/users'
import { Avatar } from '@/components/Avatar'
import { PostFeed } from '@/features/feed/PostFeed'
import { useGlobalFeed, usePostSearch, useTrending } from '@/features/feed/useFeed'

export function ExplorePage() {
  const navigate = useNavigate()
  const [raw, setRaw] = useState('')
  const [q, setQ] = useState('')

  useEffect(() => {
    const t = setTimeout(() => setQ(raw.trim()), 300)
    return () => clearTimeout(t)
  }, [raw])

  const userSearch = useQuery({
    queryKey: ['userSearch', q],
    queryFn: () => searchUsers(q).then((r) => r.data),
    enabled: q.length > 0,
  })
  const postSearch = usePostSearch(q)
  const postResults = (postSearch.data?.pages ?? []).flatMap((p) => p.posts)

  const trending = useTrending()
  const feed = useGlobalFeed()
  const feedPosts = (feed.data?.pages ?? []).flatMap((p) => p.posts)

  const searching = q.length > 0
  const people = userSearch.data ?? []

  return (
    <div className="mx-auto flex h-full w-full max-w-2xl flex-col border-x border-border">
      <header className="sticky top-0 z-10 border-b border-border bg-bg/80 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5">
          <Search size={17} className="shrink-0 text-faint" />
          <input
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder="Search people and posts"
            className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-faint"
          />
          {raw && (
            <button onClick={() => setRaw('')} aria-label="Clear search" className="text-faint hover:text-text">
              <X size={16} />
            </button>
          )}
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {searching ? (
          <>
            {userSearch.isLoading ? (
              <div className="flex justify-center py-6 text-faint">
                <Loader2 size={18} className="animate-spin" />
              </div>
            ) : people.length > 0 ? (
              <div className="divide-y divide-border border-b border-border">
                <p className="px-4 pt-3 text-xs font-semibold uppercase tracking-wide text-faint">
                  People
                </p>
                {people.map((u) => (
                  <button
                    key={u.id}
                    onClick={() => navigate(`/u/${u.id}`)}
                    className="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-card/40"
                  >
                    <Avatar name={u.display_name} src={u.avatar_url} userId={u.id} size={44} />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold">{u.display_name}</p>
                      <p className="truncate text-xs text-faint">@{u.username}</p>
                    </div>
                  </button>
                ))}
              </div>
            ) : null}

            <p className="px-4 pt-3 text-xs font-semibold uppercase tracking-wide text-faint">Posts</p>
            <PostFeed
              posts={postResults}
              isLoading={postSearch.isLoading}
              hasMore={Boolean(postSearch.hasNextPage)}
              loadingMore={postSearch.isFetchingNextPage}
              onLoadMore={postSearch.fetchNextPage}
              emptyText={`No posts for “${q}”.`}
              emptyAction={{ label: 'Try trending tags', to: '/explore' }}
            />
          </>
        ) : (
          <>
            {(trending.data?.length ?? 0) > 0 && (
              <div className="border-b border-border px-4 py-3">
                <p className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
                  <TrendingUp size={16} className="text-accent" /> Trending
                </p>
                <div className="flex flex-wrap gap-2">
                  {trending.data!.map((t) => (
                    <button
                      key={t.tag}
                      onClick={() => navigate(`/tag/${t.tag}`)}
                      className="flex items-center gap-1 rounded-full border border-border bg-card px-3 py-1.5 text-sm transition hover:border-accent/50 hover:bg-cardhover"
                    >
                      <Hash size={13} className="text-accent" />
                      {t.tag}
                      <span className="text-faint">{t.count}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            <PostFeed
              posts={feedPosts}
              isLoading={feed.isLoading}
              hasMore={Boolean(feed.hasNextPage)}
              loadingMore={feed.isFetchingNextPage}
              onLoadMore={feed.fetchNextPage}
              emptyText="No posts on the platform yet."
              emptyAction={{ label: 'Be the first to post', to: '/feed' }}
            />
          </>
        )}
      </div>
    </div>
  )
}
