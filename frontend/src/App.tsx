import { useEffect } from 'react'
import { Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom'

import { setOnAuthFail } from '@/api/client'
import { bootstrapSession } from '@/api/session'
import { getUserByUsername } from '@/api/users'
import { AppShell } from '@/components/AppShell'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { FullScreenLoader } from '@/components/FullScreenLoader'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { ChatLayout } from '@/features/chat/ChatLayout'
import { Conversation } from '@/features/chat/Conversation'
import { EmptyConversation } from '@/features/chat/EmptyConversation'
import { ExplorePage } from '@/features/explore/ExplorePage'
import { FeedPage } from '@/features/feed/FeedPage'
import { HashtagPage } from '@/features/feed/HashtagPage'
import { PostThread } from '@/features/feed/PostThread'
import { ProfilePage } from '@/features/feed/ProfilePage'
import { AdminPage } from '@/features/admin/AdminPage'
import { NotificationsPage } from '@/features/notifications/NotificationsPage'
import { AuthCallbackPage } from '@/pages/AuthCallbackPage'
import { LoginPage } from '@/pages/LoginPage'
import { RegisterPage } from '@/pages/RegisterPage'
import { VerifyPage } from '@/pages/VerifyPage'
import { useAuth } from '@/store/auth'

function UsernameRedirect() {
  // /u/by-username/:username — resolves a username to a user id, then
  // redirects to the canonical /u/:userId. Used as a fallback for mention
  // links that haven't been resolved to an id yet.
  const { username = '' } = useParams()
  const navigate = useNavigate()
  useEffect(() => {
    let cancelled = false
    void getUserByUsername(username)
      .then((r) => {
        if (!cancelled) navigate(`/u/${r.data.id}`, { replace: true })
      })
      .catch(() => {
        if (!cancelled) navigate('/feed', { replace: true })
      })
    return () => {
      cancelled = true
    }
  }, [username, navigate])
  return <FullScreenLoader />
}

function App() {
  const clear = useAuth((s) => s.clear)

  useEffect(() => {
    setOnAuthFail(() => clear())
    void bootstrapSession()
  }, [clear])

  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/verify" element={<VerifyPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route index element={<Navigate to="/feed" replace />} />
            <Route path="feed" element={<FeedPage />} />
            <Route path="explore" element={<ExplorePage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="admin" element={<AdminPage />} />
            <Route path="tag/:tag" element={<HashtagPage />} />
            <Route path="post/:postId" element={<PostThread />} />
            <Route path="u/:userId" element={<ProfilePage />} />
            <Route path="u/by-username/:username" element={<UsernameRedirect />} />
            <Route element={<ChatLayout />}>
              <Route path="messages" element={<EmptyConversation />} />
              <Route path="c/:chatId" element={<Conversation />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/feed" replace />} />
      </Routes>
    </ErrorBoundary>
  )
}

export default App
