<template>
  <div>
    <a-page-header :title="func.name" @back="goBack">
      <template #extra>
        <a-space>
          <a-button @click="goBack">返回列表</a-button>
          <a-dropdown>
            <a-button type="primary">
              添加用例 <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu @click="handleAddMenuClick">
                <a-menu-item key="manual">
                  <FormOutlined /> 手动创建
                </a-menu-item>
                <a-menu-item key="url">
                  <LinkOutlined /> 从URL生成
                </a-menu-item>
                <a-menu-item key="prd">
                  <FileTextOutlined /> 从PRD文档生成
                </a-menu-item>
                <a-menu-item key="excel">
                  <FileExcelOutlined /> 从Excel导入
                </a-menu-item>
                <a-menu-item key="description">
                  <EditOutlined /> 从描述生成
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </template>
      <a-descriptions size="small" :column="3">
        <a-descriptions-item label="描述">{{ func.description || '-' }}</a-descriptions-item>
        <a-descriptions-item label="URL">{{ func.url || '-' }}</a-descriptions-item>
        <a-descriptions-item label="用例数">{{ cases.length }}</a-descriptions-item>
      </a-descriptions>
    </a-page-header>

    <!-- 用例表格 -->
    <a-table
      :columns="columns"
      :data-source="cases"
      :loading="loading"
      row-key="id"
      :pagination="false"
      size="small"
      :scroll="{ x: 1400 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <a @click="showEditCase(record)">{{ record.name }}</a>
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
        <template v-else-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="showEditCase(record)">编辑</a-button>
            <a-popconfirm title="确认删除该用例？" @confirm="handleDeleteCase(record.id)">
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 1. 手动创建/编辑用例弹窗 -->
    <a-modal
      v-model:open="caseModalVisible"
      :title="editingCase ? '编辑用例' : '添加用例'"
      width="700px"
      @ok="handleSaveCase"
      :confirm-loading="savingCase"
    >
      <a-form :model="caseForm" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="16">
            <a-form-item label="用例名称" required>
              <a-input v-model:value="caseForm.name" placeholder="如：正确用户名密码登录" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="类型">
              <a-radio-group v-model:value="caseForm.case_type">
                <a-radio value="positive">正例</a-radio>
                <a-radio value="negative">反例</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="用例描述">
          <a-textarea v-model:value="caseForm.description" placeholder="描述这个用例测试什么" :rows="2" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="关注点">
              <a-textarea v-model:value="caseForm.focus_point" placeholder="重点关注什么" :rows="2" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="前提条件">
              <a-textarea v-model:value="caseForm.preconditions" placeholder="执行前需要什么条件" :rows="2" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="预期结果" required>
          <a-textarea v-model:value="caseForm.expected_result" placeholder="预期的正确行为" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 2. 从URL生成弹窗 -->
    <a-modal
      v-model:open="urlModalVisible"
      title="从URL生成用例"
      @ok="handleGenerateFromUrl"
      :confirm-loading="urlGenerating"
    >
      <a-form layout="vertical">
        <a-form-item label="页面URL" required>
          <a-input v-model:value="urlForm.url" placeholder="http://192.168.5.200:5001/login" />
        </a-form-item>
        <a-form-item label="页面描述（可选，帮助AI更好理解）">
          <a-textarea v-model:value="urlForm.description" placeholder="这是一个登录页面，包含用户名和密码输入框..." :rows="3" />
        </a-form-item>
      </a-form>
      <a-alert v-if="urlGenerating" type="info" show-icon style="margin-top: 12px">
        <template #message>AI正在分析页面并生成用例，请稍候...</template>
      </a-alert>
    </a-modal>

    <!-- 3. 从PRD文档生成弹窗 -->
    <a-modal
      v-model:open="prdModalVisible"
      title="从PRD文档生成用例"
      @ok="handleGenerateFromPrd"
      :confirm-loading="prdGenerating"
    >
      <a-tabs v-model:activeKey="prdTab">
        <a-tab-pane key="upload" tab="上传文档">
          <a-upload-dragger
            :before-upload="beforePrdUpload"
            :file-list="prdFileList"
            :remove="removePrdFile"
            accept=".txt,.doc,.docx"
          >
            <p class="ant-upload-drag-icon"><InboxOutlined /></p>
            <p class="ant-upload-text">点击或拖拽文件到此处</p>
            <p class="ant-upload-hint">支持 txt、doc、docx 格式</p>
          </a-upload-dragger>
        </a-tab-pane>
        <a-tab-pane key="text" tab="粘贴文本">
          <a-textarea
            v-model:value="prdText"
            placeholder="将需求文档内容粘贴到这里..."
            :rows="10"
          />
        </a-tab-pane>
      </a-tabs>
      <a-alert v-if="prdGenerating" type="info" show-icon style="margin-top: 12px">
        <template #message>AI正在分析文档并生成用例，请稍候...</template>
      </a-alert>
    </a-modal>

    <!-- 4. 从Excel导入弹窗 -->
    <a-modal
      v-model:open="excelModalVisible"
      title="从Excel导入用例"
      @ok="handleImportExcel"
      :confirm-loading="excelImporting"
    >
      <a-upload-dragger
        :before-upload="beforeExcelUpload"
        :file-list="excelFileList"
        :remove="removeExcelFile"
        accept=".xlsx,.xls"
      >
        <p class="ant-upload-drag-icon"><InboxOutlined /></p>
        <p class="ant-upload-text">点击或拖拽Excel文件到此处</p>
        <p class="ant-upload-hint">支持 xlsx、xls 格式</p>
      </a-upload-dragger>
      <a-alert type="info" show-icon style="margin-top: 12px">
        <template #message>
          <div>Excel表头应包含以下列：</div>
          <div style="font-size: 12px; color: #666; margin-top: 4px">
            用例名称（必填）、类型、描述、关注点、前提条件、预期结果
          </div>
          <div style="font-size: 12px; color: #666">
            类型列填"正例"或"反例"，默认为正例
          </div>
        </template>
      </a-alert>
    </a-modal>

    <!-- 5. 从描述生成弹窗 -->
    <a-modal
      v-model:open="descriptionModalVisible"
      title="从自然语言描述生成"
      :footer="null"
      width="600px"
    >
      <a-form>
        <a-form-item label="功能描述">
          <a-textarea
            v-model:value="descriptionText"
            :rows="8"
            placeholder="请描述要测试的功能，例如：

