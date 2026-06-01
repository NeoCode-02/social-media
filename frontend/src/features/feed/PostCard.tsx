import { useQueryClient } from '@tanstack/react-query'
import { BarChart3, Heart, MessageCircle, Repeat2, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import {
  deletePost,
  likePost,
  repostPost,
  unlikePost,
  unrepostPost,
} from '@/api/posts'
import type { Post } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { cn, formatRelative } from '@/lib/utils'
import { useAuth } from '@/store/auth'
import { PostAttachments } from './PostAttachments'
import { patchAllPosts } from './postCache'

function isPureRepost(p: Post): boolean {
  return Boolean(p.repost_of) && !p.text && p.attachments.length === 0
}

function compactNumber(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`
  return n ? String(n) : ''
}

interface Props {
  post: Post
  /** Larger styling for the focused post in a thread. */
  emphasis?: boolean
}

export function PostCard({ post, emphasis }: Props) {
  const me = useAuth((s) => s.user)
  const qc = useQueryClient()
  const navigate = useNavigate()

  // A bare repost renders as the original with a "reposted" ribbon on top.
  if (isPureRepost(post) && post.repost_of) {
    return (
      <div>
        <div className="flex items-center gap-2 pl-12 pt-2 text-xs font-medium text-faint">
          <Repeat2 size={13} />
          {post.author.id === me?.id ? 'You reposted' : `${post.author.display_name} reposted`}
        </div>
        <PostCard post={post.repost_of} />
      </div>
    )
  }

  function openProfile(e: React.MouseEvent) {
    e.stopPropagation()
    navigate(`/u/${post.author.id}`)
  }

  function open() {
    navigate(`/post/${post.id}`)
  }

  async function toggleLike(e: React.MouseEvent) {
    e.stopPropagation()
    const liked = post.liked_by_me
    patchAllPosts(qc, post.id, (p) => ({
      ...p,
      liked_by_me: !liked,
      like_count: p.like_count + (liked ? -1 : 1),
    }))
    try {
      await (liked ? unlikePost(post.id) : likePost(post.id))
    } catch {
      patchAllPosts(qc, post.id, (p) => ({
        ...p,
        liked_by_me: liked,
        like_count: p.like_count + (liked ? 1 : -1),
      }))
    }
  }

  async function toggleRepost(e: React.MouseEvent) {
    e.stopPropagation()
    const on = post.reposted_by_me
    patchAllPosts(qc, post.id, (p) => ({
      ...p,
      reposted_by_me: !on,
      repost_count: p.repost_count + (on ? -1 : 1),
    }))
    try {
      await (on ? unrepostPost(post.id) : repostPost(post.id))
      qc.invalidateQueries({ queryKey: ['timeline'] })
      qc.invalidateQueries({ queryKey: ['userFeed'] })
    } catch {
      patchAllPosts(qc, post.id, (p) => ({
        ...p,
        reposted_by_me: on,
        repost_count: p.repost_count + (on ? 1 : -1),
      }))
    }
  }

  async function onDelete(e: React.MouseEvent) {
    e.stopPropagation()
    await deletePost(post.id)
    qc.invalidateQueries({ queryKey: ['timeline'] })
    qc.invalidateQueries({ queryKey: ['userFeed'] })
    qc.invalidateQueries({ queryKey: ['replies'] })
    qc.removeQueries({ queryKey: ['post', post.id] })
  }

  const mine = post.author.id === me?.id
  const deleted = Boolean(post.deleted_at)

  return (
    <article
      onClick={emphasis ? undefined : open}
      className={cn(
        'flex cursor-pointer gap-3 border-b border-border px-4 py-3 transition hover:bg-card/40',
        emphasis && 'cursor-default hover:bg-transparent',
      )}
    >
      <button onClick={openProfile} className="shrink-0 self-start">
        <Avatar name={post.author.display_name} src={post.author.avatar_url} size={emphasis ? 48 : 40} />
      </button>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 text-sm">
          <button onClick={openProfile} className="truncate font-semibold hover:underline">
            {post.author.display_name}
          </button>
          <span className="truncate text-faint">@{post.author.username}</span>
          {!emphasis && (
            <>
              <span className="text-faint">·</span>
              <span className="shrink-0 text-faint">{formatRelative(post.created_at)}</span>
            </>
          )}
          {mine && !deleted && (
            <button
              onClick={onDelete}
              className="ml-auto flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-faint opacity-0 transition hover:bg-cardhover hover:text-danger group-hover:opacity-100"
              title="Delete"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>

        {post.reply_to && (
          <p className="mt-0.5 text-xs text-faint">
            Replying to{' '}
            <span className="text-accent">@{post.reply_to.author.username}</span>
          </p>
        )}

        {deleted ? (
          <p className="mt-1 text-sm italic text-faint">This post was deleted</p>
        ) : (
          <>
            {post.text && (
              <p className={cn('mt-1 whitespace-pre-wrap break-words', emphasis ? 'text-[15px]' : 'text-sm')}>
                {post.text}
              </p>
            )}
            {post.attachments.length > 0 && <PostAttachments attachments={post.attachments} />}

            {/* Quote-embed of another post. */}
            {post.repost_of && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  navigate(`/post/${post.repost_of!.id}`)
                }}
                className="mt-2 block w-full rounded-2xl border border-border p-3 text-left transition hover:bg-card/60"
              >
                <div className="flex items-center gap-1.5 text-xs">
                  <Avatar
                    name={post.repost_of.author.display_name}
                    src={post.repost_of.author.avatar_url}
                    size={18}
                  />
                  <span className="font-semibold">{post.repost_of.author.display_name}</span>
                  <span className="text-faint">@{post.repost_of.author.username}</span>
                </div>
                {post.repost_of.text && (
                  <p className="mt-1 line-clamp-4 text-sm text-muted">{post.repost_of.text}</p>
                )}
              </button>
            )}
          </>
        )}

        {!deleted && (
          <div className="mt-2 flex max-w-md items-center justify-between text-faint">
            <button
              onClick={(e) => {
                e.stopPropagation()
                navigate(`/post/${post.id}`)
              }}
              className="group flex items-center gap-1.5 text-xs transition hover:text-accent"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full transition group-hover:bg-accent/10">
                <MessageCircle size={16} />
              </span>
              {compactNumber(post.reply_count)}
            </button>

            <button
              onClick={toggleRepost}
              className={cn(
                'group flex items-center gap-1.5 text-xs transition hover:text-online',
                post.reposted_by_me && 'text-online',
              )}
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full transition group-hover:bg-online/10">
                <Repeat2 size={16} />
              </span>
              {compactNumber(post.repost_count)}
            </button>

            <button
              onClick={toggleLike}
              className={cn(
                'group flex items-center gap-1.5 text-xs transition hover:text-danger',
                post.liked_by_me && 'text-danger',
              )}
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full transition group-hover:bg-danger/10">
                <Heart size={16} fill={post.liked_by_me ? 'currentColor' : 'none'} />
              </span>
              {compactNumber(post.like_count)}
            </button>

            <span className="flex items-center gap-1.5 text-xs" title={`${post.view_count} views`}>
              <span className="flex h-8 w-8 items-center justify-center">
                <BarChart3 size={16} />
              </span>
              {compactNumber(post.view_count)}
            </span>
          </div>
        )}
      </div>
    </article>
  )
}
