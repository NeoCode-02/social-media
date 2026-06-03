import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { getUserByUsername } from '@/api/users'
import { tokenizeRichText } from '@/lib/linkify'
import { cn } from '@/lib/utils'

/**
 * Render post/message text with clickable URLs, #hashtags, and @mentions.
 * Text is rendered as React string children (never innerHTML) so it stays
 * XSS-safe — React escapes everything.
 *
 * Mentions resolve to a real user id via the by-username endpoint, then
 * link to /u/:userId. The id is cached in react-query, so each username
 * costs at most one HTTP request for the lifetime of the session.
 */
export function RichText({ text }: { text: string }) {
  const tokens = tokenizeRichText(text)
  return (
    <>
      {tokens.map((t, i) => {
        if (t.kind === 'hashtag') {
          return (
            <Link
              key={i}
              to={`/tag/${t.value.toLowerCase()}`}
              onClick={(e) => e.stopPropagation()}
              className="text-accent hover:underline"
            >
              #{t.value}
            </Link>
          )
        }
        if (t.kind === 'mention') {
          return <MentionLink key={i} username={t.value} />
        }
        if (t.kind === 'url') {
          return (
            <a
              key={i}
              href={t.value}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="text-accent break-all hover:underline"
            >
              {t.value}
            </a>
          )
        }
        return <span key={i}>{t.value}</span>
      })}
    </>
  )
}

function MentionLink({ username }: { username: string }) {
  // Background-resolve username → userId so the link goes somewhere real.
  // The id stays in react-query's cache keyed by username, so multiple
  // mentions to the same user share one fetch.
  const { data } = useQuery({
    queryKey: ['userByUsername', username.toLowerCase()],
    queryFn: () => getUserByUsername(username).then((r) => r.data),
    retry: 0,
    staleTime: 5 * 60_000,
  })
  const href = data ? `/u/${data.id}` : `/u/by-username/${encodeURIComponent(username)}`
  return (
    <Link
      to={href}
      onClick={(e) => e.stopPropagation()}
      className={cn('text-accent hover:underline')}
    >
      @{username}
    </Link>
  )
}
