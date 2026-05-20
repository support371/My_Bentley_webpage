'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Plus,
  Search,
  Filter,
  Download,
  Cloud,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap,
} from 'lucide-react'

const mockIModels = [
  {
    id: 1,
    name: 'Central Tower - Structure',
    project: 'Central Tower',
    status: 'synced',
    size: '245.3 MB',
    lastSync: '2024-01-15 10:30',
    version: 'v2.1.0',
    elements: 15234,
  },
  {
    id: 2,
    name: 'Bridge Infrastructure - Geometry',
    project: 'Bridge Infrastructure',
    status: 'syncing',
    size: '156.8 MB',
    lastSync: 'In progress...',
    version: 'v1.5.0',
    elements: 8956,
  },
  {
    id: 3,
    name: 'Urban Development - Master Plan',
    project: 'Urban Development',
    status: 'error',
    size: '512.1 MB',
    lastSync: '2024-01-14 15:45',
    version: 'v3.0.0',
    elements: 32145,
  },
]

const statusIcons = {
  synced: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10' },
  syncing: { icon: Zap, color: 'text-blue-400', bg: 'bg-blue-500/10' },
  error: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/10' },
}

export default function IModelsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [filter, setFilter] = useState('all')

  const filtered = mockIModels.filter((imodel) =>
    imodel.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    imodel.project.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-50">iModels</h1>
          <p className="text-slate-400 mt-2">Manage your digital twins and synchronized models</p>
        </div>
        <Button size="lg">
          <Plus className="w-4 h-4 mr-2" />
          New iModel
        </Button>
      </div>

      {/* Controls */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input
            placeholder="Search iModels..."
            className="pl-10 bg-slate-900 border-slate-700"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          {['all', 'synced', 'syncing', 'error'].map((f) => (
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

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-slate-700 bg-slate-900/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Total iModels</p>
                <p className="text-2xl font-bold text-slate-50 mt-1">{mockIModels.length}</p>
              </div>
              <Cloud className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-700 bg-slate-900/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Synced</p>
                <p className="text-2xl font-bold text-green-400 mt-1">2</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-slate-700 bg-slate-900/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Total Size</p>
                <p className="text-2xl font-bold text-slate-50 mt-1">914.2 MB</p>
              </div>
              <Download className="w-8 h-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* iModels Table */}
      <Card className="border-slate-700 bg-slate-900/50">
        <CardHeader>
          <CardTitle>All iModels</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Name</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Project</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Status</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Size</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Elements</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Last Sync</th>
                  <th className="text-left py-3 px-4 text-slate-400 font-medium">Version</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((imodel) => {
                  const statusConfig = statusIcons[imodel.status as keyof typeof statusIcons]
                  const StatusIcon = statusConfig.icon

                  return (
                    <tr key={imodel.id} className="border-b border-slate-800 hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-medium text-slate-50">{imodel.name}</td>
                      <td className="py-3 px-4 text-slate-400">{imodel.project}</td>
                      <td className="py-3 px-4">
                        <div className={`flex items-center gap-2 w-fit px-2 py-1 rounded-full ${statusConfig.bg}`}>
                          <StatusIcon className={`w-3 h-3 ${statusConfig.color}`} />
                          <span className={`text-xs font-medium ${statusConfig.color}`}>
                            {imodel.status}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{imodel.size}</td>
                      <td className="py-3 px-4 text-slate-400">{imodel.elements.toLocaleString()}</td>
                      <td className="py-3 px-4 text-slate-400">{imodel.lastSync}</td>
                      <td className="py-3 px-4 text-slate-400">
                        <span className="px-2 py-1 rounded-full bg-slate-800 text-slate-300 text-xs">
                          {imodel.version}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
