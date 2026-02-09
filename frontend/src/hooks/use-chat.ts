import { useState } from 'react'
import { chatAPI } from '@/lib/api-client'
import type { Message } from '@/types/message'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = async (content: string) => {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      type: 'text',
      content,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      // Build chat history from previous messages for backend context
      const chatHistory = messages.map(m => ({
        role: m.role,
        content: m.content,
      }))
      const result = await chatAPI.sendMessage(content, chatHistory)

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        type: 'text',
        content: result.response,
        sources: result.sources,
        cached: result.cached,
        timestamp: new Date(result.timestamp),
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'An error occurred'
      setError(errorMsg)
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          type: 'text',
          content: `Something went wrong: ${errorMsg}`,
          timestamp: new Date(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const clearChat = () => {
    setMessages([])
    setError(null)
  }

  return { messages, isLoading, error, sendMessage, clearChat }
}
