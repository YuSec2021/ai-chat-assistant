import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface ChatMainProps {
  children: ReactNode
  className?: string
}

export default function ChatMain({ children, className }: ChatMainProps) {
  return (
    <div className={cn("flex-1 flex flex-col min-w-0", className)}>
      {children}
    </div>
  )
}
