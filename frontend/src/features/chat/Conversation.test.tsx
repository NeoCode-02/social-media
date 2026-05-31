import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuth } from '@/store/auth'
import { useRealtimeStore } from '@/store/realtime'

const { chat } = vi.hoisted(() => ({
  chat: {
    id: 'c1',
    type: 'dm',
    title: null,
    avatar_url: null,
    created_at: new Date().toISOString(),
    unread_count: 0,
    last_message: null,
    members: [
      { role: 'member', last_read_message_id: null, user: { id: 'me', username: 'me', display_name: 'Me', avatar_url: null } },
      { role: 'member', last_read_message_id: null, user: { id: 'u2', username: 'ada', display_name: 'Ada', avatar_url: null } },
    ],
  },
}))

vi.mock('@/api/chats', () => ({
  getChat: vi.fn().mockResolvedValue({ data: chat }),
  listMessages: vi.fn().mockResolvedValue({ data: { messages: [], next_cursor: null } }),
  markRead: vi.fn().mockResolvedValue({ data: {} }),
  sendMessage: vi.fn(),
}))

import { Conversation } from './Conversation'

describe('Conversation', () => {
  beforeEach(() => {
    useAuth.setState({
      user: { id: 'me', username: 'me', display_name: 'Me', avatar_url: null, email: 'me@example.com', email_verified: true, created_at: '' },
      status: 'authed',
    })
    useRealtimeStore.setState({ online: {}, typing: {} })
  })

  it('renders without crashing (stable store selectors)', async () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter initialEntries={['/c/c1']}>
          <Routes>
            <Route path="/c/:chatId" element={<Conversation />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )
    expect(await screen.findByText('Ada')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText(/say hello/i)).toBeInTheDocument())
  })
})
