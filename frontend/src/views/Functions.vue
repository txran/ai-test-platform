<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="margin: 0;">功能管理</h3>
      <a-button type="primary" @click="showCreateModal">
        <template #icon><PlusOutlined /></template>
        新建功能
      </a-button>
    </div>

    <!-- 功能列表 -->
    <a-table
      :columns="columns"
      :data-source="functionList"
      :loading="loading"
      row-key="id"
      :pagination="pagination"
      @change="handleTableChange"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <a @click="goToDetail(record.id)">{{ record.name }}</a>
        </template>
        <template v-else-if="column.key === 'cases_count'">
          <a-tag color="blue">{{ record.cases_count }} 个用例</a-tag>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="goToDetail(record.id)">详情</a-button>
            <a-button type="link" size="small" @click="showEditModal(record)">编辑</a-button>
            <a-popconfirm title="确认删除该功能及其所有用例？" @confirm="handleDelete(record.id)">
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 新建/编辑弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingFunc ? '编辑功能' : '新建功能'"
      @ok="handleSave"
      :confirm-loading="saving"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="功能名称" required>
          <a-input v-model:value="form.name" placeholder="如：登录功能、商品管理" />
        </a-form-item>
        <a-form-item label="功能描述">
          <a-textarea v-model:value="form.description" placeholder="描述这个功能模块的作用" :rows="3" />
        </a-form-item>
        <a-form-item label="功能URL">
        <a-input v-model:value="form.url" placeholder="如：http://192.168.5.200:5001/login" />
        <div style="color: #999; font-size: 12px; margin-top: 4px;">
          该功能对应的测试页面完整URL，生成脚本时会使用此地址
        </div>
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
import { functions } from '../api'

const router = useRouter()
const loading = ref(false)
const functionList = ref([])
const modalVisible = ref(false)
const saving = ref(false)
const editingFunc = ref(null)

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  name: '',
  description: '',
  url: '',
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '功能名称', dataIndex: 'name', key: 'name' },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: 'URL', dataIndex: 'url', key: 'url', ellipsis: true },
  { title: '用例数', dataIndex: 'cases_count', key: 'cases_count', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' },
]

async function fetchFunctions() {
  loading.value = true
  try {
    const { data } = await functions.list({
      page: pagination.current,
      page_size: pagination.pageSize,
    })
    functionList.value = data.items || []
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
  fetchFunctions()
}

function goToDetail(id) {
  router.push(`/functions/${id}`)
}

function showCreateModal() {
  editingFunc.value = null
  form.name = ''
  form.description = ''
  form.url = ''
  modalVisible.value = true
}

function showEditModal(record) {
  editingFunc.value = record
  form.name = record.name
  form.description = record.description || ''
  form.url = record.url || ''
  modalVisible.value = true
}

async function handleSave() {
  if (!form.name.trim()) {
    message.warning('请输入功能名称')
    return
  }
  saving.value = true
  try {
    if (editingFunc.value) {
      await functions.update(editingFunc.value.id, form)
      message.success('更新成功')
    } else {
      await functions.create(form)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchFunctions()
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  try {
    await functions.delete(id)
    message.success('删除成功')
    fetchFunctions()
  } catch (e) {
    message.error('删除失败')
  }
}

onMounted(fetchFunctions)
</script>
