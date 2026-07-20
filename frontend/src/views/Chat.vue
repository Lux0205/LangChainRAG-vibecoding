<template>
  <div class="chat-container">
    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <!-- 欢迎消息 -->
      <div v-if="chatStore.messages.length === 0" class="welcome">
        <div class="welcome-icon">🤖</div>
        <h2>欢迎使用电商知识库问答系统</h2>
        <p>我是您的智能助手，可以回答关于商品的各种问题</p>
        <div class="quick-questions">
          <el-tag
            v-for="q in quickQuestions"
            :key="q"
            @click="handleSend(q)"
            class="quick-tag"
          >
            {{ q }}
          </el-tag>
        </div>
      </div>

      <!-- 消息 -->
      <div
        v-for="(msg, index) in chatStore.messages"
        :key="index"
        :class="['message-wrapper', msg.role]"
      >
        <el-avatar :size="36" :icon="msg.role === 'user' ? User : Monitor" />
        <div class="message-content">
          <div :class="['message-bubble', msg.role]">
            <div v-if="msg.role === 'assistant'" v-html="formatContent(msg.content)" />
            <span v-else>{{ msg.content }}</span>
            <span v-if="msg.role === 'assistant' && chatStore.isLoading && index === chatStore.messages.length - 1" class="typing-cursor" />
          </div>
          <!-- 引用来源 -->
          <CitationCard
            v-if="msg.citations && msg.citations.length > 0"
            :citations="msg.citations"
          />
        </div>
      </div>

      <!-- 加载指示 -->
      <div v-if="chatStore.isLoading" class="loading-indicator">
        <el-icon classis="is-loading"><Loading /></el-icon>
        <span>正在思考中...</span>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-wrapper">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="3"
          placeholder="输入您的问题... (Enter发送, Shift+Enter换行)"
          :disabled="chatStore.isLoading"
          @keydown.enter.exact.prevent="handleSend()"
          resize="none"
        />
        <div class="input-actions">
          <el-select v-model="selectedProvider" size="small" style="width: 140px">
            <el-option label="纯检索模式" value="none" />
            <el-option label="通义千问" value="tongyi" />
            <el-option label="智谱GLM" value="zhipu" />
          </el-select>
          <el-button
            type="primary"
            :icon="Position"
            :loading="chatStore.isLoading"
            :disabled="!inputText.trim()"
            @click="handleSend()"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { User, Monitor, Position, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useChatStore } from '@/stores/chat'
import CitationCard from '@/components/CitationCard.vue'

const chatStore = useChatStore()
const inputText = ref('')
const selectedProvider = ref('none')
const messageListRef = ref<HTMLElement>()

const quickQuestions = [
  'iPhone 15 Pro 多少钱？',
  '华为Mate 60 Pro支持卫星通话吗？',
  '小米14的屏幕尺寸是多少？',
  'MacBook Pro M3 内存最大多少？',
  '平台售后政策是什么？',
]

onMounted(async () => {
  if (chatStore.sessions.length === 0) {
    await chatStore.loadSessions()
  }
  if (chatStore.sessions.length > 0 && !chatStore.currentSessionId) {
    await chatStore.selectSession(chatStore.sessions[0].id)
  }
})

async function handleSend(quickQuestion?: string) {
  const text = quickQuestion || inputText.value.trim()
  if (!text) return

  if (!chatStore.currentSessionId) {
    await chatStore.createSession()
  }

  inputText.value = ''
  await chatStore.sendMessage(text, selectedProvider.value)
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function formatContent(content: string): string {
  // 简单的Markdown格式处理
  return content
    .replace(/\[(\d+)\]/g, '<sup class="citation-ref">[$1]</sup>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 40px;
}

.welcome {
  text-align: center;
  padding: 60px 20px;
}

.welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.welcome h2 {
  font-size: 24px;
  color: #303133;
  margin: 0 0 8px;
}

.welcome p {
  color: #909399;
  margin: 0 0 24px;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.quick-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.quick-tag:hover {
  background: #ecf5ff;
  color: #409eff;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
}

.message-bubble.user {
  background: #409eff;
  color: white;
  border-radius: 12px 12px 4px 12px;
}

.message-bubble.assistant {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 12px 12px 12px 4px;
}

.typing-cursor::after {
  content: '▊';
  animation: blink 1s infinite;
  color: #409eff;
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 14px;
  padding: 12px 0;
}

.input-area {
  border-top: 1px solid #e4e7ed;
  background: white;
  padding: 16px 40px;
}

.input-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

:deep(.citation-ref) {
  color: #67c23a;
  font-weight: 600;
  font-size: 12px;
}
</style>
