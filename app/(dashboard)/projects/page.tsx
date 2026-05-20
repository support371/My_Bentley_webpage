'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Search, Plus, MoreVertical, Edit2, Trash2 } from 'lucide-react'

const mockProjects = [
  {
    id: 1,
    name: 'Central Tower',
    description: 'Urban development project',
    status: 'active',
    progress: 75,
    team: 8,
    date: '2024-01-10',
  },
  {
    id: 2,
    name: 'Bridge Infrastructure',
    description: 'Highway bridge construction',
    status: 'active',
    progress: 45,
    team: 5,
    date: '2024-01-12',
  },
  {
    id: 3,
    name: 'Urban Development',
    description: 'City planning phase',
    status: 'completed',
    progress: 100,
    team: 12,
    date: '2024-01-05',
  },
]

export default function ProjectsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [projects] = useState(mockProjects)

  const filtered = projects.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Projects</h1>
          <p className="text-muted-foreground mt-2">Manage all your iTwin projects</p>
        </div>
        <Button size="lg">
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search projects..."
          className="pl-10"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((project) => (
          <Card key={project.id} className="hover:border-primary/50 transition-colors group">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{project.name}</CardTitle>
                  <CardDescription className="mt-1">{project.description}</CardDescription>
                </div>
                <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Progress Bar */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-muted-foreground">Progress</span>
                  <span className="text-xs font-bold text-primary">{project.progress}%</span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${project.progress}%` }}
                  />
                </div>
              </div>

              {/* Meta */}
              <div className="flex items-center justify-between pt-2 border-t border-border/30">
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  project.status === 'active'
                    ? 'bg-green-500/20 text-green-500'
                    : 'bg-muted text-muted-foreground'
                }`}>
                  {project.status}
                </span>
                <span className="text-xs text-muted-foreground">{project.team} team members</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filtered.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="w-12 h-12 rounded-lg bg-muted/50 flex items-center justify-center mb-4">
              <Search className="w-6 h-6 text-muted-foreground" />
            </div>
            <p className="text-muted-foreground">No projects found</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
