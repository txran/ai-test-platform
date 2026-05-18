<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="margin: 0;">场景列表</h3>
      <a-button type="primary" @click="showCreateModal">
        <template #icon><PlusOutlined /></template>
        新建场景
      </a-button>
    </div>

    <a-table
      :columns="columns"
      :data-source="suites"
      :loading="loading"
      row-key="id"
      :pagination="pagination"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <a @click="goToDetail(record.id)">{{ record.name }}</a>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusText(record.status) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="goToDetail(record.id)">详情</a-button>
            <a-popconfirm title="确认删除该套件？" @confirm="handleDelete(record.id)">
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 新建场景弹窗 -->
    <a-modal
      v-model:open="createVisible"
      title="新建场景"
      @ok="handleCreate"
      :confirm-loading="creating"
    >
      <a-form :model="createForm" layout="vertical">
        <a-form-item label="名称" required>
          <a-input v-model:value="createForm.name" placeholder="请输入套件名称" />
        </a-form-item>
        <a-form-item label="描述">
        <a-textarea v-model:value="createForm.description" placeholder="请输入套件描述" :rows="3" />
      </a-form-item>
    </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { suites as suitesApi } from '../api'

const router = useRouter()
const loading = ref(false)
const suites = ref([])
const createVisible = ref(false)
const creating = ref(false)

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

const createForm = reactive({
  name: '',
  description: '',
})

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '用例数', dataIndex: 'cases_count', key: 'cases_count', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 150 },
]

function statusColor(s) {
  const map = { draft: 'default', active: 'green', inactive: 'red' }
  return map[s] || 'default'
}

function statusText(s) {
  const map = { draft: '草稿', active: '活跃', inactive: '停用' }
  return map[s] || s
}

async function fetchSuites() {
  loading.value = true
  try {
    const { data } = await suitesApi.list({
      page: pagination.current,
      page_size: pagination.pageSize,
    })
    suites.value = Array.isArray(data) ? data : (data.items || [])
    pagination.total = Array.isArray(data) ? data.length : (data.total || 0)
  } catch (e) {
    message.error('加载套件列表失败')
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchSuites()
}

function goToDetail(id) {
  router.push(`/suites/${id}`)
}

function showCreateModal() {
  createForm.name = ''
  createForm.description = ''
  createVisible.value = true
}

async function handleCreate() {
  if (!createForm.name.trim()) {
    message.warning('请输入套件名称')
    return
  }
  creating.value = true
  try {
    await suitesApi.create({
      name: createForm.name,
      description: createForm.description,
      status: 'active',
    })
    message.success('套件创建成功')
    createVisible.value = false
    fetchSuites()
  } catch (e) {
    message.error('创建失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(id) {
  try {
    await suitesApi.delete(id)
    message.success('删除成功')
    fetchSuites()
  } catch (e) {
    message.error('删除失败')
  }
}

onMounted(fetchSuites)
</script>
