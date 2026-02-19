import './globals.css'
import { Nav } from '@/components/nav'

export const metadata = {
  title: 'ML Engine Platform',
  description: 'Production dashboard for ML lifecycle management.'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="mx-auto min-h-screen max-w-7xl p-6 md:p-8">
          <header className="mb-4">
            <h1 className="text-2xl font-semibold">ML Engine Platform</h1>
            <p className="text-sm text-muted-foreground">Internal ML control platform dashboard</p>
          </header>
          <Nav />
          {children}
        </main>
      </body>
    </html>
  )
}
