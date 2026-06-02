import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  BadgeCheck,
  Ban,
  Loader2,
  ShieldCheck,
  Trash2,
  UserCog,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  adminBan,
  adminDeletePost,
  adminDeleteUser,
  adminDemote,
  adminDismissReport,
  adminListPosts,
  adminListReports,
  adminListUsers,
  adminPromote,
  adminResolveReport,
  adminStats,
  adminUnban,
  adminVerify,
} from '@/api/admin'
import type { AdminUser, Post, Report } from '@/api/types'
import { Avatar } from '@/components/Avatar'
import { formatRelative } from '@/lib/utils'
import { useAuth } from '@/store/auth'

type Tab = 'dashboard' | 'users' | 'posts' | 'reports'
const TABS: Tab[] = ['dashboard', 'users', 'posts', 'reports']

export function AdminPage() {
  const me = useAuth((s) => s.user)
  const navigate = useNavigate()
  const [tab, setTab] = useState<Tab>('dashboard')

  // Guard: non-admins never see the panel.
  useEffect(() => {
    if (me && !me.is_admin) navigate('/feed', { replace: true })
  }, [me, navigate])
  if (!me?.is_admin) return null

  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col border-x border-border">
      <header className="sticky top-0 z-10 border-b border-border bg-bg/80 px-4 pt-3 backdrop-blur">
        <h1 className="mb-2 flex items-center gap-2 text-lg font-semibold">
          <ShieldCheck size={20} className="text-accent" /> Admin
        </h1>
        <nav className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-t-lg px-3 py-2 text-sm font-medium capitalize transition ${
                tab === t ? 'border-b-2 border-accent text-text' : 'text-faint hover:text-text'
              }`}
            >
              {t}
            </button>
          ))}
        </nav>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === 'dashboard' && <Dashboard />}
        {tab === 'users' && <Users />}
        {tab === 'posts' && <Posts />}
        {tab === 'reports' && <Reports />}
      </div>
    </div>
  )
}

function Loading() {
  return (
    <div className="flex justify-center py-10 text-faint">
      <Loader2 size={20} className="animate-spin" />
    </div>
  )
}

// --- Dashboard --------------------------------------------------------------

function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ['adminStats'], queryFn: () => adminStats().then((r) => r.data) })
  if (isLoading || !data) return <Loading />
  const cards: [string, number][] = [
    ['Total users', data.total_users],
    ['Total posts', data.total_posts],
    ['New users today', data.new_users_today],
    ['New posts today', data.new_posts_today],
    ['Banned', data.banned_users],
    ['Private accounts', data.private_accounts],
    ['Admins', data.admins],
    ['Open reports', data.open_reports],
  ]
  return (
    <div className="grid grid-cols-2 gap-3 p-4 sm:grid-cols-4">
      {cards.map(([label, n]) => (
        <div key={label} className="rounded-2xl border border-border bg-card p-4">
          <p className="text-2xl font-bold">{n}</p>
          <p className="text-xs text-faint">{label}</p>
        </div>
      ))}
    </div>
  )
}

// --- Users ------------------------------------------------------------------

function Badge({ text, tone }: { text: string; tone: string }) {
  return <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${tone}`}>{text}</span>
}

