'use client'

import { useAuthStore } from '@/lib/store'
import { Button } from './ui/button'
import { useRouter } from 'next/navigation'
import { Bell, Settings, LogOut, User } from 'lucide-react'
import { useState } from 'react'

export function Header() {
  const { user, logout } = useAuthStore()
  const router = useRouter()
  const [showUserMenu, setShowUserMenu] = useState(false)

  const handleLogout = () => {
    logout()
    router.push('/auth/login')
  }

  return (
    <header className="border-b border-border/30 bg-card/50 backdrop-blur-sm sticky top-0 z-30">
      <div className="flex items-center justify-between h-16 px-4 md:px-8 gap-4">
        <div className="flex-1" />

        <div className="flex items-center gap-4">
          {/* Notifications */}
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
            <Bell className="w-5 h-5" />
          </Button>

          {/* Settings */}
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
            <Settings className="w-5 h-5" />
          </Button>

          {/* User menu */}
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 text-foreground"
            >
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <User className="w-4 h-4 text-primary" />
              </div>
              <span className="hidden sm:inline text-sm font-medium">{user?.name || 'User'}</span>
            </Button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 rounded-md border border-border bg-card shadow-lg py-1 z-50">
                <button className="w-full text-left px-4 py-2 text-sm text-foreground hover:bg-muted/50">
                  Profile Settings
                </button>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-4 py-2 text-sm text-destructive hover:bg-destructive/10 flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
