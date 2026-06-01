import { useInfiniteQuery, useQuery } from '@tanstack/react-query'

import {
  globalFeed,
  hashtagFeed,
  listReplies,
  listTimeline,
  searchPosts,
  trendingHashtags,
  userFeed,
} from '@/api/posts'
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

export function useGlobalFeed() {
  return useInfiniteQuery({
    queryKey: ['globalFeed'],
    queryFn: ({ pageParam }) => globalFeed(pageParam).then((r) => r.data),
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
    enabled: Boolean(userId) && !userId.startsWith('@'),
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

export function useHashtagFeed(tag: string) {
  return useInfiniteQuery({
    queryKey: ['hashtag', tag],
    queryFn: ({ pageParam }) => hashtagFeed(tag, pageParam).then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: nextCursor,
    enabled: Boolean(tag),
  })
}

export function usePostSearch(q: string) {
  return useInfiniteQuery({
    queryKey: ['postSearch', q],
    queryFn: ({ pageParam }) => searchPosts(q, pageParam).then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: nextCursor,
    enabled: q.length > 0,
  })
}

export function useTrending() {
  return useQuery({
    queryKey: ['trending'],
    queryFn: () => trendingHashtags().then((r) => r.data),
    staleTime: 60_000,
  })
}
