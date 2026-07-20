<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="240px" class="sidebar">
      <div class="sidebar-header">
        <h2>📚 知识库问答</h2>
      </div>

      <!-- 新建会话按钮 -->
      <div class="new-chat-btn">
        <el-button type="primary" :icon="Plus" @click="handleNewChat" plain>
          新建会话
        </el-button>
      </div>

      <!-- 会话列表 -->
      <div class="session-list">
        <div
          v-for="session in chatStore.sessions"
          :key="session.id"
          :class="['session-item', { active: session.id === chatStore.currentSessionId }]"
          @click="handleSelectSession(session.id)"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span class="session-title">{{ session.title }}</span>
        </div>
        <el-empty v-if="chatStore.sessions.length === 0" description="暂无会话" :image-size="60" />
      </div>

      <!-- 底部导航 -->
      <div class="sidebar-footer">
        <el-button v-if="authStore.isAdmin" text @click="$router.push('/knowledge')">
          <el-icon><Folder /></el-icon> 知识库管理
        </el-button>
        <el-button text @click="$router.push('/profile')">
          <el-icon><User /></el-icon> 个人中心
        </el-button>
      </div>
    </el-aside>

    <!-- 主区域 -->
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <el-tag v-if="authStore.isAdmin" type="warning" size="small">管理员</el-tag>
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ authStore.user?.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus, ChatDotRound, Folder, User, ArrowDown } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const pageTitle = computed(() => {
  switch (route.name) {
    case 'Chat': return '智能问答'
    case 'KnowledgeManage': return '知识库管理'
    case 'Profile': return '个人中心'
    default: return '电商知识库问答系统'
  }
})

onMounted(async () => {
  if (authStore.isLoggedIn) {
    await chatStore.loadSessions()
  }
})

async function handleNewChat() {
  await chatStore.createSession()
  router.push('/chat')
}

async function handleSelectSession(sessionId: number) {
  await chatStore.selectSession(sessionId)
  router.push('/chat')
}

async function handleCommand(command: string) {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning',
    })
    authStore.logout()
    ElMessage.success('已退出登录')
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/profile')
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background: var(--sidebar-bg);
  color: var(--sidebar-text);
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 20px 16px;
  text-align: center;
  border-bottom: 1px solid #1f2d3d;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 16px;
  color: white;
}

.new-chat-btn {
  padding: 12px;
}

.new-chat-btn .el-button {
  width: 100%;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  margin: 4px 0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.session-item:hover {
  background: #263445;
}

.session-item.active {
  background: var(--sidebar-active);
  color: white;
}

.session-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-footer {
  padding: 12px;
  border-top: 1px solid #1f2d3d;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-footer .el-button {
  width: 100%;
  justify-content: flex-start;
  color: var(--sidebar-text);
}

.sidebar-footer .el-button:hover {
  color: white;
}

.header {
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #606266;
}

.main-content {
  padding: 0;
  background: #f5f7fa;
  overflow: hidden;
}
</style>
