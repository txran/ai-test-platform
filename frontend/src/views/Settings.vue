<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="margin: 0;">模型配置</h3>
      <a-button type="primary" @click="showCreateModal">
        <template #icon><PlusOutlined /></template>
        新增配置
      </a-button>
    </div>

    <a-table
      :columns="columns"
      :data-source="configs"
      :loading="loading"
      row-key="id"
      :pagination="false"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'is_default'">
          <a-tag v-if="record.is_default" color="green">默认</a-tag>
          <a-tag v-else>否</a-tag>
        </template>
        <template v-else-if="column.key === 'api_key'">
          {{ maskKey(record.api_key) }}
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="showEditModal(record)">编辑</a-button>
            <a-popconfirm title="确认删除该配置？" @confirm="handleDelete(record.id)">
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 新增/编辑弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingConfig ? '编辑配置' : '新增配置'"
      @ok="handleSave"
      :confirm-loading="saving"
      width="600px"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="配置名称" required>
          <a-input v-model:value="form.name" placeholder="如：GPT-4o" />
        </a-form-item>
        <a-form-item label="提供商">
          <a-input v-model:value="form.provider" placeholder="如：OpenAI" />
        </a-form-item>
        <a-form-item label="Base URL" required>
          <a-input v-model:value="form.base_url" placeholder="如：https://api.openai.com/v1" />
        </a-form-item>
        <a-form-item label="API Key" required>
          <a-input-password v-model:value="form.api_key" placeholder="请输入API Key" />
        </a-form-item>
        <a-form-item label="模型名称" required>
          <a-input v-model:value="form.model_name" placeholder="如：gpt-4o" />
        </a-form-item>
        <a-form-item label="设为默认">
          <a-switch v-model:checked="form.is_default" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { modelConfigs } from '../api'

const loading = ref(false)
const configs = ref([])
const modalVisible = ref(false)
const saving = ref(false)
const editingConfig = ref(null)

const form = reactive({
  name: '',
  provider: '',
  base_url: '',
  api_key: '',
  model_name: '',
  is_default: false,
})

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '提供商', dataIndex: 'provider', key: 'provider' },
  { title: 'Base URL', dataIndex: 'base_url', key: 'base_url', ellipsis: true },
  { title: '模型', dataIndex: 'model_name', key: 'model_name' },
  { title: 'API Key', dataIndex: 'api_key', key: 'api_key', width: 150 },
  { title: '默认', dataIndex: 'is_default', key: 'is_default', width: 80 },
  { title: '操作', key: 'action', width: 130 },
]

function maskKey(key) {
  if (!key) return '-'
  if (key.length <= 8) return '****'
  return key.substring(0, 4) + '****' + key.substring(key.length - 4)
}

async function fetchConfigs() {
  loading.value = true
  try {
    const { data } = await modelConfigs.list()
    configs.value = Array.isArray(data) ? data : (data.items || [])
  } catch (e) {
    message.error('加载配置失败')
  } finally {
    loading.value = false
  }
}

function showCreateModal() {
  editingConfig.value = null
  form.name = ''
  form.provider = ''
  form.base_url = ''
  form.api_key = ''
  form.model_name = ''
  form.is_default = false
  modalVisible.value = true
}

function showEditModal(record) {
  editingConfig.value = record
  form.name = record.name
  form.provider = record.provider || ''
  form.base_url = record.base_url
  form.api_key = record.api_key
  form.model_name = record.model_name
  form.is_default = record.is_default
  modalVisible.value = true
}

async function handleSave() {
  if (!form.name.trim() || !form.base_url.trim() || !form.api_key.trim() || !form.model_name.trim()) {
    message.warning('请填写必填项')
    return
  }
  saving.value = true
  try {
    const data = {
      name: form.name,
      provider: form.provider,
      base_url: form.base_url,
      api_key: form.api_key,
      model_name: form.model_name,
      is_default: form.is_default,
    }
    if (editingConfig.value) {
      await modelConfigs.update(editingConfig.value.id, data)
    } else {
      await modelConfigs.create(data)
    }
    message.success('保存成功')
    modalVisible.value = false
    fetchConfigs()
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  try {
    await modelConfigs.delete(id)
    message.success('删除成功')
    fetchConfigs()
  } catch (e) {
    message.error('删除失败')
  }
}

onMounted(fetchConfigs)
</script>
