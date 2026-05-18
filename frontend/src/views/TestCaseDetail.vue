<template>
  <div>
    <a-page-header :title="testCase.name" @back="goBack">
      <template #extra>
        <a-space>
          <a-button @click="goBack">返回列表</a-button>
          <a-popconfirm title="确认删除？" @confirm="handleDelete">
            <a-button danger>删除</a-button>
          </a-popconfirm>
        </a-space>
      </template>
    </a-page-header>

    <a-card>
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="用例名称">
              <a-input v-model:value="form.name" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="类型">
              <a-radio-group v-model:value="form.case_type">
                <a-radio value="positive">正例</a-radio>
                <a-radio value="negative">反例</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="状态">
              <a-select v-model:value="form.status" style="width: 100%">
                <a-select-option value="pending">待执行</a-select-option>
                <a-select-option value="passed">通过</a-select-option>
                <a-select-option value="failed">失败</a-select-option>
                <a-select-option value="blocked">阻塞</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="用例描述">
          <a-textarea v-model:value="form.description" :rows="2" />
        </a-form-item>

        <a-form-item label="测试URL">
          <a-input v-model:value="form.url" />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="关注点">
              <a-textarea v-model:value="form.focus_point" :rows="3" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="前提条件">
              <a-textarea v-model:value="form.preconditions" :rows="3" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="预期结果">
              <a-textarea v-model:value="form.expected_result" :rows="3" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="测试结果（实际）">
              <a-textarea v-model:value="form.actual_result" :rows="3" placeholder="执行后填写实际结果" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="存在问题">
          <a-textarea v-model:value="form.issues" :rows="2" placeholder="记录发现的Bug或问题" />
        </a-form-item>

        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSave" :loading="saving">保存</a-button>
            <span v-if="testCase.executed_at" style="color: #999">
              最后执行: {{ testCase.executed_at }}
            </span>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { testCases } from '../api'

const router = useRouter()
const route = useRoute()
const testCase = ref({})
const saving = ref(false)
const caseId = route.params.id

const form = reactive({
  name: '',
  description: '',
  case_type: 'positive',
  url: '',
  focus_point: '',
  preconditions: '',
  expected_result: '',
  actual_result: '',
  issues: '',
  status: 'pending',
})

function goBack() {
  router.push('/test-cases')
}

async function fetchTestCase() {
  try {
    const { data } = await testCases.get(caseId)
    testCase.value = data
    form.name = data.name
    form.description = data.description || ''
    form.case_type = data.case_type
    form.url = data.url || ''
    form.focus_point = data.focus_point || ''
    form.preconditions = data.preconditions || ''
    form.expected_result = data.expected_result || ''
    form.actual_result = data.actual_result || ''
    form.issues = data.issues || ''
    form.status = data.status
  } catch (e) {
    message.error('加载失败')
  }
}

async function handleSave() {
  saving.value = true
  try {
    await testCases.update(caseId, form)
    message.success('保存成功')
    fetchTestCase()
  } catch (e) {
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  try {
    await testCases.delete(caseId)
    message.success('删除成功')
    router.push('/test-cases')
  } catch (e) {
    message.error('删除失败')
  }
}

onMounted(fetchTestCase)
</script>
