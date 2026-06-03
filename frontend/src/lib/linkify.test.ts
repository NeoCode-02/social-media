import { describe, expect, it } from 'vitest'

import { extractHashtags, extractMentions, tokenizeRichText } from './linkify'

describe('tokenizeRichText', () => {
  it('keeps plain text as a single text token', () => {
    expect(tokenizeRichText('hello world')).toEqual([{ kind: 'text', value: 'hello world' }])
  })

  it('extracts a URL before a trailing mention/hashtag', () => {
    const tokens = tokenizeRichText('check https://example.com/x @alice #fun')
    expect(tokens).toContainEqual({ kind: 'url', value: 'https://example.com/x' })
    expect(tokens).toContainEqual({ kind: 'mention', value: 'alice' })
    expect(tokens).toContainEqual({ kind: 'hashtag', value: 'fun' })
  })

  it('drops text tokens that became empty after splitting', () => {
    const tokens = tokenizeRichText('#only')
    expect(tokens).toEqual([{ kind: 'hashtag', value: 'only' }])
  })
})

describe('extractMentions / extractHashtags', () => {
  it('returns distinct lowercased values', () => {
    expect(extractMentions('Hi @Alice and @ALICE and @bob')).toEqual(['alice', 'bob'])
    expect(extractHashtags('post #One #one #TWO')).toEqual(['one', 'two'])
  })

  it('returns an empty array when there are no matches', () => {
    expect(extractMentions('no mentions here')).toEqual([])
    expect(extractHashtags('no hashtags here')).toEqual([])
  })
})
