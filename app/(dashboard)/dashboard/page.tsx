'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { dashboardAPI, projectsAPI, eventsAPI } from '@/lib/api'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import {
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  Zap,
  Folder,
} from 'lucide-react'

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b']

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)
  const [projects, setProjects] = useState<any[]>([])
  const [recentEvents, setRecentEvents] = useState<any[]>([])

  const mockStats = {
    total_projects: 12,
    active_projects: 8,
    completed_projects: 4,
    total_events: 1243,
    events_today: 47,
    errors: 3,
  }

  const mockProjects = [
    { id: 1, name: 'Central Tower', status: 'active', progress: 75 },
    { id: 2, name: 'Bridge Infrastructure', status: 'active', progress: 45 },
    { id: 3, name: 'Urban Development', status: 'completed', progress: 100 },
    { id: 4, name: 'Road Network', status: 'active', progress: 60 },
  ]

  const mockEvents = [
    { id: 1, type: 'imodel_updated', project: 'Central Tower', timestamp: '2024-01-15 10:30' },
    { id: 2, type: 'user_joined', project: 'Bridge Infrastructure', timestamp: '2024-01-15 10:25' },
    { id: 3, type: 'data_synced', project: 'Urban Development', timestamp: '2024-01-15 10:20' },
    { id: 4, type: 'error_occurred', project: 'Road Network', timestamp: '2024-01-15 10:15' },
  ]

  const chartData = [
    { name: 'Mon', projects: 4, events: 240 },
    { name: 'Tue', projects: 3, events: 221 },
    { name: 'Wed', projects: 2, events: 229 },
    { name: 'Thu', projects: 5, events: 200 },
    { name: 'Fri', projects: 4, events: 218 },
    { name: 'Sat', projects: 3, events: 250 },
    { name: 'Sun', projects: 4, events: 210 },
  ]

  const projectStatusData = [
    { name: 'Active', value: 8 },
    { name: 'Completed', value: 4 },
  ]

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setIsLoading(true)
        // In a real app, these would be API calls
        // const statsData = await dashboardAPI.stats()
        // const projectsData = await projectsAPI.list()
        // const eventsData = await eventsAPI.list()

        setStats(mockStats)
        setProjects(mockProjects)
        setRecentEvents(mockEvents)
      } catch (error) {
        console.error('Failed to load dashboard:', error)
      } finally {
        setIsLoading(false)
      }
    }

    loadDashboard()
  }, [])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-primary/20 mb-4">
            <div className="w-4 h-4 bg-primary rounded-full animate-pulse" />
          </div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-2">Welcome back! Here&apos;s your project overview.</p>
        </div>
        <Button>+ New Project</Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Folder className="w-4 h-4" />
              Active Projects
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stats.active_projects}</div>
            <p className="text-xs text-green-500 mt-1 flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              2 more this month
            </p>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Events Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stats.events_today}</div>
            <p className="text-xs text-blue-500 mt-1">Real-time monitoring</p>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              Errors
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{stats.errors}</div>
            <p className="text-xs text-red-500 mt-1">Needs attention</p>
          </CardContent>
        </Card>

        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">{stats.completed_projects}</div>
            <p className="text-xs text-green-600 mt-1">This quarter</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Chart */}
        <Card className="lg:col-span-2 border-border/50">
          <CardHeader>
            <CardTitle>Activity Overview</CardTitle>
            <CardDescription>Projects and events over the past week</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                  }}
                />
                <Bar dataKey="projects" fill="hsl(var(--primary))" />
                <Bar dataKey="events" fill="hsl(var(--accent))" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Project Status Pie */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Project Status</CardTitle>
            <CardDescription>Distribution overview</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-center">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={projectStatusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {projectStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects and Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Projects */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Recent Projects</CardTitle>
            <CardDescription>Latest updates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {projects.map((project) => (
                <div key={project.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition">
                  <div className="flex-1">
                    <h4 className="font-medium text-foreground">{project.name}</h4>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{ width: `${project.progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">{project.progress}%</span>
                    </div>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    project.status === 'active'
                      ? 'bg-green-500/20 text-green-500'
                      : 'bg-muted text-muted-foreground'
                  }`}>
                    {project.status}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Events */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Recent Events</CardTitle>
            <CardDescription>Last 24 hours</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentEvents.map((event) => (
                <div key={event.id} className="flex items-start gap-3 p-3 rounded-lg bg-muted/30">
                  <div className={`w-2 h-2 rounded-full mt-2 ${
                    event.type === 'error_occurred' ? 'bg-destructive' : 'bg-primary'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground capitalize">{event.type.replace(/_/g, ' ')}</p>
                    <p className="text-xs text-muted-foreground">{event.project}</p>
                    <p className="text-xs text-muted-foreground/60 mt-1">{event.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
