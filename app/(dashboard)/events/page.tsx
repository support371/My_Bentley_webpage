'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Search, Filter, Download, AlertCircle, CheckCircle, Info, Clock } from 'lucide-react'

const mockEvents = [
  {
    id: 1,
    type: 'imodel_updated',
    title: 'iModel Updated',
    description: 'Central Tower iModel has been updated',
    project: 'Central Tower',
    timestamp: '2024-01-15 10:30:45',
    severity: 'info',
  },
  {
    id: 2,
    type: 'user_joined',
    title: 'User Joined',
    description: 'John Doe joined Bridge Infrastructure',
    project: 'Bridge Infrastructure',
    timestamp: '2024-01-15 10:25:12',
    severity: 'info',
  },
  {
    id: 3,
    type: 'error_occurred',
    title: 'Error Occurred',
    description: 'Synchronization failed for Road Network iModel',
    project: 'Road Network',
    timestamp: '2024-01-15 10:15:33',
    severity: 'error',
  },
  {
    id: 4,
    type: 'data_synced',
    title: 'Data Synchronized',
    description: 'Project data synchronized successfully',
    project: 'Urban Development',
    timestamp: '2024-01-15 10:05:22',
    severity: 'success',
  },
]

const severityIcons = {
  error: AlertCircle,
  success: CheckCircle,
  info: Info,
  warning: Clock,
}

const severityColors = {
  error: 'text-destructive',
  success: 'text-green-500',
  info: 'text-blue-500',
  warning: 'text-yellow-500',
}

export default function EventsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filter, setFilter] = useState('all')

  const filtered = mockEvents.filter(e =>
    (filter === 'all' || e.severity === filter) &&
    (e.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
     e.project.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Events</h1>
          <p className="text-muted-foreground mt-2">Real-time event log of all activities</p>
        </div>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Controls */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search events..."
            className="pl-10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          {['all', 'info', 'success', 'error'].map(f => (
            <Button
              key={f}
              variant={filter === f ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(f)}
              className="capitalize"
            >
              {f}
            </Button>
          ))}
        </div>
      </div>

      {/* Events List */}
      <div className="space-y-3">
        {filtered.map((event) => {
          const Icon = severityIcons[event.severity as keyof typeof severityIcons]

          return (
            <Card key={event.id} className="hover:border-primary/50 transition-colors">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <div className={`mt-1 ${severityColors[event.severity as keyof typeof severityColors]}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-medium text-foreground">{event.title}</h3>
                      <span className="text-xs px-2 py-1 rounded-full bg-muted text-muted-foreground">
                        {event.project}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">{event.description}</p>
                    <p className="text-xs text-muted-foreground/60 mt-2">{event.timestamp}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {filtered.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Info className="w-12 h-12 text-muted-foreground/30 mb-4" />
            <p className="text-muted-foreground">No events found</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
