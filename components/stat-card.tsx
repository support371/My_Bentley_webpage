'use client'

import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  description?: string
  icon?: LucideIcon
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  variant?: 'default' | 'success' | 'warning' | 'danger'
}

const variantStyles = {
  default: 'bg-slate-800/50 border-slate-700',
  success: 'bg-green-500/10 border-green-500/20',
  warning: 'bg-yellow-500/10 border-yellow-500/20',
  danger: 'bg-red-500/10 border-red-500/20',
}

const variantTextStyles = {
  default: 'text-slate-400',
  success: 'text-green-400',
  warning: 'text-yellow-400',
  danger: 'text-red-400',
}

export function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  trendValue,
  variant = 'default',
}: StatCardProps) {
  return (
    <Card className={cn('border', variantStyles[variant])}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-slate-400">{title}</p>
          {Icon && <Icon className={cn('w-4 h-4', variantTextStyles[variant])} />}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <div className="text-2xl font-bold text-slate-50">{value}</div>
          {trendValue && (
            <span
              className={cn(
                'text-xs font-medium',
                trend === 'up' && 'text-green-400',
                trend === 'down' && 'text-red-400',
                trend === 'neutral' && 'text-slate-400'
              )}
            >
              {trend === 'up' && '↑ '}
              {trend === 'down' && '↓ '}
              {trendValue}
            </span>
          )}
        </div>
        {description && <p className="text-xs text-slate-500 mt-2">{description}</p>}
      </CardContent>
    </Card>
  )
}
