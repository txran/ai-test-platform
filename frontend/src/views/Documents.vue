<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="margin: 0;">文档管理</h3>
      <a-upload
        :before-upload="beforeUpload"
        :show-upload-list="false"
        accept=".txt,.md,.json,.yaml,.yml,.docx,.doc,.xlsx,.xls"
      >
        <a-button type="primary">
          <template #icon><UploadOutlined /></template>
          上传文档
        </a-button>
      </a-upload>
    </div>

    <a-table
      :columns="columns"
      :data-source="documents"
      :loading="loading"
      row-key="id"
      :pagination="pagination"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'file_type'">
          <a-tag :color="typeColor(record.file_type)">{{ record.file_type }}</a-tag>
        </template>
        <template v-else-if="column.key === 'file_size'">
          {{ formatSize(record.file_size) }}
        </template>
        <template v-else-if="column.key === 'action'">
          <a-popconfirm title="确认删除该文档？" @confirm="handleDelete(record.id)">
            <a-button type="link" size="small" danger>删除</a-button>
          </a-popconfirm>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { UploadOutlined } from '@ant-design/icons-vue'
import { documents as docApi } from '../api'

const loading = ref(false)
const documents = ref([])

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

const columns = [
  { title: '文件名', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'file_type', key: 'file_type', width: 100 },
  { title: '大小', dataIndex: 'file_size', key: 'file_size', width: 100 },
  { title: '上传时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 100 },
]

function typeColor(t) {
  const map = {
    swagger: 'blue', prd: 'green', excel: 'orange', csv: 'cyan', json: 'purple',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'blue',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'green',
    'application/msword': 'blue', 'application/vnd.ms-excel': 'green',
    'text/plain': 'default', 'text/markdown': 'purple',
    'application/json': 'purple', 'text/yaml': 'cyan'
  }
  return map[t] || 'default'
}

function formatSize(bytes) {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function fetchDocuments() {
  loading.value = true
  try {
    const { data } = await docApi.list({
      page: pagination.current,
      page_size: pagination.pageSize,
    })
    documents.value = data.items || data || []
    pagination.total = data.total || documents.value.length
  } catch (e) {
    message.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchDocuments()
}

function beforeUpload(file) {
  const allowedTypes = [
    'text/plain', 'text/markdown', 'application/json', 'text/yaml', 'application/x-yaml',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/msword', 'application/vnd.ms-excel'
  ]
  const allowedExts = ['.txt', '.md', '.json', '.yaml', '.yml', '.swagger', '.docx', '.doc', '.xlsx', '.xls']
  const ext = '.' + file.name.split('.').pop().toLowerCase()

  if (!allowedTypes.includes(file.type) && !allowedExts.includes(ext)) {
    message.error('仅支持 txt, md, json, yaml 格式文件')
    return false
  }

  handleUpload(file)
  return false
}

async function handleUpload(file) {
  const formData = new FormData()
  formData.append('file', file)

  try {
    await docApi.upload(formData)
    message.success('上传成功')
    fetchDocuments()
  } catch (e) {
    message.error('上传失败')
  }
}

async function handleDelete(id) {
  try {
    await docApi.delete(id)
    message.success('删除成功')
    fetchDocuments()
  } catch (e) {
    message.error('删除失败')
  }
}

onMounted(fetchDocuments)
</script>
