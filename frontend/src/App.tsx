import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { setOnAuthFail } from '@/api/client'
import { bootstrapSession } from '@/api/session'
import { AppShell } from '@/components/AppShell'
import { ErrorBoundary } from '@/components/ErrorBoundary'
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
