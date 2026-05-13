import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

export async function parseVideo(url) {
  const { data } = await api.post('/parse', { url })
  return data
}

export async function triggerDownload(url, formatId) {
  const { data } = await api.post('/download', { url, format_id: formatId }, {
    timeout: 600000,
  })
  return data
}

export async function summarizeVideo(url) {
  const { data } = await api.post('/summarize', { url }, {
    timeout: 120000,
  })
  return data
}

function parseSSE(text) {
  const events = []
  const blocks = text.split('\n\n')
  for (const block of blocks) {
    if (!block.trim()) continue
    let event = 'message'
    let data = ''
    for (const line of block.split('\n')) {
      if (line.startsWith('event: ')) event = line.slice(7)
      else if (line.startsWith('data: ')) data = line.slice(6)
    }
    if (data) events.push({ event, data })
  }
  return events
}

export function streamSummarize(url, callbacks) {
  const { onMeta, onChunk, onMindmap, onDone } = callbacks
  const controller = new AbortController()

  function dispatch(ev) {
    try {
      const json = JSON.parse(ev.data)
      if (ev.event === 'meta' && onMeta) onMeta(json)
      else if (ev.event === 'chunk' && onChunk) onChunk(json.text)
      else if (ev.event === 'mindmap' && onMindmap) onMindmap(json.markdown)
      else if (ev.event === 'done' && onDone) onDone()
      else if (ev.event === 'error') throw new Error(json.detail || 'AI 总结失败')
    } catch (e) {
      if (ev.event === 'error') throw e
    }
  }

  fetch('/api/summarize/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''
        for (const part of parts) {
          if (!part.trim()) continue
          for (const ev of parseSSE(part + '\n\n')) dispatch(ev)
        }
      }
      if (buffer.trim()) {
        for (const ev of parseSSE(buffer + '\n\n')) dispatch(ev)
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError' && onDone) onDone(err)
    })
  return controller
}

export function streamChat(url, question, context, onChunk, onDone) {
  const controller = new AbortController()
  let finished = false
  const safeDone = (err) => {
    if (finished) return
    finished = true
    onDone(err)
  }

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, question, context }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''
        for (const part of parts) {
          if (!part.trim()) continue
          const parsed = parseSSE(part + '\n\n')
          for (const ev of parsed) {
            try {
              const json = JSON.parse(ev.data)
              if (ev.event === 'chunk' && json.text != null) onChunk(json.text)
              else if (ev.event === 'done') safeDone()
              else if (ev.event === 'error') throw new Error(json.detail || 'AI 回答失败')
            } catch (e) {
              if (ev.event === 'error') throw e
            }
          }
        }
      }
      if (buffer.trim()) {
        const parsed = parseSSE(buffer + '\n\n')
        for (const ev of parsed) {
          try {
            const json = JSON.parse(ev.data)
            if (ev.event === 'chunk' && json.text != null) onChunk(json.text)
            else if (ev.event === 'done') safeDone()
            else if (ev.event === 'error') throw new Error(json.detail || 'AI 回答失败')
          } catch (e) {
            if (ev.event === 'error') safeDone(e)
          }
        }
      }
      safeDone()
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        safeDone(err)
      }
    })
  return controller
}
