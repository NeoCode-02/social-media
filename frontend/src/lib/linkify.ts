/**
 * Shared post/message text parser. Produces a flat list of typed tokens
 * that RichText and any future renderer (e.g. a message preview card) can
 * consume. Centralizing the regexes here means a hashtag spec change only
 * needs to be applied in one place.
 */

export type RichToken =
  | { kind: 'text'; value: string }
  | { kind: 'url'; value: string }
  | { kind: 'hashtag'; value: string }
  | { kind: 'mention'; value: string }

const TOKEN =
  /(https?:\/\/[^\s]+|#\w{1,50}|@\w{3,32})/g

/**
 * Split plain text into typed tokens. URLs come first so a trailing
 * " #tag" / "@user" doesn't get eaten by the URL match.
 */
export function tokenizeRichText(text: string): RichToken[] {
  const parts = text.split(TOKEN)
  const out: RichToken[] = []
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i]
    if (i % 2 === 1) {
      if (part.startsWith('http')) out.push({ kind: 'url', value: part })
      else if (part.startsWith('#')) out.push({ kind: 'hashtag', value: part.slice(1) })
      else if (part.startsWith('@')) out.push({ kind: 'mention', value: part.slice(1) })
      else out.push({ kind: 'text', value: part })
    } else if (part) {
      out.push({ kind: 'text', value: part })
    }
  }
  return out
}

/** Convenience: extract distinct lowercase hashtags. */
export function extractHashtags(text: string): string[] {
  const seen = new Set<string>()
  for (const t of tokenizeRichText(text)) {
    if (t.kind === 'hashtag') seen.add(t.value.toLowerCase())
  }
  return [...seen]
}

/** Convenience: extract distinct lowercase usernames (no leading @). */
export function extractMentions(text: string): string[] {
  const seen = new Set<string>()
  for (const t of tokenizeRichText(text)) {
    if (t.kind === 'mention') seen.add(t.value.toLowerCase())
  }
  return [...seen]
}
