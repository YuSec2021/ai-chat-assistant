"use client"

import { useState, useEffect } from 'react'
import { useTheme } from 'next-themes'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ChatHeaderProps {
  conversation?: {
    id: string
    title: string
  } | null
}

export default function ChatHeader({ conversation }: ChatHeaderProps) {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return null
  }

  const toggleTheme = () => {
    if (theme === 'light') {
      setTheme('dark')
    } else if (theme === 'dark') {
      setTheme('system')
    } else {
      setTheme('light')
    }
  }

  return (
    <div className="h-14 border-b border-border flex items-center justify-between px-6">
      <h1 className="text-base font-semibold truncate">
        {conversation?.title || 'AI Chat Assistant'}
      </h1>
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleTheme}
        title={`Current theme: ${theme}`}
      >
        {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </Button>
    </div>
  )
}
