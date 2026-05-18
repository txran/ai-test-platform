<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider 
      v-model:collapsed="collapsed" 
      collapsible 
      theme="light"
      :style="{
        background: '#FFFFFF',
        borderRight: '1px solid #E5E5EA',
        boxShadow: '1px 0 8px rgba(0,0,0,0.04)',
      }"
    >
      <div class="logo">AI测试平台</div>
      <a-menu v-model:selectedKeys="selectedKeys" theme="light" mode="inline" @click="handleMenu">
        <a-menu-item key="/documents">
          <template #icon><FolderOutlined /></template>
          文档管理
        </a-menu-item>
        <a-menu-item key="/functions">
          <template #icon><FunctionOutlined /></template>
          功能管理
        </a-menu-item>
        <a-menu-item key="/">
          <template #icon><AppstoreOutlined /></template>
          场景管理
        </a-menu-item>
        <a-menu-item key="/settings">
          <template #icon><SettingOutlined /></template>
          系统设置
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header :style="{
        background: '#FFFFFF',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        borderBottom: '1px solid #E5E5EA',
        boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
      }">
        <h2 style="margin: 0; color: #1D1D1F; font-weight: 600;">{{ pageTitle }}</h2>
      </a-layout-header>
      <a-layout-content :style="{
        margin: '16px',
        padding: '24px',
        background: '#FFFFFF',
        minHeight: '280px',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      }">
        <router-view :key="$route.fullPath" />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  AppstoreOutlined,
  FunctionOutlined,
  FolderOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const selectedKeys = ref(['/'])

const pageTitle = computed(() => {
  if (route.path === '/') return '场景管理'
  if (route.path.startsWith('/suites/')) return '场景详情'
  if (route.path === '/functions') return '功能管理'
  if (route.path.startsWith('/functions/')) return '功能详情'
  if (route.path.startsWith('/executions/')) return '执行详情'
  if (route.path === '/documents') return '文档管理'
  if (route.path === '/settings') return '系统设置'
  return 'AI测试平台'
})

watch(() => route.path, (newPath) => {
  if (newPath === '/' || newPath.startsWith('/suites/') || newPath.startsWith('/executions/')) {
    selectedKeys.value = ['/']
  } else if (newPath.startsWith('/functions')) {
    selectedKeys.value = ['/functions']
  } else {
    selectedKeys.value = [newPath]
  }
}, { immediate: true })

function handleMenu({ key }) {
  router.push(key)
}
</script>

<style>
/* 苹果风格全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
  background: #F5F5F7;
  color: #1D1D1F;
  -webkit-font-smoothing: antialiased;
}

.logo {
  color: #1D1D1F;
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  padding: 20px 0;
  border-bottom: 1px solid #E5E5EA;
}

/* 菜单样式 */
.ant-menu-light {
  border-right: none !important;
}

.ant-menu-item {
  border-radius: 8px !important;
  margin: 4px 8px !important;
  transition: all 0.2s ease !important;
}

.ant-menu-item:hover {
  background: #F5F5F7 !important;
}

.ant-menu-item-selected {
  background: #007AFF15 !important;
  color: #007AFF !important;
}

/* 卡片样式 */
.ant-card {
  border-radius: 12px !important;
  border: 1px solid #E5E5EA !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
  transition: all 0.2s ease !important;
}

.ant-card:hover {
  box-shadow: 0 4px 16px rgba(0,0,0,0.08) !important;
}

.ant-card-head {
  border-bottom: 1px solid #F0F0F0 !important;
}

/* 按钮样式 */
.ant-btn-primary {
  background: #007AFF !important;
  border-color: #007AFF !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
  box-shadow: 0 2px 4px rgba(0,122,255,0.2) !important;
  transition: all 0.2s ease !important;
}

.ant-btn-primary:hover {
  background: #0056CC !important;
  border-color: #0056CC !important;
  box-shadow: 0 4px 8px rgba(0,122,255,0.3) !important;
  transform: translateY(-1px);
}

.ant-btn-default {
  border-radius: 8px !important;
  border-color: #E5E5EA !important;
  transition: all 0.2s ease !important;
}

.ant-btn-default:hover {
  border-color: #007AFF !important;
  color: #007AFF !important;
}

/* 表格样式 */
.ant-table {
  border-radius: 12px !important;
  overflow: hidden;
}

.ant-table-thead > tr > th {
  background: #FAFAFA !important;
  border-bottom: 1px solid #E5E5EA !important;
  font-weight: 600 !important;
  color: #1D1D1F !important;
}

.ant-table-tbody > tr > td {
  border-bottom: 1px solid #F0F0F0 !important;
  transition: all 0.2s ease !important;
}

.ant-table-tbody > tr:hover > td {
  background: #F5F5F7 !important;
}

/* 输入框样式 */
.ant-input,
.ant-select-selector {
  border-radius: 8px !important;
  border-color: #E5E5EA !important;
  transition: all 0.2s ease !important;
}

.ant-input:focus,
.ant-select-focused .ant-select-selector {
  border-color: #007AFF !important;
  box-shadow: 0 0 0 2px rgba(0,122,255,0.1) !important;
}

/* 标签样式 */
.ant-tag {
  border-radius: 6px !important;
  font-weight: 500 !important;
}

/* 页面头部 */
.ant-page-header {
  padding: 12px 0 !important;
}

.ant-page-header-heading-title {
  font-weight: 600 !important;
  color: #1D1D1F !important;
}

/* 描述列表 */
.ant-descriptions-bordered .ant-descriptions-item-label {
  background: #FAFAFA !important;
  font-weight: 500 !important;
}

/* 分页器 */
.ant-pagination-item {
  border-radius: 8px !important;
}

.ant-pagination-item-active {
  border-color: #007AFF !important;
}

.ant-pagination-item-active a {
  color: #007AFF !important;
}

/* 模态框 */
.ant-modal-content {
  border-radius: 12px !important;
  overflow: hidden;
}

.ant-modal-header {
  border-bottom: 1px solid #F0F0F0 !important;
}

/* 消息提示 */
.ant-message-notice-content {
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #C7C7CC;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #A1A1A6;
}

/* 链接样式 */
a {
  color: #007AFF;
  transition: all 0.2s ease;
}

a:hover {
  color: #0056CC;
}

/* 空状态 */
.ant-empty-description {
  color: #86868B !important;
}

/* 加载状态 */
.ant-spin-dot-item {
  background: #007AFF !important;
}
</style>
