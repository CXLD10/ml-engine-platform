'use client'

import { useEffect, useState } from 'react'
import { Card, CardTitle } from '@/components/ui/card'
import { ErrorState, LoadingState } from '@/components/ui/state'
import { api } from '@/lib/api'

export default function DashboardPage() {
  const [state, setState] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.models(), api.drift(), api.latency(), api.health(), api.freshness()])
      .then(([models, drift, latency, health, freshness]) => setState({ models, drift, latency, health, freshness }))
      .catch((err) => setError(err?.response?.data?.detail ?? 'Failed to load dashboard'))
  }, [])

  if (error) return <ErrorState message={error} />
  if (!state) return <LoadingState />

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <Card><CardTitle>Active model</CardTitle><p className="mt-2 text-2xl font-semibold">{state.models.active_version ?? 'None'}</p></Card>
      <Card><CardTitle>Drift status</CardTitle><p className="mt-2 text-2xl font-semibold">{state.drift.status}</p><p className="text-sm text-muted-foreground">Score {state.drift.score?.toFixed?.(4)}</p></Card>
      <Card><CardTitle>Latency P95</CardTitle><p className="mt-2 text-2xl font-semibold">{state.latency.p95_ms.toFixed(2)} ms</p><p className="text-sm text-muted-foreground">Avg {state.latency.average_ms.toFixed(2)} ms</p></Card>
      <Card><CardTitle>Upstream health</CardTitle><p className="mt-2 text-2xl font-semibold">{state.health.status}</p><p className="text-sm text-muted-foreground">Env: {state.health.environment}</p></Card>
      <Card className="md:col-span-2 xl:col-span-2"><CardTitle>Last training timestamp</CardTitle><p className="mt-2 text-lg">{state.freshness.model_last_trained ?? 'No training run recorded'}</p></Card>
    </div>
  )
}
