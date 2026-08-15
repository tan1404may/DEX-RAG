const API_BASE = 'http://localhost:8000'

export interface QueryResponse {
  question: string
  answer: string
  sources: {
    text: string
    score: number
    metadata: Record<string, any>
  }[]
}

export async function queryRag(question: string, userId: string = 'default'): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, user_id: userId, top_k: 5 }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function ingestDocument(file: File, userId: string = 'default', docId?: string): Promise<any> {
  const form = new FormData()
  form.append('file', file)
  form.append('user_id', userId)
  if (docId) form.append('doc_id', docId)

  const res = await fetch(`${API_BASE}/ingest`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}