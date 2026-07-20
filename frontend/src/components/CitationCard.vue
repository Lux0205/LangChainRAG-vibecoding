<template>
  <div class="citation-container" v-if="citations && citations.length > 0">
    <el-collapse>
      <el-collapse-item title="📎 参考来源" name="citations">
        <div class="citation-list">
          <div
            v-for="cite in citations"
            :key="cite.index"
            class="citation-item"
          >
            <div class="citation-header">
              <span class="citation-index">[{{ cite.index }}]</span>
              <span class="citation-doc">{{ cite.doc_title }}</span>
              <el-tag size="small" type="success" effect="plain">
                相似度: {{ (cite.score * 100).toFixed(0) }}%
              </el-tag>
            </div>
            <div class="citation-text">{{ cite.content }}</div>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { Citation } from '@/stores/chat'

defineProps<{
  citations: Citation[]
}>()
</script>

<style scoped>
.citation-container {
  margin-top: 8px;
}

.citation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.citation-item {
  background: #f0f9eb;
  border-left: 3px solid #67c23a;
  border-radius: 4px;
  padding: 10px 12px;
}

.citation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.citation-index {
  font-weight: 700;
  color: #67c23a;
}

.citation-doc {
  flex: 1;
  font-weight: 600;
  color: #303133;
  font-size: 13px;
}

.citation-text {
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}
</style>
