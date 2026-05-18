<template>
  <div>
    <!-- 返回按钮 -->
    <a-button style="margin-bottom: 16px" @click="goBack">
      <template #icon><ArrowLeftOutlined /></template>
      返回
    </a-button>

    <!-- 执行信息 -->
    <a-card title="执行信息" style="margin-bottom: 16px">
      <a-descriptions :column="3" bordered size="small">
        <a-descriptions-item label="执行ID">{{ execution.id }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="statusColor(execution.status)">{{ statusText(execution.status) }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="结果">
          <span v-if="execution.status === 'passed'">
            <span style="color: #52c41a">{{ execution.passed_cases || 0 }} 通过</span>
            <span v-if="execution.failed_cases > 0" style="color: #ff4d4f; margin-left: 8px">{{ execution.failed_cases }} 失败</span>
          </span>
          <span v-else>-</span>
        </a-descriptions-item>
        <a-descriptions-item label="耗时">
          {{ execution.duration ? `${execution.duration}s` : '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="开始时间">{{ execution.start_time || '-' }}</a-descriptions-item>
        <a-descriptions-item label="结束时间">{{ execution.end_time || '-' }}</a-descriptions-item>
      </a-descriptions>
    </a-card>

    <!-- 错误信息 -->
    <a-card v-if="execution.error_message" title="错误信息" style="margin-bottom: 16px">
      <a-alert :message="execution.error_message" type="error" show-icon />
    </a-card>

    <!-- 用例结果 -->
    <a-card title="用例结果" style="margin-bottom: 16px">
      <a-table
        :columns="resultColumns"
        :data-source="caseResults"
        :pagination="false"
        size="small"
        :row-class-name="rowClassName"
        :custom-row="onClickRow"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'passed' ? 'green' : 'red'">
              {{ record.status === 'passed' ? '通过' : '失败' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'screenshots'">
            <span>{{ getCaseScreenshots(record.case_id).length }} 张</span>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 选中用例的截图 -->
    <a-card v-if="selectedCase" :title="`截图 - ${selectedCase.case_name}`" style="margin-bottom: 16px">
      <div v-if="selectedCaseScreenshots.length === 0">
        <a-empty description="该用例暂无截图" />
      </div>
      <div v-else>
        <div v-for="s in selectedCaseScreenshots" :key="s.id" style="text-align: center; padding: 16px;">
          <div style="margin-bottom: 8px; font-weight: bold;">
            步骤 {{ s.step_number }}: {{ s.step_description || '' }}
          </div>
          <img
            :src="s.screenshot_path"
            :alt="`步骤 ${s.step_number}`"
            style="max-width: 100%; max-height: 500px; border: 1px solid #e8e8e8; border-radius: 4px;"
          />
        </div>
      </div>
    </a-card>
    <a-card v-else title="截图" style="margin-bottom: 16px">
      <a-empty description="点击上方用例查看对应截图" />
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ArrowLeftOutlined, LeftCircleOutlined, RightCircleOutlined } from '@ant-design/icons-vue'
import { executions as execApi } from '../api'

const route = useRoute()
const router = useRouter()
const execId = computed(() => route.params.id)

const execution = ref({})
const screenshots = ref([])
const caseResults = ref([])

const resultColumns = [
  { title: '用例ID', dataIndex: 'case_id', key: 'case_id', width: 80 },
  { title: '用例名称', dataIndex: 'case_name', key: 'case_name', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '截图', key: 'screenshots', width: 80 },
  { title: '错误信息', dataIndex: 'error_message', key: 'error_message', ellipsis: true },
]

const selectedCase = ref(null)

const selectedCaseScreenshots = computed(() => {
  if (!selectedCase.value) return []
  return screenshots.value.filter(s => s.case_id === selectedCase.value.case_id)
})

function getCaseScreenshots(caseId) {
  return screenshots.value.filter(s => s.case_id === caseId)
}

function rowClassName(record) {
  return selectedCase.value && selectedCase.value.case_id === record.case_id ? 'ant-table-row-selected' : ''
}

function onClickRow(record) {
  return {
    onClick: (event) => {
      selectedCase.value = record
    }
  }
}

function statusColor(s) {
  const map = { pending: 'default', running: 'processing', passed: 'green', error: 'orange' }
  return map[s] || 'default'
}

function statusText(s) {
  const map = { pending: '待执行', running: '运行中', passed: '成功', error: '错误' }
  return map[s] || s || '-'
}

function goBack() {
  router.back()
}

async function fetchExecution() {
  try {
    const { data } = await execApi.get(execId.value)
    execution.value = data
    caseResults.value = data.case_results || []
  } catch (e) {
    message.error('加载执行信息失败')
  }
}

async function fetchScreenshots() {
  try {
    const { data } = await execApi.screenshots(execId.value)
    screenshots.value = data.screenshots || []
  } catch (e) {
    screenshots.value = []
  }
}

onMounted(() => {
  fetchExecution()
  fetchScreenshots()
})
</script>

<style scoped>
:deep(.slick-dots li button) {
  background: #999;
}

:deep(.custom-slick-arrow) {
  width: 25px;
  height: 25px;
  font-size: 25px;
  color: #fff;
  background-color: rgba(31, 45, 61, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
}

:deep(.custom-slick-arrow:hover) {
  background-color: rgba(31, 45, 61, 0.8);
}
</style>
