import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Link2, MapPin, MessageSquare, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { createDm } from '@/api/chats'
import { getUser } from '@/api/users'
import { Avatar } from '@/components/Avatar'
import { Button } from '@/components/Button'
import { useAuth } from '@/store/auth'

interface Props {
  userId: string
  onClose: () => void
}

function websiteHref(raw: string): string {
  return /^https?:\/\//i.test(raw) ? raw : `https://${raw}`
}

export function ProfileView({ userId, onClose }: Props) {
  const me = useAuth((s) => s.user)
  const navigate = useNavigate()
  const { data: profile, isLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: async () => (await getUser(userId)).data,
  })

  async function onMessage() {
    const { data } = await createDm(userId)
    onClose()
    navigate(`/c/${data.id}`)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 10 }}
        transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm overflow-hidden rounded-3xl border border-border bg-elev shadow-soft"
      >
        <div className="relative h-20 bg-gradient-to-br from-accent/30 via-violet/20 to-transparent">
          <button
            onClick={onClose}
            className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-full bg-black/20 text-white/80 transition hover:bg-black/30 hover:text-white"
          >
            <X size={16} />
          </button>
        </div>

        <div className="px-6 pb-6">
          {isLoading || !profile ? (
            <div className="flex h-40 items-center justify-center">
              <span className="h-7 w-7 animate-spin rounded-full border-2 border-border border-t-accent" />
            </div>
          ) : (
            <>
              <div className="-mt-10 mb-3">
                <div className="inline-block rounded-full ring-4 ring-elev">
                  <Avatar
                    name={profile.display_name}
                    src={profile.avatar_url}
                    userId={profile.id}
                    showPresence
                    size={76}
                  />
                </div>
              </div>

              <h2 className="text-lg font-semibold">{profile.display_name}</h2>
              <p className="text-sm text-faint">@{profile.username}</p>

              {profile.bio && (
                <p className="mt-3 whitespace-pre-wrap text-sm text-text">{profile.bio}</p>
              )}

              <div className="mt-3 space-y-1.5 text-sm text-muted">
                {profile.location && (
                  <p className="flex items-center gap-2">
                    <MapPin size={14} className="text-faint" /> {profile.location}
                  </p>
                )}
                {profile.website && (
                  <p className="flex items-center gap-2">
                    <Link2 size={14} className="text-faint" />
                    <a
                      href={websiteHref(profile.website)}
                      target="_blank"
                      rel="noreferrer"
                      className="truncate text-accent hover:underline"
                    >
                      {profile.website}
                    </a>
                  </p>
                )}
              </div>

              {me?.id !== profile.id && (
                <Button onClick={onMessage} className="mt-5 w-full">
                  <MessageSquare size={16} /> Message
                </Button>
              )}
            </>
          )}
        </div>
      </motion.div>
    </motion.div>
  )
}
