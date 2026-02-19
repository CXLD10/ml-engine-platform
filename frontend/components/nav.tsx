'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

const links = [
  { href: '/', label: 'Overview' },
  { href: '/prediction-explorer', label: 'Prediction Explorer' },
  { href: '/model-management', label: 'Model Management' },
  { href: '/monitoring', label: 'Monitoring' }
]

export function Nav() {
  const pathname = usePathname()

  return (
    <nav className="mb-6 flex flex-wrap gap-2">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={cn(
            'rounded-lg border px-3 py-2 text-sm transition',
            pathname === link.href ? 'border-foreground bg-foreground text-white' : 'border-border bg-white hover:bg-muted'
          )}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  )
}
