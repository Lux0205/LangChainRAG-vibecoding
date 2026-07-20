import request from './request'

export function uploadDocument(file: File): Promise<any> {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getDocuments(page = 1, pageSize = 20, keyword = ''): Promise<any> {
  return request.get('/knowledge/documents', {
    params: { page, page_size: pageSize, keyword },
  })
}

export function deleteDocument(docId: number): Promise<any> {
  return request.delete(`/knowledge/documents/${docId}`)
}

export function getKnowledgeStats(): Promise<any> {
  return request.get('/knowledge/stats')
}
