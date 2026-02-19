'use client'

import { useMemo, useState } from 'react'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CardTitle } from '@/components/ui/card'
import { ErrorState, LoadingState } from '@/components/ui/state'
import { api } from '@/lib/api'

export default function PredictionExplorerPage() {
  const [symbol, setSymbol] = useState('AAPL')
  const [data, setData] = useState<any>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const chartData = useMemo(() => {
    if (!data?.features) return []
    return Object.entries(data.features).map(([name, value], i) => ({ idx: i + 1, name, value: Number(value) }))
  }, [data])

  const fetchPrediction = async () => {
    setLoading(true)
    setError('')
    try {
      const payload = await api.predict(symbol)
      setData(payload)
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Prediction request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardTitle>Symbol input</CardTitle>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} className="rounded-lg border border-border px-3 py-2" />
          <button onClick={fetchPrediction} className="rounded-lg bg-foreground px-4 py-2 text-white">Fetch prediction</button>
        </div>
      </Card>

      {loading && <LoadingState label="Fetching prediction..." />}
      {error && <ErrorState message={error} />}
      {data && !loading && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <Card><CardTitle>Prediction</CardTitle><p className="mt-2 text-2xl font-semibold">{data.prediction}</p></Card>
            <Card><CardTitle>Confidence</CardTitle><p className="mt-2 text-2xl font-semibold">{Number(data.confidence).toFixed(4)}</p></Card>
            <Card><CardTitle>Model version</CardTitle><p className="mt-2 text-2xl font-semibold">{data.model_version}</p></Card>
          </div>
          <Card>
            <CardTitle>Feature values</CardTitle>
            <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
              {Object.entries(data.features ?? {}).map(([k, v]) => (
                <div key={k} className="rounded-md bg-muted p-2 text-sm"><span className="font-medium">{k}</span>: {String(v)}</div>
              ))}
            </div>
          </Card>
          <Card>
            <CardTitle>Feature chart</CardTitle>
            <div className="mt-4 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="idx" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#111827" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
