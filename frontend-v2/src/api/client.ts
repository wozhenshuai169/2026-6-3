import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截 — 部分接口仍需要 token（register/createRoom 等）
client.interceptors.request.use((config) => {
  const stored = localStorage.getItem('user')
  if (stored && config.method === 'post') {
    try {
      const user = JSON.parse(stored)
      // 若请求 data 里还没有 token 且接口需要，自动补上
      if (user.token && config.data && typeof config.data === 'object') {
        if ('token' in config.data && !config.data.token) {
          config.data.token = user.token
        }
      }
    } catch { /* ignore */ }
  }
  return config
})

// 响应拦截 — 统一错误处理
client.interceptors.response.use(
  (res) => res.data,
  (error) => {
    const detail = error.response?.data?.detail || error.message || '网络请求失败'
    console.error('[API Error]', detail)
    return Promise.reject(new Error(detail))
  },
)

export default client
