// 苹果风格主题配置
export const appleTheme = {
  name: 'Apple Style',
  description: '苹果风格，简洁现代',
  colors: {
    primary: '#007AFF',
    secondary: '#5856D6',
    success: '#34C759',
    warning: '#FF9500',
    danger: '#FF3B30',
    background: '#F5F5F7',
    text: '#1D1D1F',
    textSecondary: '#86868B',
    sidebar: '#FFFFFF',
    sidebarText: '#1D1D1F',
    sidebarActive: '#007AFF',
    card: '#FFFFFF',
    border: '#E5E5EA',
  },
  cssVariables: {
    '--border-radius': '12px',
    '--border-radius-lg': '16px',
    '--shadow-sm': '0 1px 3px rgba(0,0,0,0.08)',
    '--shadow-md': '0 4px 12px rgba(0,0,0,0.08)',
    '--shadow-lg': '0 8px 24px rgba(0,0,0,0.12)',
    '--font-family': '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif',
    '--transition': 'all 0.2s ease',
    '--spacing-xs': '4px',
    '--spacing-sm': '8px',
    '--spacing-md': '16px',
    '--spacing-lg': '24px',
    '--spacing-xl': '32px',
  },
}

// 获取主题CSS变量
export function getThemeCSSVariables(theme) {
  return {
    ...theme.colors,
    ...theme.cssVariables,
  }
}
