import { useInfiniteQuery } from '@tanstack/react-query'

import { listReplies, listTimeline, userFeed } from '@/api/posts'
import type { PostPage } from '@/api/types'

const nextCursor = (last: PostPage) => last.next_cursor ?? undefined

export function useTimeline() {
  return useInfiniteQuery({
    queryKey: ['timeline'],
    queryFn: ({ pageParam }) => listTimeline(pageParam).then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: nextCursor,
  })
}

export function useUserFeed(userId: string) {
  return useInfiniteQuery({
    queryKey: ['userFeed', userId],
    queryFn: ({ pageParam }) => userFeed(userId, pageParam).then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: nextCursor,
  })
}

export function useReplies(postId: string) {
  return useInfiniteQuery({
    queryKey: ['replies', postId],
    queryFn: ({ pageParam }) => listReplies(postId, pageParam).then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: nextCursor,
  })
}
