import { cn } from '@/lib/utils'
import { type ReactNode } from 'react'

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <section className={cn('rounded-xl border border-border bg-card p-5 shadow-sm', className)}>{children}</section>
}

export function CardTitle({ children }: { children: ReactNode }) {
  return <h3 className="text-sm font-semibold text-muted-foreground">{children}</h3>
}
