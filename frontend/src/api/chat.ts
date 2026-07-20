import request from './request'

export function getSessions(): Promise<any[]> {
  return request.get('/chat/sessions')
}

export function createSession(): Promise<any> {
  return request.post('/chat/sessions')
}

export function deleteSession(sessionId: number) {
  return request.delete(`/chat/sessions/${sessionId}`)
}

export function getMessages(sessionId: number): Promise<any[]> {
  return request.get(`/chat/sessions/${sessionId}/messages`)
}

/**
 * SSE流式聊天
 * 使用fetch API因为axios不支持SSE流式读取
 */
export async function chatStream(
  sessionId: number,
  question: string,
  provider: string | undefined,
  onToken: (token: string) => void,
  onCitations: (citations: any[]) => void,
) {
  const token = localStorage.getItem('access_token')
  const url = `/api/chat/chat?session_id=${sessionId}&question=${encodeURIComponent(question)}${provider ? '&provider=' + provider : ''}`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'token') {
            onToken(data.content)
          } else if (data.type === 'citations') {
            onCitations(data.data)
          }
        } catch {
          // 忽略解析错误
        }
      }
    }
  }
}
