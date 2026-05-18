import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// === 功能管理 ===
export const functions = {
  list: () => api.get('/functions'),
  get: (id) => api.get(`/functions/${id}`),
  create: (data) => api.post('/functions', data),
  update: (id, data) => api.put(`/functions/${id}`, data),
  delete: (id) => api.delete(`/functions/${id}`),
  getCases: (funcId) => api.get(`/functions/${funcId}/cases`),
  createCase: (funcId, data) => api.post(`/functions/${funcId}/cases`, data),
}

// === 用例管理 ===
export const testCases = {
  get: (id) => api.get(`/cases/${id}`),
  update: (id, data) => api.put(`/cases/${id}`, data),
  delete: (id) => api.delete(`/cases/${id}`),
}

// === 套件管理 ===
export const suites = {
  list: () => api.get('/suites'),
  get: (id) => api.get(`/suites/${id}`),
  create: (data) => api.post('/suites', data),
  update: (id, data) => api.put(`/suites/${id}`, data),
  delete: (id) => api.delete(`/suites/${id}`),
  addFunctions: (id, functionIds) => api.post(`/suites/${id}/functions`, { function_ids: functionIds }),
  removeFunction: (suiteId, funcId) => api.delete(`/suites/${suiteId}/functions/${funcId}`),
  listFunctions: (id) => api.get(`/suites/${id}/functions`),
  listScripts: (id) => api.get(`/suites/${id}/scripts`),
  getScript: (scriptId) => api.get(`/scripts/${scriptId}`),
  generateScript: (id) => api.post(`/suites/${id}/generate`),
  execute: (id) => api.post(`/suites/${id}/execute`),
  listExecutions: (id) => api.get(`/suites/${id}/executions`),
}

// === 生成用例 ===
export const generate = {
  fromUrl: (data) => api.post('/generate/from-url', data),
  fromPrd: (data) => api.post('/generate/from-prd', data),
  uploadPrd: (formData) => api.post('/generate/upload-prd', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  importExcel: (formData) => api.post('/generate/import-excel', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  manual: (data) => api.post('/generate/manual', data),
  import: (formData) => api.post('/generate/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  fromDescription: (functionId, formData) => api.post(`/generate/functions/${functionId}/generate-from-description`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
}

// === 文档管理 ===
export const documents = {
  list: (params = {}) => api.get('/documents', { params }),
  upload: (formData) => api.post('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  delete: (id) => api.delete(`/documents/${id}`),
}

// === 模型配置 ===
export const modelConfigs = {
  list: () => api.get('/model-configs'),
  get: (id) => api.get(`/model-configs/${id}`),
  create: (data) => api.post('/model-configs', data),
  update: (id, data) => api.put(`/model-configs/${id}`, data),
  delete: (id) => api.delete(`/model-configs/${id}`),
}

// === 执行 ===
export const executions = {
  list: (params = {}) => api.get('/executions', { params }),
  get: (id) => api.get(`/executions/${id}`),
  create: (data) => api.post('/executions', data),
  screenshots: (id) => api.get(`/executions/${id}/screenshots`),
}

export default api


// === 补充缺失的方法 ===
testCases.create = (data) => api.post('/cases', data)
testCases.list = (params = {}) => api.get('/cases', { params })
generate.fromSwagger = (data) => api.post('/generate/from-swagger', data)
