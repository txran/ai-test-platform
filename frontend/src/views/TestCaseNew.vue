<template>
  <div>
    <a-page-header title="新建测试用例" @back="goBack" />

    <a-card>
      <a-tabs v-model:activeKey="activeTab">
        <!-- 手动创建 -->
        <a-tab-pane key="manual" tab="手动创建">
          <a-form :model="manualForm" layout="vertical" style="max-width: 600px">
            <a-form-item label="用例名称" required>
              <a-input v-model:value="manualForm.name" placeholder="如：正确用户名密码登录" />
            </a-form-item>
            <a-form-item label="用例类型">
              <a-radio-group v-model:value="manualForm.case_type">
                <a-radio value="positive">正例</a-radio>
                <a-radio value="negative">反例</a-radio>
              </a-radio-group>
            </a-form-item>
            <a-form-item label="测试URL">
              <a-input v-model:value="manualForm.url" placeholder="http://example.com/login" />
            </a-form-item>
            <a-form-item label="输入数据 (JSON)">
              <a-textarea v-model:value="manualForm.input_data_str" placeholder='{"username": "admin", "password": "123456"}' :rows="4" />
            </a-form-item>
            <a-form-item label="预期结果">
              <a-textarea v-model:value="manualForm.expected_result" placeholder="描述预期的正确行为" :rows="3" />
            </a-form-item>
            <a-form-item>
              <a-button type="primary" @click="handleManualCreate" :loading="creating">创建</a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <!-- 从URL生成 -->
        <a-tab-pane key="url" tab="从URL生成">
          <a-form :model="urlForm" layout="vertical" style="max-width: 600px">
            <a-form-item label="页面URL" required>
              <a-input v-model:value="urlForm.url" placeholder="http://example.com/login" />
            </a-form-item>
            <a-form-item label="页面描述（可选）">
              <a-textarea v-model:value="urlForm.description" placeholder="描述页面功能，如：这是一个登录页面，包含用户名和密码输入框" :rows="4" />
            </a-form-item>
            <a-form-item>
              <a-button type="primary" @click="handleUrlGenerate" :loading="generating">AI生成用例</a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <!-- 从Swagger生成 -->
        <a-tab-pane key="swagger" tab="从Swagger生成">
          <a-form :model="swaggerForm" layout="vertical" style="max-width: 600px">
            <a-form-item label="Swagger JSON内容" required>
              <a-textarea v-model:value="swaggerForm.content" placeholder="粘贴Swagger/OpenAPI JSON内容" :rows="10" />
            </a-form-item>
            <a-form-item>
              <a-upload :before-upload="handleSwaggerFile" :show-upload-list="false" accept=".json">
                <a-button>上传JSON文件</a-button>
              </a-upload>
            </a-form-item>
            <a-form-item>
              <a-button type="primary" @click="handleSwaggerGenerate" :loading="generating">AI生成用例</a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <!-- 从需求文档生成 -->
        <a-tab-pane key="prd" tab="从需求文档生成">
          <a-form :model="prdForm" layout="vertical" style="max-width: 600px">
            <a-form-item label="需求文档内容" required>
              <a-textarea v-model:value="prdForm.content" placeholder="粘贴产品需求文档(PRD)内容" :rows="10" />
            </a-form-item>
            <a-form-item>
              <a-button type="primary" @click="handlePrdGenerate" :loading="generating">AI生成用例</a-button>
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <!-- 批量导入 -->
        <a-tab-pane key="import" tab="批量导入">
          <a-space direction="vertical" style="width: 100%">
            <a-alert message="支持JSON和CSV格式文件" type="info" show-icon />
            <a-upload-dragger
              name="file"
              :before-upload="handleImportFile"
              :show-upload-list="false"
              accept=".json,.csv"
            >
              <p class="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p class="ant-upload-hint">支持 .json 和 .csv 格式</p>
            </a-upload-dragger>

            <a-card title="JSON格式示例" size="small">
              <pre class="code-block">[
  {
    "name": "正确用户名密码登录",
    "case_type": "positive",
    "url": "http://example.com/login",
    "input_data": {"username": "admin", "password": "123456"},
    "expected_result": "登录成功，跳转到首页"
  }
]</pre>
            </a-card>
          </a-space>
        </a-tab-pane>
      </a-tabs>

      <!-- 生成结果预览 -->
      <a-modal
        v-model:open="resultVisible"
        title="生成的测试用例"
        width="800px"
        :footer="null"
      >
        <a-table
          :columns="resultColumns"
          :data-source="generatedCases"
          :pagination="false"
          size="small"
        />
        <div style="text-align: right; margin-top: 16px;">
          <a-button @click="resultVisible = false">关闭</a-button>
        </div>
      </a-modal>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { InboxOutlined } from '@ant-design/icons-vue'
