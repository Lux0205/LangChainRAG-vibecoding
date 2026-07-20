<template>
  <div class="knowledge-container">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-value">{{ stats.total_documents || 0 }}</div>
        <div class="stat-label">文档总数</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ stats.indexed_documents || 0 }}</div>
        <div class="stat-label">已索引</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ stats.total_chunks || 0 }}</div>
        <div class="stat-label">知识片段</div>
      </el-card>
    </div>

    <!-- 上传区域 -->
    <el-card class="upload-card">
      <div class="upload-area">
        <el-upload
          drag
          :action="uploadAction"
          :headers="uploadHeaders"
          :before-upload="beforeUpload"
          :on-success="handleUploadSuccess"
          :on-error="handleUploadError"
          accept=".pdf,.docx,.txt,.csv"
          :show-file-list="false"
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 PDF / DOCX / TXT / CSV 格式，单文件不超过50MB
            </div>
          </template>
        </el-upload>
      </div>
    </el-card>

    <!-- 文档列表 -->
    <el-card class="table-card">
      <div class="table-header">
        <h3>知识库文档</h3>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文档标题"
          :prefix-icon="Search"
          style="width: 240px"
          clearable
          @input="handleSearch"
        />
      </div>

      <el-table :data="documents" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="文档标题" min-width="200" />
        <el-table-column prop="file_type" label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_type?.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="chunk_count" label="片段数" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === 'indexed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'"
              size="small"
            >
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
              circle
            />
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="loadDocuments"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, Delete, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as knowledgeApi from '@/api/knowledge'

const documents = ref<any[]>([])
const stats = ref<any>({})
const loading = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const uploadAction = '/api/knowledge/upload'
const uploadHeaders = {
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
}

onMounted(() => {
  loadDocuments()
  loadStats()
})

async function loadDocuments() {
  loading.value = true
  try {
    const res = await knowledgeApi.getDocuments(currentPage.value, pageSize.value, searchKeyword.value)
    documents.value = res.items || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await knowledgeApi.getKnowledgeStats()
  } catch {
    // 忽略
  }
}

function handleSearch() {
  currentPage.value = 1
  loadDocuments()
}

function beforeUpload(file: File) {
  const maxSize = 50 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过50MB')
    return false
  }
  return true
}

function handleUploadSuccess() {
  ElMessage.success('文档上传成功，正在索引...')
  loadDocuments()
  loadStats()
}

function handleUploadError() {
  ElMessage.error('文档上传失败')
}

async function handleDelete(row: any) {
  await ElMessageBox.confirm(
    `确定要删除文档《${row.title}》吗？删除后不可恢复。`,
    '确认删除',
    { type: 'warning' }
  )
  await knowledgeApi.deleteDocument(row.id)
  ElMessage.success('删除成功')
  loadDocuments()
  loadStats()
}

function statusText(status: string) {
  const map: Record<string, string> = {
    processing: '索引中',
    indexed: '已索引',
    failed: '失败',
  }
  return map[status] || status
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.knowledge-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.upload-card {
  margin-bottom: 20px;
}

.upload-area {
  padding: 10px 0;
}

.table-card {
  margin-bottom: 20px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
