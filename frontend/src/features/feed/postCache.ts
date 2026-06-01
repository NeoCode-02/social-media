import type { InfiniteData, QueryClient } from '@tanstack/react-query'

import type { Post, PostPage } from '@/api/types'

type PostFn = (p: Post) => Post

/** Apply `fn` to a post with `id`, recursing into embedded repost_of/reply_to. */
export function applyToPost(post: Post, id: string, fn: PostFn): Post {
  let next = post
  if (post.repost_of) {
    const r = applyToPost(post.repost_of, id, fn)
    if (r !== post.repost_of) next = { ...next, repost_of: r }
  }
  if (post.reply_to) {
    const r = applyToPost(post.reply_to, id, fn)
    if (r !== post.reply_to) next = { ...next, reply_to: r }
  }
  if (next.id === id) next = fn(next)
  return next
}

function mapPage(data: InfiniteData<PostPage> | undefined, id: string, fn: PostFn) {
  if (!data) return data
  return {
    ...data,
    pages: data.pages.map((pg) => ({
      ...pg,
      posts: pg.posts.map((p) => applyToPost(p, id, fn)),
    })),
  }
}

/** Patch a post everywhere it may be cached (timeline, profile feeds, threads). */
export function patchAllPosts(qc: QueryClient, id: string, fn: PostFn): void {
  qc.setQueriesData<InfiniteData<PostPage>>({ queryKey: ['timeline'] }, (d) => mapPage(d, id, fn))
  qc.setQueriesData<InfiniteData<PostPage>>({ queryKey: ['globalFeed'] }, (d) => mapPage(d, id, fn))
  qc.setQueriesData<InfiniteData<PostPage>>({ queryKey: ['userFeed'] }, (d) => mapPage(d, id, fn))
  qc.setQueriesData<InfiniteData<PostPage>>({ queryKey: ['replies'] }, (d) => mapPage(d, id, fn))
  qc.setQueriesData<Post>({ queryKey: ['post'] }, (p) => (p ? applyToPost(p, id, fn) : p))
}

/** Insert a freshly created/received post at the top of the home + global feeds. */
export function prependToTimeline(qc: QueryClient, post: Post): void {
  const prepend = (key: string) =>
    qc.setQueryData<InfiniteData<PostPage>>([key], (old) => {
      if (!old || old.pages.length === 0) return old
      if (old.pages.some((pg) => pg.posts.some((p) => p.id === post.id))) return old
      const pages = old.pages.map((pg, i) =>
        i === 0 ? { ...pg, posts: [post, ...pg.posts] } : pg,
      )
      return { ...old, pages }
    })
  prepend('timeline')
  prepend('globalFeed')
}
