'use client'

import { useEffect, useMemo, useState } from 'react'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, BarChart, Bar } from 'recharts'
import { Card, CardTitle } from '@/components/ui/card'
import { ErrorState, LoadingState } from '@/components/ui/state'
import { api } from '@/lib/api'

export default function MonitoringPage() {
  const [payload, setPayload] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.drift(), api.history(), api.latency()])
      .then(([drift, history, latency]) => setPayload({ drift, history, latency }))
      .catch(() => setError('Failed to load monitoring data'))
  }, [])

  const latencySeries = useMemo(
    () => (payload?.latency?.history ?? []).map((value: number, idx: number) => ({ idx, value })),
    [payload]
  )

  const trainingSeries = useMemo(
    () =>
      (payload?.history?.runs ?? []).map((run: any, idx: number) => ({
        idx,
        rmse: run.metrics?.rmse ?? 0,
        version: run.version
      })),
    [payload]
  )

  if (error) return <ErrorState message={error} />
  if (!payload) return <LoadingState />

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Card>
        <CardTitle>Drift metrics</CardTitle>
        <p className="mt-3 text-2xl font-semibold">{payload.drift.status}</p>
        <p className="text-sm text-muted-foreground">Score: {payload.drift.score.toFixed(4)} / Threshold: {payload.drift.threshold}</p>
      </Card>
      <Card>
        <CardTitle>Training history (RMSE)</CardTitle>
        <div className="mt-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={trainingSeries}>
              <XAxis dataKey="idx" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="rmse" fill="#111827" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <Card className="xl:col-span-2">
        <CardTitle>Latency chart</CardTitle>
        <div className="mt-4 h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={latencySeries}>
              <XAxis dataKey="idx" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#111827" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}