import { testCases, generate } from '../api'

const router = useRouter()
const activeTab = ref('manual')
const creating = ref(false)
const generating = ref(false)
const resultVisible = ref(false)
const generatedCases = ref([])

const manualForm = reactive({
  name: '',
  case_type: 'positive',
  url: '',
  input_data_str: '',
  expected_result: '',
})

const urlForm = reactive({
  url: '',
  description: '',
})

const swaggerForm = reactive({
  content: '',
})

const prdForm = reactive({
  content: '',
})

const resultColumns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'case_type', key: 'case_type', width: 80,
    customRender: ({ text }) => text === 'positive' ? '正例' : '反例'
  },
  { title: '预期结果', dataIndex: 'expected_result', key: 'expected_result', ellipsis: true },
]

function goBack() {
  router.back()
}

// 手动创建
async function handleManualCreate() {
  if (!manualForm.name.trim()) {
    message.warning('请输入用例名称')
    return
  }
  creating.value = true
  try {
    let input_data = null
    if (manualForm.input_data_str.trim()) {
      try {
        input_data = JSON.parse(manualForm.input_data_str)
      } catch {
        message.error('输入数据JSON格式错误')
        return
      }
    }
    await testCases.create({
      name: manualForm.name,
      case_type: manualForm.case_type,
      url: manualForm.url,
      input_data,
      expected_result: manualForm.expected_result,
    })
    message.success('创建成功')
    router.push('/test-cases')
  } catch (e) {
    message.error('创建失败')
  } finally {
    creating.value = false
  }
}

// 从URL生成
async function handleUrlGenerate() {
  if (!urlForm.url.trim()) {
    message.warning('请输入URL')
    return
  }
  generating.value = true
  try {
    const { data } = await generate.fromUrl({
      url: urlForm.url,
      description: urlForm.description,
    })
    generatedCases.value = data.cases || []
    resultVisible.value = true
    message.success(data.message)
  } catch (e) {
    message.error('AI生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generating.value = false
  }
}

// Swagger文件上传
function handleSwaggerFile(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    swaggerForm.content = e.target.result
  }
  reader.readAsText(file)
  return false
}

// 从Swagger生成
async function handleSwaggerGenerate() {
  if (!swaggerForm.content.trim()) {
    message.warning('请输入Swagger内容')
    return
  }
  generating.value = true
  try {
    const { data } = await generate.fromSwagger({
      content: swaggerForm.content,
    })
    generatedCases.value = data.cases || []
    resultVisible.value = true
    message.success(data.message)
  } catch (e) {
    message.error('AI生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generating.value = false
  }
}

// 从PRD生成
async function handlePrdGenerate() {
  if (!prdForm.content.trim()) {
    message.warning('请输入需求文档内容')
    return
  }
  generating.value = true
  try {
    const { data } = await generate.fromPrd({
      content: prdForm.content,
    })
    generatedCases.value = data.cases || []
    resultVisible.value = true
    message.success(data.message)
  } catch (e) {
    message.error('AI生成失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generating.value = false
  }
}

// 批量导入
async function handleImportFile(file) {
  try {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await generate.import(formData)
    message.success(data.message)
    router.push('/test-cases')
  } catch (e) {
    message.error('导入失败: ' + (e.response?.data?.detail || e.message))
  }
  return false
}
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
  margin: 0;
}
</style>
