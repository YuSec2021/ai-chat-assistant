'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/stores/useAuthStore'

export default function Home() {
  const router = useRouter()
  const { isAuthenticated, hasHydrated } = useAuthStore()
  const [hasMounted, setHasMounted] = useState(false)

  // Wait for client-side mount
  useEffect(() => {
    setHasMounted(true)
  }, [])

  useEffect(() => {
    // Only redirect after hydration is complete
    if (!hasHydrated || !hasMounted) {
      return
    }

    // Redirect to chat if authenticated, otherwise to login
    if (isAuthenticated) {
      router.push('/chat/new')
    } else {
      router.push('/login')
    }
  }, [isAuthenticated, hasHydrated, hasMounted, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
        <p className="text-slate-400">Loading...</p>
      </div>
    </div>
  )
}
