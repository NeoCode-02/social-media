import { useQuery, useQueryClient } from '@tanstack/react-query'
import { AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  CalendarDays,
  Link2,
  Loader2,
  Lock,
  MapPin,
  MessageSquare,
  UserCheck,
} from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { createDm } from '@/api/chats'
import { followUser, listFollowRequests, unfollowUser } from '@/api/follows'
import { getUser } from '@/api/users'
import type { UserProfile } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { FollowRequests } from '@/features/profile/FollowRequests'
import { ProfileDialog } from '@/features/profile/ProfileDialog'
import { useAuth } from '@/store/auth'
import { PostFeed } from './PostFeed'
import { useUserFeed } from './useFeed'

function websiteHref(raw: string): string {
  return /^https?:\/\//i.test(raw) ? raw : `https://${raw}`
}

export function ProfilePage() {
  const { userId = '' } = useParams()
  const me = useAuth((s) => s.user)
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [editing, setEditing] = useState(false)
  const [showRequests, setShowRequests] = useState(false)

  const { data: profile, isLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: async () => (await getUser(userId)).data,
    enabled: Boolean(userId),
  })
  const isMe = me?.id === userId
  const canViewPosts = Boolean(profile?.can_view_posts)
  const feed = useUserFeed(userId)
  const posts = (feed.data?.pages ?? []).flatMap((p) => p.posts)

  // Pending follow-request count (own profile only).
  const requests = useQuery({
    queryKey: ['followRequests'],
    queryFn: () => listFollowRequests().then((r) => r.data),
    enabled: isMe,
  })
  const pendingCount = requests.data?.length ?? 0

  function patchProfile(update: Partial<UserProfile>) {
    qc.setQueryData<UserProfile>(['user', userId], (u) => (u ? { ...u, ...update } : u))
  }

  async function toggleFollow() {
    if (!profile) return
    const state = profile.follow_state

    if (state === 'accepted' || state === 'pending') {
      // Unfollow, or cancel a still-pending request.
      patchProfile({
        is_following: false,
        follow_state: 'none',
        followers_count: profile.followers_count - (state === 'accepted' ? 1 : 0),
        can_view_posts: profile.is_private ? false : profile.can_view_posts,
      })
      try {
        await unfollowUser(userId)
        qc.invalidateQueries({ queryKey: ['userFeed', userId] })
      } catch {
        qc.invalidateQueries({ queryKey: ['user', userId] })
      }
      return
    }

    // Follow a public account (instant) or request a private one (pending).
    try {
      const { data } = await followUser(userId)
      const accepted = data.status === 'accepted'
      patchProfile({
        follow_state: data.status,
        is_following: accepted,
        followers_count: profile.followers_count + (accepted ? 1 : 0),
        can_view_posts: accepted ? true : profile.can_view_posts,
      })
      if (accepted) {
        qc.invalidateQueries({ queryKey: ['userFeed', userId] })
        qc.invalidateQueries({ queryKey: ['timeline'] })
      }
    } catch {
      qc.invalidateQueries({ queryKey: ['user', userId] })
    }
  }

  const followLabel =
    profile?.follow_state === 'accepted'
      ? 'Following'
      : profile?.follow_state === 'pending'
        ? 'Requested'
        : 'Follow'

  async function onMessage() {
    const { data } = await createDm(userId)
    navigate(`/c/${data.id}`)
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
        <h1 className="truncate text-lg font-semibold">{profile?.display_name ?? 'Profile'}</h1>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {isLoading || !profile ? (
          <div className="flex justify-center py-10 text-faint">
            <Loader2 size={22} className="animate-spin" />
          </div>
        ) : (
          <>
            <div className="h-28 bg-gradient-to-br from-accent/30 via-violet/20 to-transparent" />
            <div className="px-4 pb-3">
              <div className="-mt-12 mb-3 flex items-end justify-between">
                <div className="rounded-full ring-4 ring-bg">
                  <Avatar
                    name={profile.display_name}
                    src={profile.avatar_url}
                    userId={profile.id}
                    showPresence
                    size={88}
                  />
                </div>
                {isMe ? (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setShowRequests(true)}
                      title="Follow requests"
                      className="relative flex h-10 w-10 items-center justify-center rounded-full border border-border transition hover:bg-cardhover"
                    >
                      <UserCheck size={17} />
                      {pendingCount > 0 && (
                        <span className="absolute -right-1 -top-1 flex h-5 min-w-[20px] items-center justify-center rounded-full bg-accent px-1 text-[11px] font-bold text-accentink">
                          {pendingCount}
                        </span>
                      )}
                    </button>
                    <button
                      onClick={() => setEditing(true)}
                      className="rounded-full border border-border px-4 py-2 text-sm font-semibold transition hover:bg-cardhover"
                    >
                      Edit profile
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={onMessage}
                      className="flex h-10 w-10 items-center justify-center rounded-full border border-border transition hover:bg-cardhover"
                      title="Message"
                    >
                      <MessageSquare size={17} />
                    </button>
                    <button
                      onClick={toggleFollow}
                      className={
                        profile.follow_state !== 'none'
                          ? 'rounded-full border border-border px-4 py-2 text-sm font-semibold transition hover:border-danger hover:text-danger'
                          : 'rounded-full bg-accent px-4 py-2 text-sm font-semibold text-accentink transition hover:brightness-105'
                      }
                    >
                      {followLabel}
                    </button>
                  </div>
                )}
              </div>

              <h2 className="flex items-center gap-1.5 text-xl font-bold">
                {profile.display_name}
                {profile.is_private && (
                  <Lock size={15} className="text-faint" aria-label="Private account" />
                )}
              </h2>
              <p className="text-sm text-faint">@{profile.username}</p>

              {profile.bio && <p className="mt-2 whitespace-pre-wrap text-sm">{profile.bio}</p>}

              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted">
                {profile.location && (
                  <span className="flex items-center gap-1">
                    <MapPin size={14} className="text-faint" /> {profile.location}
                  </span>
                )}
                {profile.website && (
                  <a
                    href={websiteHref(profile.website)}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-accent hover:underline"
                  >
                    <Link2 size={14} /> {profile.website}
                  </a>
                )}
                <span className="flex items-center gap-1">
                  <CalendarDays size={14} className="text-faint" />
                  Joined {new Date(profile.created_at).toLocaleDateString([], { month: 'long', year: 'numeric' })}
                </span>
              </div>

              <div className="mt-2 flex gap-4 text-sm">
                <span>
                  <b>{profile.following_count}</b> <span className="text-faint">Following</span>
                </span>
                <span>
                  <b>{profile.followers_count}</b> <span className="text-faint">Followers</span>
                </span>
                <span>
                  <b>{profile.posts_count}</b> <span className="text-faint">Posts</span>
                </span>
              </div>
            </div>

            <div className="border-t border-border">
              {canViewPosts ? (
                <PostFeed
                  posts={posts}
                  isLoading={feed.isLoading}
                  hasMore={Boolean(feed.hasNextPage)}
                  loadingMore={feed.isFetchingNextPage}
                  onLoadMore={feed.fetchNextPage}
                  emptyText={isMe ? "You haven't posted yet." : 'No posts yet.'}
                />
              ) : (
                <div className="flex flex-col items-center gap-2 px-6 py-16 text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-card">
                    <Lock size={20} className="text-faint" />
                  </div>
                  <p className="text-sm font-semibold">This account is private</p>
                  <p className="max-w-xs text-xs text-faint">
                    {profile.follow_state === 'pending'
                      ? 'Your follow request is pending approval. You’ll see their posts once accepted.'
                      : `Follow @${profile.username} to see their posts.`}
                  </p>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <AnimatePresence>{editing && <ProfileDialog onClose={() => setEditing(false)} />}</AnimatePresence>
      <AnimatePresence>
        {showRequests && <FollowRequests onClose={() => setShowRequests(false)} />}
      </AnimatePresence>
    </div>
  )
}
