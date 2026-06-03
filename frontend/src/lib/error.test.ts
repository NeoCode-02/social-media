import { describe, expect, it } from 'vitest'

import { apiError } from './error'

describe('apiError', () => {
  it('returns the detail string when the API sent a plain message', () => {
    expect(apiError({ response: { data: { detail: 'Email already in use' } } })).toBe(
      'Email already in use',
    )
  })

  it('falls back to a Pydantic validation error message', () => {
    expect(
      apiError({
        response: { data: { detail: [{ msg: 'value is not a valid email' }] } },
      }),
    ).toBe('value is not a valid email')
  })

  it('returns a generic message for unknown shapes', () => {
    expect(apiError(new Error('boom'))).toMatch(/something went wrong/i)
    expect(apiError(undefined)).toMatch(/something went wrong/i)
  })
})