用户登录功能：
- 支持用户名/密码登录
- 密码错误时提示错误
- 连续5次错误锁定账户
- 登录成功跳转首页"
          />
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            @click="generateFromDescription"
            :loading="generatingDesc"
          >
            <ThunderboltOutlined /> 生成用例
          </a-button>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  DownOutlined, FormOutlined, LinkOutlined,
  FileTextOutlined, FileExcelOutlined, InboxOutlined,
  EditOutlined, ThunderboltOutlined
} from '@ant-design/icons-vue'
import { functions, testCases, generate } from '../api'

const router = useRouter()
const route = useRoute()
const funcId = route.params.id

const func = ref({})
const cases = ref([])
const loading = ref(false)

// 手动创建
const caseModalVisible = ref(false)
const savingCase = ref(false)
const editingCase = ref(null)
const caseForm = reactive({
  name: '',
  description: '',
  case_type: 'positive',
  focus_point: '',
  preconditions: '',
  expected_result: '',
})

// URL生成
const urlModalVisible = ref(false)
const urlGenerating = ref(false)
const urlForm = reactive({ url: '', description: '' })

// PRD生成
const prdModalVisible = ref(false)
const prdGenerating = ref(false)
const prdTab = ref('upload')
const prdFile = ref(null)
const prdFileList = ref([])
const prdText = ref('')

// Excel导入
const excelModalVisible = ref(false)
const excelImporting = ref(false)
const excelFile = ref(null)
const excelFileList = ref([])


// 从描述生成
const descriptionModalVisible = ref(false)
const generatingDesc = ref(false)
const descriptionText = ref("")
const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 50, fixed: 'left' },
  { title: '用例名称', dataIndex: 'name', key: 'name', width: 150, fixed: 'left' },
  { title: '类型', dataIndex: 'case_type', key: 'case_type', width: 70 },
  { title: '描述', dataIndex: 'description', key: 'description', width: 120, ellipsis: true },
  { title: '关注点', dataIndex: 'focus_point', key: 'focus_point', width: 100, ellipsis: true },
  { title: '前提条件', dataIndex: 'preconditions', key: 'preconditions', width: 100, ellipsis: true },
  { title: '预期结果', dataIndex: 'expected_result', key: 'expected_result', width: 150 },
  { title: '测试结果', dataIndex: 'actual_result', key: 'actual_result', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '存在问题', dataIndex: 'issues', key: 'issues', width: 100 },
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

function goBack() {
  router.push('/functions')
}

