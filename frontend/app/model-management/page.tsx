'use client'

import { useEffect, useState } from 'react'
import { Card, CardTitle } from '@/components/ui/card'
import { ErrorState, LoadingState } from '@/components/ui/state'
import { api } from '@/lib/api'

export default function ModelManagementPage() {
  const [models, setModels] = useState<{ available_versions: string[]; active_version: string | null } | null>(null)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    try {
      setModels(await api.models())
    } catch {
      setError('Failed to load model versions')
    }
  }

  useEffect(() => {
    load()
  }, [])

  const activate = async (version: string) => {
    setStatus('Activating model...')
    try {
      await api.activate(version)
      setStatus(`Activated ${version}`)
      await load()
    } catch {
      setStatus('Activation failed. Check NEXT_PUBLIC_ADMIN_KEY.')
    }
  }

  const retrain = async () => {
    setStatus('Triggering retraining...')
    try {
      await api.triggerTraining()
      setStatus('Retraining triggered')
    } catch {
      setStatus('Retraining failed. Check admin key.')
    }
  }

  if (error) return <ErrorState message={error} />
  if (!models) return <LoadingState />

  return (
    <div className="space-y-4">
      <Card>
        <CardTitle>Model versions</CardTitle>
        <div className="mt-3 space-y-2">
          {models.available_versions.map((version) => (
            <div key={version} className="flex items-center justify-between rounded-lg border border-border p-3">
              <span>{version} {models.active_version === version && <strong>(active)</strong>}</span>
              <button onClick={() => activate(version)} className="rounded-lg border border-border px-3 py-1 text-sm">Activate</button>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <CardTitle>Trigger retraining</CardTitle>
        <button onClick={retrain} className="mt-3 rounded-lg bg-foreground px-4 py-2 text-white">Trigger retraining (admin)</button>
      </Card>
      {status && <p className="text-sm text-muted-foreground">{status}</p>}
    </div>
  )
}
