import { Link } from 'react-router-dom'

// Split on #hashtags and @mentions. Capturing groups keep the delimiters.
const TOKEN = /(#\w{1,50}|@\w{3,32})/g

/**
 * Render post/message text with clickable #hashtags and @mentions.
 * Text is rendered as React string children (never innerHTML) so it stays
 * XSS-safe — React escapes everything.
 */
export function RichText({ text }: { text: string }) {
  const parts = text.split(TOKEN)
  return (
    <>
      {parts.map((part, i) => {
        if (i % 2 === 1 && part.startsWith('#')) {
          const tag = part.slice(1)
          return (
            <Link
              key={i}
              to={`/tag/${tag.toLowerCase()}`}
              onClick={(e) => e.stopPropagation()}
              className="text-accent hover:underline"
            >
              {part}
            </Link>
          )
        }
        if (i % 2 === 1 && part.startsWith('@')) {
          const username = part.slice(1)
          return (
            <Link
              key={i}
              to={`/u/@${username}`}
              onClick={(e) => e.stopPropagation()}
              className="text-accent hover:underline"
            >
              {part}
            </Link>
          )
        }
        return part
      })}
    </>
  )
}
