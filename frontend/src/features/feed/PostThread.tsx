import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { getPost } from '@/api/posts'
import { PostCard } from './PostCard'
import { PostComposer } from './PostComposer'
import { PostFeed } from './PostFeed'
import { patchAllPosts } from './postCache'
import { useReplies } from './useFeed'

export function PostThread() {
  const { postId = '' } = useParams()
  const qc = useQueryClient()
  const navigate = useNavigate()

  const { data: post, isLoading } = useQuery({
    queryKey: ['post', postId],
    queryFn: async () => (await getPost(postId)).data,
    enabled: Boolean(postId),
  })
  const replies = useReplies(postId)
  const replyPosts = (replies.data?.pages ?? []).flatMap((p) => p.posts)

  function onReplied() {
    patchAllPosts(qc, postId, (p) => ({ ...p, reply_count: p.reply_count + 1 }))
    replies.refetch()
  }

  return (
    <div className="mx-auto flex h-full w-full max-w-2xl flex-col border-x border-border">
      <header className="sticky top-0 z-10 flex items-center gap-4 border-b border-border bg-bg/80 px-4 py-3 backdrop-blur">
        <button
          onClick={() => navigate(-1)}
          className="flex h-9 w-9 items-center justify-center rounded-full text-muted transition hover:bg-cardhover hover:text-text"
        >
          <ArrowLeft size={18} />
        </button>
        <h1 className="text-lg font-semibold">Post</h1>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {isLoading || !post ? (
          <div className="flex justify-center py-10 text-faint">
            <Loader2 size={22} className="animate-spin" />
          </div>
        ) : (
          <>
            <div className="border-b border-border">
              <PostCard post={post} emphasis />
            </div>
            <div className="border-b border-border">
              <PostComposer parentId={postId} placeholder="Post your reply" autoFocus onPosted={onReplied} />
            </div>
            <PostFeed
              posts={replyPosts}
              isLoading={replies.isLoading}
              hasMore={Boolean(replies.hasNextPage)}
              loadingMore={replies.isFetchingNextPage}
              onLoadMore={replies.fetchNextPage}
              emptyText="No replies yet."
            />
          </>
        )}
      </div>
    </div>
  )
}
