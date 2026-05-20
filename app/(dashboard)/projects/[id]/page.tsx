'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ArrowLeft, Settings, Share2, Trash2, Users, FileText, Clock } from 'lucide-react'
import Link from 'next/link'
import { StatCard } from '@/components/stat-card'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'

const mockProjectDetail = {
  id: '1',
  name: 'Central Tower',
  description: 'Urban development project in downtown area',
  status: 'active',
  progress: 75,
  team: 8,
  iModels: 3,
  dateCreated: '2024-01-10',
  dateModified: '2024-01-15',
  budget: '$2.5M',
  iModelCount: 3,
  documentCount: 47,
}

const timelineData = [
  { month: 'Jan', progress: 15 },
  { month: 'Feb', progress: 28 },
  { month: 'Mar', progress: 42 },
  { month: 'Apr', progress: 58 },
  { month: 'May', progress: 68 },
  { month: 'Jun', progress: 75 },
]

const resourceData = [
  { name: 'Team Members', value: 8 },
  { name: 'iModels', value: 3 },
  { name: 'Documents', value: 47 },
]

export default function ProjectDetailPage({ params }: { params: { id: string } }) {
  const [project] = useState(mockProjectDetail)

  return (
    <div className="space-y-6">
      {/* Header with back button */}
      <div className="flex items-center gap-4">
        <Link href="/projects">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-slate-50">{project.name}</h1>
          <p className="text-slate-400 mt-1">{project.description}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
          <Button variant="outline">
            <Settings className="w-4 h-4 mr-2" />
            Settings
          </Button>
        </div>
      </div>

      {/* Status cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Progress"
          value={`${project.progress}%`}
          variant="default"
          trend="up"
          trendValue="+5% this week"
        />
        <StatCard
          title="Team Members"
          value={project.team}
          variant="success"
          description="Active collaborators"
        />
        <StatCard
          title="iModels"
          value={project.iModels}
          variant="default"
          description="Digital twins"
        />
        <StatCard
          title="Documents"
          value="47"
          variant="default"
          description="Total files"
        />
      </div>

      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Progress and timeline */}
        <div className="lg:col-span-2 space-y-6">
          {/* Overall progress */}
          <Card className="border-slate-700 bg-slate-900/50">
            <CardHeader>
              <CardTitle>Project Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-slate-400">Overall Completion</span>
                  <span className="text-sm font-bold text-blue-400">{project.progress}%</span>
                </div>
                <div className="h-3 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-blue-600"
                    style={{ width: `${project.progress}%` }}
                  />
                </div>
              </div>

              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={timelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgb(30 41 59)" />
                  <XAxis dataKey="month" stroke="rgb(148 163 184)" />
                  <YAxis stroke="rgb(148 163 184)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgb(15 23 42)',
                      border: '1px solid rgb(30 41 59)',
                      borderRadius: '6px',
                    }}
                  />
                  <Line type="monotone" dataKey="progress" stroke="rgb(59 130 246)" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* iModels */}
          <Card className="border-slate-700 bg-slate-900/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>iModels</CardTitle>
              <Button size="sm">+ Add iModel</Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-4 p-3 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition">
                    <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                      <FileText className="w-5 h-5 text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-50">iModel {i}</p>
                      <p className="text-sm text-slate-500">Updated 2 days ago</p>
                    </div>
                    <span className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-400">Active</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Project Info */}
          <Card className="border-slate-700 bg-slate-900/50">
            <CardHeader>
              <CardTitle className="text-base">Project Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <p className="text-slate-500 mb-1">Status</p>
                <span className="inline-block px-3 py-1 rounded-full bg-green-500/20 text-green-400 font-medium">
                  {project.status}
                </span>
              </div>
              <div className="border-t border-slate-800 pt-4">
                <p className="text-slate-500 mb-1">Budget</p>
                <p className="font-semibold text-slate-50">{project.budget}</p>
              </div>
              <div className="border-t border-slate-800 pt-4">
                <p className="text-slate-500 mb-1">Created</p>
                <p className="font-semibold text-slate-50">{project.dateCreated}</p>
              </div>
              <div className="border-t border-slate-800 pt-4">
                <p className="text-slate-500 mb-1">Last Modified</p>
                <p className="font-semibold text-slate-50">{project.dateModified}</p>
              </div>
            </CardContent>
          </Card>

          {/* Team Members */}
          <Card className="border-slate-700 bg-slate-900/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Team Members</CardTitle>
              <Button size="sm" variant="ghost">
                <Users className="w-4 h-4" />
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-xs font-medium text-blue-400">
                      U{i}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-50 truncate">User {i}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
