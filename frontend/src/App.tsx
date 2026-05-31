import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { setOnAuthFail } from '@/api/client'
import { bootstrapSession } from '@/api/session'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { ChatLayout } from '@/features/chat/ChatLayout'
import { Conversation } from '@/features/chat/Conversation'
import { EmptyConversation } from '@/features/chat/EmptyConversation'
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
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/verify" element={<VerifyPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<ChatLayout />}>
          <Route index element={<EmptyConversation />} />
          <Route path="c/:chatId" element={<Conversation />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
