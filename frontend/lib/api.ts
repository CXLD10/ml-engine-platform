import axios from 'axios'

const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_BACKEND_URL ?? 'http://localhost:8000'
})

function unwrap<T>(data: any): T {
  if (data && typeof data === 'object' && data.status === 'success' && 'data' in data) {
    return data.data as T
  }
  return data as T
}

export const api = {
  health: async () => unwrap<{ status: string; service: string; environment: string }>((await client.get('/health')).data),
  ready: async () => unwrap<{ status: string }>((await client.get('/ready')).data),
  models: async () => {
    const res = unwrap<any>((await client.get('/models')).data)
    return { available_versions: res.available_versions ?? [], active_version: res.active_version ?? null }
  },
  drift: async () => {
    const res = unwrap<any>((await client.get('/monitoring/drift')).data)
    const featureRows = Object.values(res.details ?? {}) as Array<any>
    const score = featureRows.length ? featureRows.reduce((acc, row) => acc + (row.mean_deviation_ratio ?? 0), 0) / featureRows.length : 0
    return { status: res.status ?? 'unknown', score, threshold: 0.25 }
  },
  latency: async () => {
    const res = unwrap<any>((await client.get('/monitoring/latency')).data)
    return {
      count: res.recent_calls ?? 0,
      average_ms: res.avg_latency_ms ?? 0,
      p95_ms: res.avg_latency_ms ?? 0,
      max_ms: res.avg_latency_ms ?? 0,
      history: Array.from({ length: Math.max(res.recent_calls ?? 0, 1) }).map((_, idx) => Number(res.avg_latency_ms ?? 0) + idx * 0.2)
    }
  },
  freshness: async () => {
    const res = unwrap<any>((await client.get('/monitoring/freshness')).data)
    return { model_last_trained: res.model_last_trained ?? null, last_upstream_fetch: res.upstream_last_seen ?? null }
  },
  history: async () => unwrap<{ runs: Array<{ timestamp: string; version: string; metrics?: { rmse?: number } }> }>((await client.get('/monitoring/history')).data),
  predict: async (symbol: string) => unwrap<any>((await client.get('/predict', { params: { symbol } })).data),
  activate: async (version: string) => unwrap((await client.post(`/admin/activate/${version}`, {}, { headers: { 'X-API-Key': process.env.NEXT_PUBLIC_ADMIN_KEY ?? '' } })).data),
  triggerTraining: async () => unwrap((await client.post('/admin/train', {}, { headers: { 'X-API-Key': process.env.NEXT_PUBLIC_ADMIN_KEY ?? '' } })).data)
}
