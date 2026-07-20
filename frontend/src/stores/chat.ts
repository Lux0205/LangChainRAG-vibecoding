import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as chatApi from '@/api/chat'

export interface Message {
  id?: number
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  created_at?: string
}

export interface Citation {
  index: number
  doc_title: string
  content: string
  score: number
}

export interface ChatSession {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export const useChatStore = defineStore('chat', () => {
  // State
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<number | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)

  // Actions
  async function loadSessions() {
    sessions.value = await chatApi.getSessions()
  }

  async function createSession() {
    const session = await chatApi.createSession()
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    messages.value = []
    return session
  }

  async function selectSession(sessionId: number) {
    currentSessionId.value = sessionId
    messages.value = await chatApi.getMessages(sessionId)
  }

  async function deleteSession(sessionId: number) {
    await chatApi.deleteSession(sessionId)
    sessions.value = sessions.value.filter(s => s.id !== sessionId)
    if (currentSessionId.value === sessionId) {
      currentSessionId.value = null
      messages.value = []
    }
  }

  async function sendMessage(content: string, provider?: string) {
    if (!currentSessionId.value) return

    // 添加用户消息
    const userMsg: Message = { role: 'user', content }
    messages.value.push(userMsg)
    isLoading.value = true

    // 创建助手消息占位
    const assistantMsg: Message = { role: 'assistant', content: '', citations: [] }
    messages.value.push(assistantMsg)

    try {
      // SSE流式请求
      await chatApi.chatStream(
        currentSessionId.value,
        content,
        provider,
        // onToken
        (token: string) => {
          assistantMsg.content += token
        },
        // onCitations
        (citations: Citation[]) => {
          assistantMsg.citations = citations
        },
      )
    } catch (error: any) {
      assistantMsg.content = `请求失败: ${error.message || '未知错误'}`
    } finally {
      isLoading.value = false
      // 刷新会话列表（标题可能变了）
      loadSessions()
    }
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isLoading,
    loadSessions,
    createSession,
    selectSession,
    deleteSession,
    sendMessage,
  }
})
