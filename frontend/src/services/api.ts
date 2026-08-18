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

export interface DocumentItem {
  doc_id: string
  title: string
  created_at: string
}

export interface DocumentListResponse {
  documents: DocumentItem[]
  total: number
}

export async function queryRag(
  question: string,
  userId: string = 'default',
  docId?: string
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      user_id: userId,
      top_k: 5,
      doc_id: docId,
    }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function ingestFile(file: File, userId: string = 'default'): Promise<any> {
  const form = new FormData()
  form.append('file', file)
  form.append('user_id', userId)

  const res = await fetch(`${API_BASE}/ingest`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function listDocuments(userId: string = 'default'): Promise<DocumentListResponse> {
  const res = await fetch(`${API_BASE}/documents?user_id=${userId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function deleteDocument(docId: string, userId: string = 'default'): Promise<any> {
  const res = await fetch(`${API_BASE}/documents/${docId}?user_id=${userId}`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}