'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Users,
  Settings,
  Lock,
  AlertCircle,
  Trash2,
  Edit2,
  Plus,
  Search,
  Shield,
} from 'lucide-react'
import { StatCard } from '@/components/stat-card'

const mockUsers = [
  {
    id: 1,
    name: 'John Doe',
    email: 'john@example.com',
    role: 'admin',
    status: 'active',
    joined: '2024-01-10',
  },
  {
    id: 2,
    name: 'Jane Smith',
    email: 'jane@example.com',
    role: 'editor',
    status: 'active',
    joined: '2024-01-12',
  },
  {
    id: 3,
    name: 'Bob Wilson',
    email: 'bob@example.com',
    role: 'viewer',
    status: 'inactive',
    joined: '2024-01-05',
  },
]

const mockAuditLog = [
  { id: 1, user: 'John Doe', action: 'Created project', resource: 'Central Tower', timestamp: '2024-01-15 10:30' },
  { id: 2, user: 'Jane Smith', action: 'Updated iModel', resource: 'Structure v2.1', timestamp: '2024-01-15 10:15' },
  { id: 3, user: 'Bob Wilson', action: 'Deleted file', resource: 'Old_backup.bim', timestamp: '2024-01-15 09:45' },
]

export default function AdminPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [activeTab, setActiveTab] = useState('users')

  const filteredUsers = mockUsers.filter((user) =>
    user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-50">Admin Panel</h1>
          <p className="text-slate-400 mt-2">Manage users, roles, and platform settings</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Users"
          value="24"
          description="Active members"
          icon={Users}
          variant="default"
        />
        <StatCard
          title="Active Sessions"
          value="12"
          description="Currently online"
          variant="success"
        />
        <StatCard
          title="Admins"
          value="3"
          description="Platform administrators"
          icon={Shield}
          variant="default"
        />
        <StatCard
          title="Storage Used"
          value="1.2 TB"
          description="Of 5 TB quota"
          variant="warning"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-700">
        {['users', 'roles', 'audit', 'settings'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 font-medium text-sm capitalize border-b-2 transition ${
              activeTab === tab
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <Input
                placeholder="Search users..."
                className="pl-10 bg-slate-900 border-slate-700"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add User
            </Button>
          </div>

          <Card className="border-slate-700 bg-slate-900/50 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-700 bg-slate-800/30">
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">Name</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">Email</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">Role</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">Status</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">Joined</th>
                    <th className="text-left py-3 px-4 text-slate-400 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="border-b border-slate-800 hover:bg-slate-800/30 transition">
                      <td className="py-3 px-4 font-medium text-slate-50">{user.name}</td>
                      <td className="py-3 px-4 text-slate-400">{user.email}</td>
                      <td className="py-3 px-4">
                        <span className="inline-block px-2 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs font-medium capitalize">
                          {user.role}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                            user.status === 'active'
                              ? 'bg-green-500/20 text-green-400'
                              : 'bg-slate-600/30 text-slate-400'
                          }`}
                        >
                          {user.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400">{user.joined}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <Button variant="ghost" size="sm">
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-red-400 hover:text-red-300">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* Audit Log Tab */}
      {activeTab === 'audit' && (
        <Card className="border-slate-700 bg-slate-900/50">
          <CardHeader>
            <CardTitle>Audit Log</CardTitle>
            <CardDescription>Recent system activities and user actions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {mockAuditLog.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start gap-4 p-3 rounded-lg border border-slate-800 hover:bg-slate-800/30 transition"
                >
                  <div className="w-2 h-2 rounded-full bg-blue-400 mt-1.5" />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-50">{log.action}</p>
                    <p className="text-sm text-slate-400 mt-1">
                      {log.user} • {log.resource}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">{log.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="space-y-4">
          <Card className="border-slate-700 bg-slate-900/50">
            <CardHeader>
              <CardTitle>Platform Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-50">Platform Name</label>
                <Input defaultValue="iTwin Ops" className="bg-slate-900 border-slate-700" />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-50">Max Upload Size (MB)</label>
                <Input defaultValue="500" type="number" className="bg-slate-900 border-slate-700" />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-50">Session Timeout (minutes)</label>
                <Input defaultValue="60" type="number" className="bg-slate-900 border-slate-700" />
              </div>

              <div className="border-t border-slate-700 pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-50">Require Email Verification</p>
                    <p className="text-sm text-slate-500 mt-1">New users must verify email</p>
                  </div>
                  <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                </div>
              </div>

              <div className="border-t border-slate-700 pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-50">Enable Two-Factor Auth</p>
                    <p className="text-sm text-slate-500 mt-1">Required for all admin users</p>
                  </div>
                  <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
                </div>
              </div>

              <Button className="mt-6">Save Settings</Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
