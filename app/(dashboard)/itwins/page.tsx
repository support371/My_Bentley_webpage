'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Plus, Database } from 'lucide-react'

export default function ITwinsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">iTwins</h1>
          <p className="text-muted-foreground mt-2">Collaborate on digital twins</p>
        </div>
        <Button size="lg">
          <Plus className="w-4 h-4 mr-2" />
          New iTwin
        </Button>
      </div>

      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-20">
          <Database className="w-16 h-16 text-muted-foreground/30 mb-4" />
          <p className="text-muted-foreground text-lg">No iTwins yet</p>
          <p className="text-muted-foreground/60 text-sm mt-1">Create your first iTwin to get started</p>
          <Button className="mt-6">Create iTwin</Button>
        </CardContent>
      </Card>
    </div>
  )
}