function Users() {
  const qc = useQueryClient()
  const meId = useAuth((s) => s.user?.id)
  const [raw, setRaw] = useState('')
  const [q, setQ] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setQ(raw.trim()), 300)
    return () => clearTimeout(t)
  }, [raw])

  const query = useInfiniteQuery({
    queryKey: ['adminUsers', q],
    queryFn: ({ pageParam }) => adminListUsers(q, pageParam ? Number(pageParam) : 0).then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  })
  const users = (query.data?.pages ?? []).flatMap((p) => p.users)
  const invalidate = () => qc.invalidateQueries({ queryKey: ['adminUsers'] })

  const act = useMutation({
    mutationFn: ({ fn, id }: { fn: (id: string) => Promise<unknown>; id: string }) => fn(id),
    onSuccess: invalidate,
  })

  return (
    <div>
      <div className="p-4">
        <input
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          placeholder="Search by name, @username or email"
          className="w-full rounded-full border border-border bg-card px-4 py-2.5 text-sm outline-none focus:border-violet/50"
        />
      </div>
      {query.isLoading ? (
        <Loading />
      ) : (
        <ul className="divide-y divide-border">
          {users.map((u: AdminUser) => (
            <li key={u.id} className="flex items-center gap-3 px-4 py-3">
              <Avatar name={u.display_name} src={u.avatar_url} userId={u.id} size={40} />
              <div className="min-w-0 flex-1">
                <p className="flex items-center gap-1.5 truncate text-sm font-semibold">
                  {u.display_name}
                  {u.is_admin && <Badge text="ADMIN" tone="bg-accent/15 text-accent" />}
                  {u.is_banned && <Badge text="BANNED" tone="bg-danger/15 text-danger" />}
                  {!u.email_verified && <Badge text="UNVERIFIED" tone="bg-card text-faint" />}
                </p>
                <p className="truncate text-xs text-faint">@{u.username} · {u.email}</p>
              </div>
              {u.id !== meId && (
                <div className="flex shrink-0 items-center gap-1">
                  <IconBtn
                    title={u.is_banned ? 'Unban' : 'Ban'}
                    danger={!u.is_banned}
                    onClick={() => act.mutate({ fn: u.is_banned ? adminUnban : adminBan, id: u.id })}
                  >
                    <Ban size={15} />
                  </IconBtn>
                  <IconBtn
                    title={u.is_admin ? 'Demote' : 'Promote to admin'}
                    onClick={() => act.mutate({ fn: u.is_admin ? adminDemote : adminPromote, id: u.id })}
                  >
                    <UserCog size={15} />
                  </IconBtn>
                  {!u.email_verified && (
                    <IconBtn title="Force-verify" onClick={() => act.mutate({ fn: adminVerify, id: u.id })}>
                      <BadgeCheck size={15} />
                    </IconBtn>
                  )}
                  <IconBtn
                    title="Delete account"
                    danger
                    onClick={() => {
                      if (confirm(`Delete @${u.username}? This cannot be undone.`)) {
                        act.mutate({ fn: adminDeleteUser, id: u.id })
                      }
                    }}
                  >
                    <Trash2 size={15} />
                  </IconBtn>
                </div>
              )}
            </li>
          ))}
          <LoadMore query={query} />
        </ul>
      )}
    </div>
  )
}

function IconBtn({
  title,
  onClick,
  danger,
  children,
}: {
  title: string
  onClick: () => void
  danger?: boolean
  children: React.ReactNode
}) {
  return (
    <button
      title={title}
      onClick={onClick}
      className={`flex h-8 w-8 items-center justify-center rounded-full text-muted transition hover:bg-cardhover ${
        danger ? 'hover:text-danger' : 'hover:text-accent'
      }`}
    >
      {children}
    </button>
  )
}

// --- Posts ------------------------------------------------------------------

function Posts() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [raw, setRaw] = useState('')
  const [q, setQ] = useState('')
  useEffect(() => {
    const t = setTimeout(() => setQ(raw.trim()), 300)
    return () => clearTimeout(t)
  }, [raw])

  const query = useInfiniteQuery({
    queryKey: ['adminPosts', q],
    queryFn: ({ pageParam }) => adminListPosts(q, pageParam).then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  })
  const posts = (query.data?.pages ?? []).flatMap((p) => p.posts)
  const del = useMutation({
    mutationFn: (id: string) => adminDeletePost(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['adminPosts'] }),
  })

  return (
    <div>
      <div className="p-4">
        <input
          value={raw}
          onChange={(e) => setRaw(e.target.value)}
          placeholder="Search post text"
          className="w-full rounded-full border border-border bg-card px-4 py-2.5 text-sm outline-none focus:border-violet/50"
        />
      </div>
      {query.isLoading ? (
        <Loading />
      ) : (
        <ul className="divide-y divide-border">
          {posts.map((p: Post) => (
            <li key={p.id} className="flex items-start gap-3 px-4 py-3">
              <Avatar name={p.author.display_name} src={p.author.avatar_url} size={36} />
              <button onClick={() => navigate(`/post/${p.id}`)} className="min-w-0 flex-1 text-left">
                <p className="truncate text-sm font-semibold">
                  {p.author.display_name} <span className="text-faint">@{p.author.username}</span>
                </p>
                <p className="line-clamp-2 text-sm text-muted">{p.text ?? '(media / no text)'}</p>
                <p className="mt-0.5 text-[11px] text-faint">
                  {formatRelative(p.created_at)} · {p.like_count} likes · {p.reply_count} replies
                </p>
              </button>
              <IconBtn
                title="Delete post"
                danger
                onClick={() => {
                  if (confirm('Delete this post?')) del.mutate(p.id)
                }}
              >
                <Trash2 size={15} />
              </IconBtn>
            </li>
          ))}
          <LoadMore query={query} />
        </ul>
      )}
    </div>
  )
}

