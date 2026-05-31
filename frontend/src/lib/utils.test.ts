import { describe, expect, it } from 'vitest'

import type { Chat } from '@/api/types'
import { chatFace, initials } from './utils'

describe('initials', () => {
  it('takes up to two leading letters, uppercased', () => {
    expect(initials('Ada Lovelace')).toBe('AL')
    expect(initials('bob')).toBe('B')
    expect(initials('')).toBe('?')
  })
})

describe('chatFace', () => {
  const dm: Chat = {
    id: '1',
    type: 'dm',
    title: null,
    avatar_url: null,
    created_at: '',
    unread_count: 0,
    last_message: null,
    members: [
      { role: 'member', last_read_message_id: null, user: { id: 'me', username: 'me', display_name: 'Me', avatar_url: null } },
      { role: 'member', last_read_message_id: null, user: { id: 'u2', username: 'ada', display_name: 'Ada', avatar_url: null } },
    ],
  }

  it('shows the other participant for a DM', () => {
    const face = chatFace(dm, 'me')
    expect(face.name).toBe('Ada')
    expect(face.userId).toBe('u2')
  })

  it('shows the title for a group', () => {
    const group: Chat = { ...dm, type: 'group', title: 'Squad' }
    expect(chatFace(group, 'me').name).toBe('Squad')
  })
})
