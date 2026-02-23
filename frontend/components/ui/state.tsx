export function LoadingState({ label = 'Loading data...' }: { label?: string }) {
  return <div className="rounded-xl border border-dashed border-border bg-white p-6 text-sm text-muted-foreground">{label}</div>
}

export function ErrorState({ message }: { message: string }) {
  return <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-600">{message}</div>
}
