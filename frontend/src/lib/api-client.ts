const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export interface ChatRequest {
  message: string
  chat_history?: { role: string; content: string }[]
}

export interface ChatResponse {
  response: string
  sources: { id: string; source: string; title: string }[]
  cached: boolean
  timestamp: string
}

export class ChatAPIClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  async sendMessage(
    message: string,
    chatHistory?: { role: string; content: string }[]
  ): Promise<ChatResponse> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)

    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          chat_history: chatHistory,
        } as ChatRequest),
        signal: controller.signal,
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }))
        throw new Error(err.detail || `API error: ${response.status}`)
      }

      return response.json()
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new Error('Request timed out. Please try again.')
      }
      throw err
    } finally {
      clearTimeout(timeoutId)
    }
  }

  async ingest(sources?: string[]): Promise<{ results: Record<string, number | string> }> {
    const response = await fetch(`${this.baseUrl}/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sources ? { sources } : {}),
    })

    if (!response.ok) {
      throw new Error(`Ingest error: ${response.status}`)
    }

    return response.json()
  }

  async clearCache(): Promise<void> {
    await fetch(`${this.baseUrl}/cache/clear`, { method: 'POST' })
  }

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/health`)
    if (!response.ok) throw new Error(`Health check failed: ${response.status}`)
    return response.json()
  }
}

export const chatAPI = new ChatAPIClient()
