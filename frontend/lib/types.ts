export type ApiEnvelope<T> = {
  status: 'success' | 'error'
  data: T
  message?: string
  request_id?: string
  timestamp?: string
}

export type ModelSummary = {
  available_versions: string[]
  active_version: string | null
}

export type DriftStatus = {
  status: string
  score: number
  threshold: number
}

export type LatencySnapshot = {
  count: number
  average_ms: number
  p95_ms: number
  max_ms: number
  history: number[]
}
