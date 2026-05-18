<template>
  <div>
    <a-page-header title="场景详情" @back="goBack">
      <template #extra>
        <a-space>
          <a-button @click="goBack">返回列表</a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 套件信息 -->
    <a-card style="margin-bottom: 16px">
      <a-descriptions :column="3" bordered size="small">
        <a-descriptions-item label="名称">{{ suite.name }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="statusColor(suite.status)">{{ statusText(suite.status) }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="描述" :span="3">{{ suite.description || '-' }}</a-descriptions-item>
        <a-descriptions-item label="创建时间">{{ suite.created_at }}</a-descriptions-item>
      </a-descriptions>
    </a-card>

    <!-- 操作栏 -->
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3 style="margin: 0;">关联功能</h3>
      <a-space>
        <a-button type="primary" @click="showSelectFunction">
          <template #icon><PlusOutlined /></template>
          添加功能
        </a-button>
        <a-button @click="handleGenerateScript" :loading="generating">
          <template #icon><ThunderboltOutlined /></template>
          生成脚本
        </a-button>
        <a-button type="primary" danger @click="handleExecute" :loading="executing">
          <template #icon><PlayCircleOutlined /></template>
          执行
        </a-button>
      </a-space>
    </div>

    <!-- 功能列表（带用例） -->
    <a-collapse v-if="suiteFunctions.length > 0" style="margin-bottom: 24px">
      <a-collapse-panel v-for="func in suiteFunctions" :key="func.id" :header="func.name">
        <template #extra>
          <a-space>
            <a-tag>{{ func.cases?.length || 0 }} 个用例</a-tag>
            <a-button type="link" size="small" danger @click.stop="handleRemoveFunction(func.id)">移除</a-button>
          </a-space>
        </template>
        <a-table
          :columns="caseColumns"
          :data-source="func.cases || []"
          :pagination="false"
          size="small"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'case_type'">
              <a-tag :color="record.case_type === 'positive' ? 'green' : 'red'">
                {{ record.case_type === 'positive' ? '正例' : '反例' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="caseStatusColor(record.status)">{{ caseStatusText(record.status) }}</a-tag>
            </template>
          </template>
        </a-table>
      </a-collapse-panel>
    </a-collapse>
    <a-empty v-else description="暂未关联功能，请先添加功能" style="margin-bottom: 24px" />

    <!-- 当前脚本 -->
    <a-card title="当前脚本" style="margin-bottom: 16px" size="small">
      <pre v-if="currentScript" class="code-block">{{ currentScript.script_content }}</pre>
      <a-empty v-else description="暂无脚本，请先生成脚本" />
    </a-card>

    <!-- 执行历史 -->
    <a-card title="执行历史" size="small">
      <a-table
        :columns="execColumns"
        :data-source="executions"
        :loading="execLoading"
        row-key="id"
        :pagination="false"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="execStatusColor(record.status)">{{ execStatusText(record.status) }}</a-tag>
          </template>
          <template v-else-if="column.key === 'result'">
            <span v-if="record.status === 'passed'">
              <span style="color: #52c41a">{{ record.passed_cases || 0 }} 通过</span>
              <span v-if="record.failed_cases > 0" style="color: #ff4d4f; margin-left: 8px">{{ record.failed_cases }} 失败</span>
            </span>
            <span v-else-if="record.status === 'error'" style="color: #ff4d4f">-</span>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'duration'">
            {{ record.duration ? `${record.duration}s` : '-' }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" size="small" @click="goToExecution(record.id)">查看详情</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 选择功能弹窗 -->
    <a-modal
      v-model:open="selectFuncVisible"
      title="选择功能"
      width="600px"
      @ok="handleAddFunctions"
      :confirm-loading="addingFunctions"
    >
      <a-table
        :columns="funcColumns"
        :data-source="availableFunctions"
        :loading="funcLoading"
        row-key="id"
        :pagination="false"
        size="small"
        :row-selection="{ selectedRowKeys: selectedFuncIds, onChange: onSelectChange }"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined, ThunderboltOutlined, PlayCircleOutlined } from '@ant-design/icons-vue'
import { suites, functions as funcApi, executions as execApi } from '../api'

const route = useRoute()
const router = useRouter()
const suiteId = route.params.id

const suite = ref({})
const suiteFunctions = ref([])
const currentScript = ref(null)
const executions = ref([])

const execLoading = ref(false)
const generating = ref(false)
const executing = ref(false)

const selectFuncVisible = ref(false)
const availableFunctions = ref([])
const funcLoading = ref(false)
const selectedFuncIds = ref([])
const addingFunctions = ref(false)

const caseColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 50 },
  { title: '用例名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'case_type', key: 'case_type', width: 70 },
  { title: '关注点', dataIndex: 'focus_point', key: 'focus_point', ellipsis: true },
  { title: '前提条件', dataIndex: 'preconditions', key: 'preconditions', ellipsis: true },
  { title: '预期结果', dataIndex: 'expected_result', key: 'expected_result', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
]

const funcColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '功能名称', dataIndex: 'name', key: 'name' },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '用例数', dataIndex: 'cases_count', key: 'cases_count', width: 80 },
]

const execColumns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 90 },
  { title: '结果', key: 'result', width: 120 },
  { title: '开始时间', dataIndex: 'start_time', key: 'start_time', width: 180 },
  { title: '耗时', dataIndex: 'duration', key: 'duration', width: 100 },
  { title: '错误信息', dataIndex: 'error_message', key: 'error_message', ellipsis: true },
  { title: '操作', key: 'action', width: 100 },
]

