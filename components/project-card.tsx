'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { MoreVertical, Edit2, Trash2, ArrowRight } from 'lucide-react'
import Link from 'next/link'

interface ProjectCardProps {
  id: string | number
  name: string
  description: string
  status: 'active' | 'completed' | 'paused'
  progress: number
  team: number
  dateModified: string
  iModels?: number
}

export function ProjectCard({
  id,
  name,
  description,
  status,
  progress,
  team,
  dateModified,
  iModels = 0,
}: ProjectCardProps) {
  const statusColors = {
    active: 'bg-green-500/20 text-green-500',
    completed: 'bg-blue-500/20 text-blue-500',
    paused: 'bg-yellow-500/20 text-yellow-500',
  }

  return (
    <Card className="hover:border-blue-500/50 transition-all group cursor-pointer">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <Link href={`/projects/${id}`}>
              <CardTitle className="text-lg hover:text-blue-400 transition">{name}</CardTitle>
            </Link>
            <CardDescription className="mt-1">{description}</CardDescription>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="opacity-0 group-hover:opacity-100 transition"
          >
            <MoreVertical className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Progress Bar */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-400">Progress</span>
            <span className="text-xs font-bold text-blue-400">{progress}%</span>
          </div>
          <div className="h-2 rounded-full bg-slate-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Meta Info */}
        <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800">
          <div className="text-center">
            <span className="text-xs text-slate-500">Team</span>
            <p className="text-sm font-semibold text-slate-200">{team}</p>
          </div>
          <div className="text-center">
            <span className="text-xs text-slate-500">iModels</span>
            <p className="text-sm font-semibold text-slate-200">{iModels}</p>
          </div>
          <div className="text-center">
            <span className={`inline-block text-xs px-2 py-1 rounded-full font-medium ${statusColors[status]}`}>
              {status}
            </span>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800">
          <span className="text-xs text-slate-500">{dateModified}</span>
          <Link href={`/projects/${id}`}>
            <Button variant="ghost" size="sm" className="text-blue-400 hover:text-blue-300">
              View <ArrowRight className="w-3 h-3 ml-1" />
            </Button>
          </Link>
        </div>
      </CardContent>
    </Card>
  )
}
