import { useQuery } from '@tanstack/react-query'
import { Loader2, Search, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { searchUsers } from '@/api/users'
import { Avatar } from '@/components/Avatar'
import { PostFeed } from '@/features/feed/PostFeed'
import { useGlobalFeed } from '@/features/feed/useFeed'

export function ExplorePage() {
  const navigate = useNavigate()
  const [raw, setRaw] = useState('')
  const [q, setQ] = useState('')

  useEffect(() => {
    const t = setTimeout(() => setQ(raw.trim()), 300)
    return () => clearTimeout(t)
  }, [raw])

  const search = useQuery({
    queryKey: ['userSearch', q],
    queryFn: () => searchUsers(q).then((r) => r.data),
    enabled: q.length > 0,
  })

  const feed = useGlobalFeed()
  const posts = (feed.data?.pages ?? []).flatMap((p) => p.posts)
  const searching = q.length > 0

  return (
    <div className="mx-auto flex h-full w-full max-w-2xl flex-col border-x border-border">
      <header className="sticky top-0 z-10 border-b border-border bg-bg/80 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2.5">
          <Search size={17} className="shrink-0 text-faint" />
          <input
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder="Search people"
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
          search.isLoading ? (
            <div className="flex justify-center py-10 text-faint">
              <Loader2 size={20} className="animate-spin" />
            </div>
          ) : (search.data?.length ?? 0) === 0 ? (
            <div className="px-4 py-16 text-center text-sm text-faint">
              No people found for “{q}”.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {search.data!.map((u) => (
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
          )
        ) : (
          <PostFeed
            posts={posts}
            isLoading={feed.isLoading}
            hasMore={Boolean(feed.hasNextPage)}
            loadingMore={feed.isFetchingNextPage}
            onLoadMore={feed.fetchNextPage}
            emptyText="No posts on the platform yet."
          />
        )}
      </div>
    </div>
  )
}
