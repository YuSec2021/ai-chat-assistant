"use client"

import { cn } from '@/lib/utils'

export default function WelcomeScreen() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <div className="max-w-2xl text-center space-y-6">
        {/* Logo or Icon */}
        <div className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
          <span className="text-3xl">🤖</span>
        </div>

        {/* Welcome Text */}
        <div>
          <h1 className="text-3xl font-bold mb-3">
            Welcome to AI Chat Assistant
          </h1>
          <p className="text-muted-foreground text-lg">
            Start a new conversation or select one from the sidebar
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left max-w-3xl mx-auto">
          <div className="p-4 rounded-lg bg-secondary border border-border">
            <div className="font-semibold mb-2">💬 Smart Chat</div>
            <p className="text-sm text-muted-foreground">
              Natural conversations with AI assistant
            </p>
          </div>
          <div className="p-4 rounded-lg bg-secondary border border-border">
            <div className="font-semibold mb-2">🎯 Agent Routing</div>
            <p className="text-sm text-muted-foreground">
              Automatic task routing to specialized agents
            </p>
          </div>
          <div className="p-4 rounded-lg bg-secondary border border-border">
            <div className="font-semibold mb-2">📎 File Support</div>
            <p className="text-sm text-muted-foreground">
              Upload PDFs, images, and more for analysis
            </p>
          </div>
        </div>

        {/* Call to Action */}
        <div className="pt-4">
          <p className="text-sm text-muted-foreground">
            Click "New chat" in the sidebar to get started
          </p>
        </div>
      </div>
    </div>
  )
}