function goBack() { router.push('/') }
function goToExecution(id) { router.push(`/executions/${id}`) }

function statusColor(s) { return { draft: 'default', active: 'green', inactive: 'red' }[s] || 'default' }
function statusText(s) { return { draft: '草稿', active: '活跃', inactive: '停用' }[s] || s || '-' }
function caseStatusColor(s) { return { pending: 'default', passed: 'green', failed: 'red', blocked: 'orange' }[s] || 'default' }
function caseStatusText(s) { return { pending: '待执行', passed: '通过', failed: '失败', blocked: '阻塞' }[s] || s || '-' }
function execStatusColor(s) { return { pending: 'default', running: 'processing', passed: 'green', error: 'orange' }[s] || 'default' }
function execStatusText(s) { return { pending: '待执行', running: '运行中', passed: '成功', error: '错误' }[s] || s }

async function fetchSuite() {
  try {
    const { data } = await suites.get(suiteId)
    suite.value = data
  } catch (e) { message.error('加载套件失败') }
}

async function fetchSuiteFunctions() {
  try {
    const { data } = await suites.listFunctions(suiteId)
    suiteFunctions.value = Array.isArray(data) ? data : []
  } catch (e) { suiteFunctions.value = [] }
}

async function fetchScript() {
  try {
    const { data } = await suites.listScripts(suiteId)
    const scripts = Array.isArray(data) ? data : []
    const current = scripts.find(s => s.is_current)
    if (current) {
      const { data: detail } = await suites.getScript(current.id)
      currentScript.value = detail
    } else { currentScript.value = null }
  } catch (e) { currentScript.value = null }
}

async function fetchExecutions() {
  execLoading.value = true
  try {
    const { data } = await suites.listExecutions(suiteId)
    executions.value = Array.isArray(data) ? data : []
  } catch (e) { executions.value = [] }
  finally { execLoading.value = false }
}

function showSelectFunction() {
  selectFuncVisible.value = true
  selectedFuncIds.value = []
  fetchAvailableFunctions()
}

async function fetchAvailableFunctions() {
  funcLoading.value = true
  try {
    const { data } = await funcApi.list({ page_size: 100 })
    availableFunctions.value = data.items || []
  } catch (e) { availableFunctions.value = [] }
  finally { funcLoading.value = false }
}

function onSelectChange(keys) { selectedFuncIds.value = keys }