// --- Reports ----------------------------------------------------------------

function Reports() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [status, setStatus] = useState<'open' | 'resolved' | 'dismissed'>('open')

  const query = useInfiniteQuery({
    queryKey: ['adminReports', status],
    queryFn: ({ pageParam }) => adminListReports(status, pageParam).then((r) => r.data),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last) => last.next_cursor ?? undefined,
  })
  const reports = (query.data?.pages ?? []).flatMap((p) => p.reports)
  const invalidate = () => qc.invalidateQueries({ queryKey: ['adminReports'] })
  const resolve = useMutation({ mutationFn: (id: string) => adminResolveReport(id), onSuccess: invalidate })
  const dismiss = useMutation({ mutationFn: (id: string) => adminDismissReport(id), onSuccess: invalidate })

  return (
    <div>
      <div className="flex gap-1 p-4">
        {(['open', 'resolved', 'dismissed'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize transition ${
              status === s ? 'bg-accent text-accentink' : 'border border-border text-muted hover:bg-cardhover'
            }`}
          >
            {s}
          </button>
        ))}
      </div>
      {query.isLoading ? (
        <Loading />
      ) : reports.length === 0 ? (
        <p className="px-4 py-10 text-center text-sm text-faint">No {status} reports.</p>
      ) : (
        <ul className="divide-y divide-border">
          {reports.map((r: Report) => (
            <li key={r.id} className="px-4 py-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-faint">
                  <span className="font-semibold text-muted">@{r.reporter.username}</span> reported a{' '}
                  {r.target_type} · {formatRelative(r.created_at)}
                </span>
                {status === 'open' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => resolve.mutate(r.id)}
                      className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-accentink"
                    >
                      Resolve
                    </button>
                    <button
                      onClick={() => dismiss.mutate(r.id)}
                      className="rounded-full border border-border px-3 py-1 text-xs font-semibold"
                    >
                      Dismiss
                    </button>
                  </div>
                )}
              </div>
              {r.reason && <p className="mt-1 text-sm">“{r.reason}”</p>}
              {r.post && (
                <button
                  onClick={() => navigate(`/post/${r.post!.id}`)}
                  className="mt-2 block w-full rounded-xl border border-border bg-card p-2 text-left text-sm text-muted hover:bg-cardhover"
                >
                  {r.post.deleted_at ? '(post deleted)' : (r.post.text ?? '(media)')}
                </button>
              )}
              {r.target_user && (
                <button
                  onClick={() => navigate(`/u/${r.target_user!.id}`)}
                  className="mt-2 text-sm text-accent hover:underline"
                >
                  @{r.target_user.username}
                </button>
              )}
            </li>
          ))}
          <LoadMore query={query} />
        </ul>
      )}
    </div>
  )
}

// --- shared -----------------------------------------------------------------

interface InfiniteLike {
  hasNextPage: boolean
  isFetchingNextPage: boolean
  fetchNextPage: () => void
}

function LoadMore({ query }: { query: InfiniteLike }) {
  if (!query.hasNextPage) return null
  return (
    <li className="p-3 text-center">
      <button
        onClick={() => query.fetchNextPage()}
        disabled={query.isFetchingNextPage}
        className="text-sm text-accent hover:underline disabled:opacity-50"
      >
        {query.isFetchingNextPage ? 'Loading…' : 'Load more'}
      </button>
    </li>
  )
}
