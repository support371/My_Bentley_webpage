'use client'

import { useNotificationStore } from '@/lib/notifications'
import { CheckCircle, AlertCircle, Info, AlertTriangle, X } from 'lucide-react'
import { Button } from './ui/button'
import { cn } from '@/lib/utils'

const notificationIcons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
}

const notificationStyles = {
  success: 'bg-green-500/10 border-green-500/20 text-green-50',
  error: 'bg-red-500/10 border-red-500/20 text-red-50',
  info: 'bg-blue-500/10 border-blue-500/20 text-blue-50',
  warning: 'bg-yellow-500/10 border-yellow-500/20 text-yellow-50',
}

const notificationIconStyles = {
  success: 'text-green-400',
  error: 'text-red-400',
  info: 'text-blue-400',
  warning: 'text-yellow-400',
}

export function NotificationCenter() {
  const { notifications, removeNotification } = useNotificationStore()

  return (
    <div className="fixed top-4 right-4 z-50 space-y-3 max-w-md">
      {notifications.map((notification) => {
        const Icon = notificationIcons[notification.type]

        return (
          <div
            key={notification.id}
            className={cn(
              'rounded-lg border p-4 flex items-start gap-3 animate-in slide-in-from-right-full',
              notificationStyles[notification.type]
            )}
          >
            <Icon className={cn('w-5 h-5 mt-0.5 flex-shrink-0', notificationIconStyles[notification.type])} />

            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm">{notification.title}</p>
              <p className="text-sm opacity-90 mt-0.5">{notification.message}</p>
              {notification.action && (
                <button
                  onClick={notification.action.onClick}
                  className="text-sm font-medium mt-2 hover:underline"
                >
                  {notification.action.label}
                </button>
              )}
            </div>

            <button
              onClick={() => removeNotification(notification.id)}
              className="flex-shrink-0 opacity-50 hover:opacity-100 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