async function fetchFunction() {
  loading.value = true
  try {
    const { data } = await functions.get(funcId)
    func.value = data
    cases.value = data.cases || []
  } catch (e) {
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

// === 菜单点击 ===
function handleAddMenuClick({ key }) {
  if (key === 'manual') showAddCase()
  else if (key === 'url') showUrlModal()
  else if (key === 'prd') showPrdModal()
  else if (key === 'excel') showExcelModal()
  else if (key === "description") descriptionModalVisible.value = true
}

// === 1. 手动创建 ===
function showAddCase() {
  editingCase.value = null
  caseForm.name = ''
  caseForm.description = ''
  caseForm.case_type = 'positive'
  caseForm.focus_point = ''
  caseForm.preconditions = ''
  caseForm.expected_result = ''
  caseModalVisible.value = true
}

function showEditCase(record) {
  editingCase.value = record
  caseForm.name = record.name
  caseForm.description = record.description || ''
  caseForm.case_type = record.case_type
  caseForm.focus_point = record.focus_point || ''
  caseForm.preconditions = record.preconditions || ''
  caseForm.expected_result = record.expected_result || ''
  caseModalVisible.value = true
}

async function handleSaveCase() {
  if (!caseForm.name.trim()) {
    message.warning('请输入用例名称')
    return
  }
  savingCase.value = true
  try {
    if (editingCase.value) {
      await testCases.update(editingCase.value.id, caseForm)
      message.success('更新成功')
    } else {
      await functions.createCase(funcId, caseForm)
      message.success('添加成功')
    }
    caseModalVisible.value = false
    fetchFunction()
  } catch (e) {
    message.error('保存失败')
  } finally {
    savingCase.value = false
  }
}

async function handleDeleteCase(caseId) {
  try {
    await testCases.delete(caseId)
    message.success('删除成功')
    fetchFunction()
  } catch (e) {
    message.error('删除失败')
  }
}

// === 2. URL生成 ===
function showUrlModal() {
  urlForm.url = func.value.url || ''
  urlForm.description = ''
  urlModalVisible.value = true
}

async function handleGenerateFromUrl() {
  if (!urlForm.url.trim()) {
    message.warning('请输入URL')
    return
  }
  urlGenerating.value = true
  try {
    const { data } = await generate.fromUrl({
      url: urlForm.url,
      description: urlForm.description,
      function_id: parseInt(funcId),
    })
    message.success(data.message)
    urlModalVisible.value = false
    fetchFunction()
  } catch (e) {
    message.error(e.response?.data?.detail || '生成失败')
  } finally {
    urlGenerating.value = false
  }
}

// === 3. PRD文档生成 ===
function showPrdModal() {
  prdFile.value = null
  prdFileList.value = []
  prdText.value = ''
  prdTab.value = 'upload'
  prdModalVisible.value = true
}

function beforePrdUpload(file) {
  prdFile.value = file
  prdFileList.value = [file]
  return false
}

function removePrdFile() {
  prdFile.value = null
  prdFileList.value = []
}

async function handleGenerateFromPrd() {
  prdGenerating.value = true
  try {
    if (prdTab.value === 'upload' && prdFile.value) {
      // 上传文件
      const formData = new FormData()
      formData.append('function_id', funcId)
      formData.append('file', prdFile.value)
      const { data } = await generate.uploadPrd(formData)
      message.success(data.message)
    } else if (prdTab.value === 'text' && prdText.value.trim()) {
      // 粘贴文本
      const { data } = await generate.fromPrd({
        content: prdText.value,
        function_id: parseInt(funcId),
      })
      message.success(data.message)
    } else {
      message.warning('请上传文档或粘贴文本')
      prdGenerating.value = false
      return
    }
    prdModalVisible.value = false
    fetchFunction()
  } catch (e) {
    message.error(e.response?.data?.detail || '生成失败')
  } finally {
    prdGenerating.value = false
  }
}

// === 4. Excel导入 ===
function showExcelModal() {
  excelFile.value = null
  excelFileList.value = []
  excelModalVisible.value = true
}

function beforeExcelUpload(file) {
  excelFile.value = file
  excelFileList.value = [file]
  return false
}

function removeExcelFile() {
  excelFile.value = null
  excelFileList.value = []
}

async function handleImportExcel() {
  if (!excelFile.value) {
    message.warning('请选择Excel文件')
    return
  }
  excelImporting.value = true
  try {
    const formData = new FormData()
    formData.append('function_id', funcId)
    formData.append('file', excelFile.value)
    const { data } = await generate.importExcel(formData)
    message.success(data.message)
    excelModalVisible.value = false
    fetchFunction()
  } catch (e) {
    message.error(e.response?.data?.detail || '导入失败')
  } finally {
    excelImporting.value = false
  }
}


// === 5. 从描述生成 ===
async function generateFromDescription() {
  if (!descriptionText.value.trim()) {
    message.warning("请输入功能描述")
    return
  }
  
  generatingDesc.value = true
  try {
    const formData = new FormData()
    formData.append("description", descriptionText.value)
    
    const { data } = await generate.fromDescription(route.params.id, formData)
    message.success(data.message)
    descriptionModalVisible.value = false
    descriptionText.value = ""
    fetchFunction()
  } catch (e) {
    message.error(e.response?.data?.detail || "生成失败")
  } finally {
    generatingDesc.value = false
  }
}
onMounted(fetchFunction)
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
