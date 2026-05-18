<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="margin: 0;">测试用例管理</h3>
      <a-space>
        <a-button type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
          新建用例
        </a-button>
        <a-upload :before-upload="handleImport" :show-upload-list="false" accept=".json,.csv">
          <a-button>
            <template #icon><UploadOutlined /></template>
            导入
          </a-button>
        </a-upload>
      </a-space>
    </div>

    <!-- 筛选条件 -->
    <a-card size="small" style="margin-bottom: 16px;">
      <a-space>
        <a-input v-model:value="filters.keyword" placeholder="搜索用例名称" style="width: 200px" @pressEnter="fetchCases" />
        <a-select v-model:value="filters.case_type" placeholder="类型" style="width: 100px" allowClear>
          <a-select-option value="positive">正例</a-select-option>
          <a-select-option value="negative">反例</a-select-option>
        </a-select>
        <a-select v-model:value="filters.status" placeholder="状态" style="width: 100px" allowClear>
          <a-select-option value="pending">待执行</a-select-option>
          <a-select-option value="passed">通过</a-select-option>
          <a-select-option value="failed">失败</a-select-option>
          <a-select-option value="blocked">阻塞</a-select-option>
        </a-select>
        <a-button type="primary" @click="fetchCases">搜索</a-button>
        <a-button @click="resetFilters">重置</a-button>
      </a-space>
    </a-card>

    <!-- 用例表格 -->
    <a-table
      :columns="columns"
      :data-source="cases"
      :loading="loading"
      row-key="id"
      :pagination="pagination"
      @change="handleTableChange"
      size="small"
      :scroll="{ x: 1500 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <a @click="showEditModal(record)">{{ record.name }}</a>
        </template>
        <template v-else-if="column.key === 'case_type'">
          <a-tag :color="record.case_type === 'positive' ? 'green' : 'red'">
            {{ record.case_type === 'positive' ? '正例' : '反例' }}
          </a-tag>
        </template>
        <template v-else-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusText(record.status) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'expected_result'">
          <a-tooltip :title="record.expected_result">
            <span class="ellipsis-cell">{{ record.expected_result || '-' }}</span>
          </a-tooltip>
        </template>
        <template v-else-if="column.key === 'actual_result'">
          <a-tooltip :title="record.actual_result">
            <span class="ellipsis-cell">{{ record.actual_result || '-' }}</span>
          </a-tooltip>
        </template>
        <template v-else-if="column.key === 'issues'">
          <a-tooltip :title="record.issues">
            <span class="ellipsis-cell" style="color: #ff4d4f">{{ record.issues || '-' }}</span>
          </a-tooltip>
        </template>
        <template v-else-if="column.key === 'suites'">
          <a-tag v-for="s in (record.suites || [])" :key="s.id" color="blue">{{ s.name }}</a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="showEditModal(record)">编辑</a-button>
            <a-popconfirm title="确认删除？" @confirm="handleDelete(record.id)">
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 新建/编辑弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingCase ? '编辑用例' : '新建用例'"
      width="700px"
      @ok="handleSave"
      :confirm-loading="saving"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="用例名称" required>
              <a-input v-model:value="form.name" placeholder="如：正确用户名密码登录" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="类型">
              <a-radio-group v-model:value="form.case_type">
                <a-radio value="positive">正例</a-radio>
                <a-radio value="negative">反例</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="用例描述">
          <a-textarea v-model:value="form.description" placeholder="描述这个用例测试什么" :rows="2" />
        </a-form-item>
        <a-form-item label="测试URL">
          <a-input v-model:value="form.url" placeholder="http://example.com/login" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="关注点">
              <a-textarea v-model:value="form.focus_point" placeholder="这个用例重点关注什么" :rows="2" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="前提条件">
              <a-textarea v-model:value="form.preconditions" placeholder="执行前需要满足什么条件" :rows="2" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="预期结果" required>
          <a-textarea v-model:value="form.expected_result" placeholder="预期的正确行为/结果" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined } from '@ant-design/icons-vue'
import { testCases, generate } from '../api'

const loading = ref(false)
const cases = ref([])
const modalVisible = ref(false)
const saving = ref(false)
const editingCase = ref(null)

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

const filters = reactive({
  keyword: '',
  case_type: undefined,
  status: undefined,
})

const form = reactive({
  name: '',
  description: '',
  case_type: 'positive',
  url: '',
  focus_point: '',
  preconditions: '',
  expected_result: '',
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 50, fixed: 'left' },
  { title: '用例名称', dataIndex: 'name', key: 'name', width: 150, fixed: 'left' },
  { title: '类型', dataIndex: 'case_type', key: 'case_type', width: 70 },
  { title: '用例描述', dataIndex: 'description', key: 'description', width: 150, ellipsis: true },
  { title: '关注点', dataIndex: 'focus_point', key: 'focus_point', width: 120, ellipsis: true },
  { title: '前提条件', dataIndex: 'preconditions', key: 'preconditions', width: 120, ellipsis: true },
  { title: '预期结果', dataIndex: 'expected_result', key: 'expected_result', width: 150 },
  { title: '测试结果', dataIndex: 'actual_result', key: 'actual_result', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '执行时间', dataIndex: 'executed_at', key: 'executed_at', width: 150 },
  { title: '存在问题', dataIndex: 'issues', key: 'issues', width: 120 },
  { title: '关联套件', key: 'suites', width: 100 },
  { title: '操作', key: 'action', width: 100, fixed: 'right' },
]

function statusColor(s) {
  const map = { pending: 'default', passed: 'green', failed: 'red', blocked: 'orange' }
  return map[s] || 'default'
}

function statusText(s) {
  const map = { pending: '待执行', passed: '通过', failed: '失败', blocked: '阻塞' }
  return map[s] || s || '-'
}

async function fetchCases() {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...filters,
    }
    const { data } = await testCases.list(params)
    cases.value = data.items || []
    pagination.total = data.total || 0
  } catch (e) {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchCases()
}

function resetFilters() {
  filters.keyword = ''
  filters.case_type = undefined
  filters.status = undefined
  pagination.current = 1
  fetchCases()
}

function showCreateModal() {
  editingCase.value = null
  form.name = ''
  form.description = ''
  form.case_type = 'positive'
  form.url = ''
  form.focus_point = ''
  form.preconditions = ''
  form.expected_result = ''
  modalVisible.value = true
}

function showEditModal(record) {
  editingCase.value = record
  form.name = record.name
  form.description = record.description || ''
  form.case_type = record.case_type
  form.url = record.url || ''
  form.focus_point = record.focus_point || ''
  form.preconditions = record.preconditions || ''
  form.expected_result = record.expected_result || ''
  modalVisible.value = true
}

async function handleSave() {
  if (!form.name.trim()) {
    message.warning('请输入用例名称')
    return
  }
  saving.value = true
  try {
    if (editingCase.value) {
      await testCases.update(editingCase.value.id, form)
      message.success('更新成功')
    } else {
      await testCases.create(form)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchCases()
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  try {
    await testCases.delete(id)
    message.success('删除成功')
    fetchCases()
  } catch (e) {
    message.error('删除失败')
  }
}

async function handleImport(file) {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await generate.import(formData)
    message.success(data.message)
    fetchCases()
  } catch (e) {
    message.error('导入失败')
  }
  return false
}

onMounted(fetchCases)
</script>

<style scoped>
.ellipsis-cell {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