async function handleAddFunctions() {
  if (selectedFuncIds.value.length === 0) { message.warning('请选择至少一个功能'); return }
  addingFunctions.value = true
  try {
    await suites.addFunctions(suiteId, selectedFuncIds.value)
    message.success('添加成功')
    selectFuncVisible.value = false
    fetchSuiteFunctions()
  } catch (e) { message.error('添加失败') }
  finally { addingFunctions.value = false }
}

async function handleRemoveFunction(funcId) {
  try {
    await suites.removeFunction(suiteId, funcId)
    message.success('移除成功')
    fetchSuiteFunctions()
  } catch (e) { message.error('移除失败') }
}

async function handleGenerateScript() {
  if (suiteFunctions.value.length === 0) { message.warning('请先添加功能'); return }
  generating.value = true
  
  // 显示生成中提示
  const hide = message.loading('正在生成测试脚本，请稍候...', 0)
  
  try {
    await suites.generateScript(suiteId)
    hide()
    message.success('脚本生成完成', 3)
    await fetchScript()
  } catch (e) {
    hide()
    message.error('生成失败：' + (e.message || '请检查网络连接'), 5)
  } finally {
    generating.value = false
  }
}

async function handleExecute() {
  if (!currentScript.value) { message.warning('请先生成脚本'); return }
  executing.value = true
  
  // 显示执行中提示
  let hide = null
  
  try {
    // 提交执行任务
    const { data: execResult } = await suites.execute(suiteId, { headless: true })
    const executionId = execResult?.id
    
    if (!executionId) {
      throw new Error('未获取到执行ID')
    }
    
    // 初始提示
    hide = message.loading('测试执行中...', 0)
    
    // 轮询检查执行状态
    let attempts = 0
    const maxAttempts = 240 // 最多等待10分钟 (240 * 2.5s)
    let lastProgress = ''
    
    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2500)) // 等待2.5秒
      attempts++
      
      try {
        const { data: execStatus } = await execApi.get(executionId)
        
        // 更新进度提示（只在进度变化时更新）
        if (execStatus.total_cases > 0) {
          const progress = Math.round((execStatus.completed_cases / execStatus.total_cases) * 100)
          const progressText = `${execStatus.completed_cases}/${execStatus.total_cases} (${progress}%)`
          
          if (progressText !== lastProgress) {
            lastProgress = progressText
            if (hide) hide() // 关闭旧提示
            hide = message.loading(`测试执行中... ${progressText}`, 0)
          }
        }
        
        if (execStatus.status === 'passed' || execStatus.status === 'error') {
          // 执行完成
          if (hide) hide()
          if (execStatus.status === 'passed') {
            const passed = execStatus.passed_cases || 0
            const failed = execStatus.failed_cases || 0
            const total = execStatus.total_cases || 0
            message.success(`测试执行完成！耗时 ${execStatus.duration || '?'}秒，${passed}/${total} 通过`, 5)
          } else {
            message.error(`执行出错：${execStatus.error_message || '未知错误'}`, 5)
          }
          // 刷新执行列表和脚本
          await fetchExecutions()
          await fetchScript()
          return
        } else if (execStatus.status === 'error') {
          if (hide) hide()
          message.error(`执行出错：${execStatus.error_message || '未知错误'}`, 5)
          await fetchExecutions()
          return
        }
        // 继续等待...
      } catch (pollError) {
        // 轮询失败不影响继续
        console.warn('轮询状态失败:', pollError)
      }
    }
    
    // 超时
    if (hide) hide()
    message.warning('执行超时，请手动刷新查看结果', 5)
    await fetchExecutions()
    
  } catch (e) {
    if (hide) hide()
    message.error('执行失败：' + (e.message || '请检查网络连接'), 5)
  } finally {
    executing.value = false
  }
}

onMounted(() => {
  fetchSuite()
  fetchSuiteFunctions()
  fetchScript()
  fetchExecutions()
})
</script>

<style scoped>
.code-block {
  background: #f5f5f5;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
}
</style>
