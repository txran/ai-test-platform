<template>
  <div class="theme-demo">
    <a-page-header title="主题样式对比" @back="goBack">
      <template #extra>
        <a-space>
          <a-button @click="goBack">返回</a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-row :gutter="16" style="margin-bottom: 16px;">
      <a-col :span="24">
        <a-card title="选择主题">
          <a-select
            v-model:value="selectedTheme"
            style="width: 100%"
            placeholder="选择一个主题"
            @change="onThemeChange"
          >
            <a-select-option v-for="theme in themeList" :key="theme.id" :value="theme.id">
              {{ theme.name }} - {{ theme.category }}
            </a-select-option>
          </a-select>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16">
      <a-col :span="16">
        <a-card title="预览效果">
          <div class="preview-container" :style="previewStyle">
            <!-- 侧边栏预览 -->
            <div class="preview-sidebar" :style="sidebarStyle">
              <div class="sidebar-logo">AI测试平台</div>
              <a-menu mode="inline" theme="dark" :style="sidebarMenuStyle">
                <a-menu-item key="1">
                  <FolderOutlined />
                  <span>文档管理</span>
                </a-menu-item>
                <a-menu-item key="2">
                  <FunctionOutlined />
                  <span>功能管理</span>
                </a-menu-item>
                <a-menu-item key="3" class="ant-menu-item-selected">
                  <AppstoreOutlined />
                  <span>场景管理</span>
                </a-menu-item>
                <a-menu-item key="4">
                  <SettingOutlined />
                  <span>系统设置</span>
                </a-menu-item>
              </a-menu>
            </div>

            <!-- 内容区预览 -->
            <div class="preview-content" :style="contentStyle">
              <div class="content-header" :style="headerStyle">
                <h2>场景管理</h2>
                <a-button type="primary">新建场景</a-button>
              </div>
              <a-table
                :columns="columns"
                :data-source="dataSource"
                :pagination="false"
                size="small"
                :style="tableStyle"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'status'">
                    <a-tag :color="record.status === '已上线' ? 'green' : 'default'">
                      {{ record.status }}
                    </a-tag>
                  </template>
                  <template v-if="column.key === 'action'">
                    <a-space>
                      <a-button type="link" size="small">详情</a-button>
                      <a-button type="link" size="small" danger>删除</a-button>
                    </a-space>
                  </template>
                </template>
              </a-table>
            </div>
          </div>
        </a-card>
      </a-col>

      <a-col :span="8">
        <a-card title="主题信息">
          <a-descriptions :column="1" bordered size="small">
            <a-descriptions-item label="主题名称">{{ currentTheme.name }}</a-descriptions-item>
            <a-descriptions-item label="分类">{{ currentTheme.category }}</a-descriptions-item>
            <a-descriptions-item label="适合场景">{{ currentTheme.bestFor }}</a-descriptions-item>
            <a-descriptions-item label="描述">{{ currentTheme.description }}</a-descriptions-item>
          </a-descriptions>
        </a-card>

        <a-card title="颜色配置" style="margin-top: 16px;">
          <div class="color-grid">
            <div v-for="(value, key) in currentTheme.colors" :key="key" class="color-item">
              <div class="color-preview" :style="{ background: value }"></div>
              <div class="color-info">
                <div class="color-name">{{ key }}</div>
                <div class="color-value">{{ value }}</div>
              </div>
            </div>
          </div>
        </a-card>

        <a-card title="CSS变量" style="margin-top: 16px;">
          <pre class="css-variables">{{ cssVariablesText }}</pre>
        </a-card>

        <a-card style="margin-top: 16px;">
          <a-button type="primary" block @click="applyTheme">
            应用此主题
          </a-button>
          <a-button block style="margin-top: 8px;" @click="resetTheme">
            重置为默认
          </a-button>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  FolderOutlined,
  FunctionOutlined,
  AppstoreOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'
import { themes, themeList, getThemeCSSVariables } from '../themeConfig'

const router = useRouter()
const selectedTheme = ref('minimalism')

const currentTheme = computed(() => {
  return themes[selectedTheme.value] || themes.minimalism
})

const cssVariablesText = computed(() => {
  const vars = currentTheme.value.cssVariables || {}
  return Object.entries(vars)
    .map(([key, value]) => `${key}: ${value};`)
    .join('\n')
})

const previewStyle = computed(() => ({
  display: 'flex',
  minHeight: '400px',
  border: '1px solid #d9d9d9',
  borderRadius: '8px',
  overflow: 'hidden',
}))

const sidebarStyle = computed(() => ({
  width: '200px',
  background: currentTheme.value.colors.sidebar,
  color: currentTheme.value.colors.sidebarText,
}))

const sidebarMenuStyle = computed(() => ({
  background: currentTheme.value.colors.sidebar,
}))

const contentStyle = computed(() => ({
  flex: 1,
  background: currentTheme.value.colors.background,
  padding: '16px',
}))

const headerStyle = computed(() => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: '16px',
  color: currentTheme.value.colors.text,
}))

const tableStyle = computed(() => ({
  color: currentTheme.value.colors.text,
}))

const columns = [
  { title: '名称', dataIndex: 'name', key: 'name' },
  { title: '描述', dataIndex: 'desc', key: 'desc' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '操作', key: 'action' },
]

const dataSource = [
  { key: '1', name: '用户注册测试', desc: '测试用户注册功能', status: '草稿' },
  { key: '2', name: '商品管理测试', desc: '测试商品管理功能', status: '已上线' },
  { key: '3', name: '订单流程测试', desc: '测试订单流程', status: '草稿' },
]

function onThemeChange(value) {
  selectedTheme.value = value
}

function applyTheme() {
  // 这里可以实现主题应用逻辑
  message.success(`已应用主题: ${currentTheme.value.name}`)
  // TODO: 将主题配置保存到本地存储或应用到全局
  localStorage.setItem('selectedTheme', selectedTheme.value)
}

function resetTheme() {
  selectedTheme.value = 'minimalism'
  localStorage.removeItem('selectedTheme')
  message.info('已重置为默认主题')
}

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.theme-demo {
  padding: 0;
}

.preview-container {
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  overflow: hidden;
}

.preview-sidebar {
  border-right: 1px solid #d9d9d9;
}

.sidebar-logo {
  padding: 16px;
  text-align: center;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.color-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-preview {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
}

.color-info {
  flex: 1;
  min-width: 0;
}

.color-name {
  font-size: 12px;
  color: #666;
}

.color-value {
  font-size: 12px;
  font-family: monospace;
  word-break: break-all;
}

.css-variables {
  font-size: 12px;
  font-family: monospace;
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  margin: 0;
  white-space: pre-wrap;
}
</style>
