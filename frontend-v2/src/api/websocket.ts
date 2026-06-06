import { useEffect, useRef, useCallback } from 'react'

type MessageHandler = (data: unknown) => void

interface WSConnection {
  ws: WebSocket
  handlers: Map<string, Set<MessageHandler>>
}

const connections = new Map<string, WSConnection>()

function getConnection(url: string): WSConnection {
  let conn = connections.get(url)
  if (!conn || conn.ws.readyState === WebSocket.CLOSED) {
    const ws = new WebSocket(url)
    conn = { ws, handlers: new Map() }
    connections.set(url, conn)

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data)
        const type = parsed.type || 'message'
        const handlerSet = conn!.handlers.get(type)
        if (handlerSet) {
          handlerSet.forEach((h) => h(parsed))
        }
        // also send to 'message' catch-all
        if (type !== 'message') {
          const all = conn!.handlers.get('*')
          if (all) all.forEach((h) => h(parsed))
        }
      } catch {
        const all = conn!.handlers.get('*')
        if (all) all.forEach((h) => h(event.data))
      }
    }
  }
  return conn
}

/**
 * 管理 WebSocket 连接，支持多 type 监听
 * @param url WebSocket 地址，为空则不连接
 * @param handlers type → handler 的映射；'*' 为通配
 */
export function useWebSocket(
  url: string | null,
  handlers: Record<string, MessageHandler> = {},
) {
  const handlersRef = useRef(handlers)
  handlersRef.current = handlers

  const send = useCallback(
    (data: unknown) => {
      if (!url) return
      const conn = getConnection(url)
      if (conn.ws.readyState === WebSocket.OPEN) {
        conn.ws.send(typeof data === 'string' ? data : JSON.stringify(data))
      } else {
        conn.ws.addEventListener('open', () => {
          conn.ws.send(typeof data === 'string' ? data : JSON.stringify(data))
        }, { once: true })
      }
    },
    [url],
  )

  useEffect(() => {
    if (!url) return

    const conn = getConnection(url)

    // 注册 handlers
    for (const [type, handler] of Object.entries(handlersRef.current)) {
      if (!conn.handlers.has(type)) {
        conn.handlers.set(type, new Set())
      }
      conn.handlers.get(type)!.add(handler)
    }

    return () => {
      // 清理
      for (const [type, handler] of Object.entries(handlersRef.current)) {
        conn.handlers.get(type)?.delete(handler)
      }
    }
  }, [url])

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (!url) return
      const conn = connections.get(url)
      if (!conn) return
      for (const handler of Object.values(handlersRef.current)) {
        for (const set of conn.handlers.values()) {
          set.delete(handler)
        }
      }
    }
  }, [url])

  return { send }
}
