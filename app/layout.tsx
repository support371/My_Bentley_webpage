import type { Metadata } from 'next'
import { NotificationCenter } from '@/components/notification-center'
import './globals.css'

export const metadata: Metadata = {
  title: 'iTwin Ops',
  description: 'Engineering and construction digital operations platform',
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-foreground antialiased">
        <div className="min-h-screen">
          {children}
        </div>
        <NotificationCenter />
      </body>
    </html>
  )
}
